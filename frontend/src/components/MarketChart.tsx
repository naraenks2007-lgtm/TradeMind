import React, { useState, useMemo } from 'react';
import { MarketSnapshot, CandleData } from '../types';
import { Layers, Activity, Eye, Info } from 'lucide-react';

interface MarketChartProps {
  snapshot: MarketSnapshot | null;
  loading: boolean;
}

export const MarketChart: React.FC<MarketChartProps> = ({ snapshot, loading }) => {
  const [showEma20, setShowEma20] = useState(true);
  const [showEma50, setShowEma50] = useState(true);
  const [showBollinger, setShowBollinger] = useState(true);
  const [activeSubPanel, setActiveSubPanel] = useState<'rsi' | 'macd' | 'none'>('rsi');
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const candles = snapshot?.candles || [];
  const series = snapshot?.raw_indicator_series;

  // Compute coordinate ranges
  const { minPrice, maxPrice, maxVolume, pricesSpan } = useMemo(() => {
    if (!candles.length) return { minPrice: 0, maxPrice: 100, maxVolume: 1000, pricesSpan: 100 };
    let min = Infinity;
    let max = -Infinity;
    let maxVol = 0;

    candles.forEach((c, i) => {
      if (c.low < min) min = c.low;
      if (c.high > max) max = c.high;
      if (c.volume > maxVol) maxVol = c.volume;

      // Include bollinger bands in range if shown
      if (showBollinger && series?.bb_upper?.[i]) {
        const u = series.bb_upper[i];
        const l = series.bb_lower?.[i];
        if (u && u > max) max = u;
        if (l && l < min) min = l;
      }
    });

    // Add 2% padding
    const padding = (max - min) * 0.04 || 1;
    return {
      minPrice: min - padding,
      maxPrice: max + padding,
      maxVolume: maxVol || 1,
      pricesSpan: (max + padding) - (min - padding) || 1
    };
  }, [candles, showBollinger, series]);

  if (loading) {
    return (
      <div className="w-full h-[520px] bg-[#121824] rounded-2xl border border-slate-800 flex flex-col items-center justify-center space-y-3">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs text-slate-400 font-mono">Loading market candles & calculating indicators...</p>
      </div>
    );
  }

  if (!snapshot || !candles.length) {
    return (
      <div className="w-full h-[520px] bg-[#121824] rounded-2xl border border-slate-800 flex items-center justify-center">
        <p className="text-sm text-slate-500 font-mono">No OHLCV market data available.</p>
      </div>
    );
  }

  // Dimensions
  const svgWidth = 840;
  const mainHeight = 340;
  const subHeight = activeSubPanel !== 'none' ? 110 : 0;
  const totalSvgHeight = mainHeight + subHeight + 30;

  const candleWidth = Math.max(2, (svgWidth - 60) / candles.length);
  const candleGap = candleWidth * 0.25;
  const barWidth = Math.max(1.5, candleWidth - candleGap);

  const getY = (price: number) => {
    return mainHeight - ((price - minPrice) / pricesSpan) * (mainHeight - 30) - 15;
  };

  const hoveredCandle: CandleData | null = hoverIndex !== null ? candles[hoverIndex] : candles[candles.length - 1];
  const hoveredEma20 = hoverIndex !== null && series?.ema20 ? series.ema20[hoverIndex] : snapshot.indicators.ema20;
  const hoveredEma50 = hoverIndex !== null && series?.ema50 ? series.ema50[hoverIndex] : snapshot.indicators.ema50;
  const hoveredRsi = hoverIndex !== null && series?.rsi ? series.rsi[hoverIndex] : snapshot.indicators.rsi;

  return (
    <div className="w-full bg-[#121824] rounded-2xl border border-slate-800 p-4 flex flex-col shadow-xl">
      
      {/* Header controls & Data Source Tag */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3 mb-2">
        <div className="flex items-center space-x-3">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-bold text-white tracking-wide">{snapshot.symbol}</span>
              <span className={`text-xs px-2 py-0.5 rounded-md font-mono font-semibold ${
                snapshot.change_pct >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
              }`}>
                {snapshot.change_pct >= 0 ? '+' : ''}{snapshot.change_pct}%
              </span>
            </div>
            <div className="flex items-center space-x-2 text-xs text-slate-400 mt-0.5">
              <span>₹{snapshot.current_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
              <span>•</span>
              <span className="font-mono text-slate-400">Timeframe: {snapshot.timeframe}</span>
            </div>
          </div>
        </div>

        {/* Source Badge with Disclaimer */}
        <div className="flex items-center space-x-2">
          <div className={`px-2.5 py-1 rounded-lg border text-[11px] font-mono flex items-center gap-1.5 ${
            snapshot.is_synthetic 
              ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
              : 'bg-blue-500/10 text-blue-300 border-blue-500/30'
          }`}>
            <Info className="w-3.5 h-3.5" />
            <span>Source: {snapshot.data_source}</span>
          </div>

          <div className="text-[11px] font-mono text-slate-400 bg-slate-900/60 px-2.5 py-1 rounded-lg border border-slate-800">
            Latest: {snapshot.last_timestamp}
          </div>
        </div>

        {/* Indicator Toggles */}
        <div className="flex items-center space-x-1.5 bg-slate-900/80 p-1 rounded-xl border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setShowEma20(!showEma20)}
            className={`px-2 py-0.5 rounded transition ${showEma20 ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'text-slate-500'}`}
          >
            EMA 20
          </button>
          <button
            onClick={() => setShowEma50(!showEma50)}
            className={`px-2 py-0.5 rounded transition ${showEma50 ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-500'}`}
          >
            EMA 50
          </button>
          <button
            onClick={() => setShowBollinger(!showBollinger)}
            className={`px-2 py-0.5 rounded transition ${showBollinger ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'text-slate-500'}`}
          >
            Bollinger
          </button>
          <span className="text-slate-700">|</span>
          <button
            onClick={() => setActiveSubPanel(activeSubPanel === 'rsi' ? 'none' : 'rsi')}
            className={`px-2 py-0.5 rounded transition ${activeSubPanel === 'rsi' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' : 'text-slate-500'}`}
          >
            RSI (14)
          </button>
          <button
            onClick={() => setActiveSubPanel(activeSubPanel === 'macd' ? 'none' : 'macd')}
            className={`px-2 py-0.5 rounded transition ${activeSubPanel === 'macd' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' : 'text-slate-500'}`}
          >
            MACD
          </button>
        </div>
      </div>

      {/* Hover Info Bar */}
      {hoveredCandle && (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs font-mono bg-slate-900/60 border border-slate-800/80 px-3 py-1.5 rounded-lg text-slate-300 mb-2">
          <span><span className="text-slate-500">DATE:</span> {hoveredCandle.date}</span>
          <span><span className="text-slate-500">O:</span> ₹{hoveredCandle.open.toFixed(2)}</span>
          <span><span className="text-slate-500">H:</span> ₹{hoveredCandle.high.toFixed(2)}</span>
          <span><span className="text-slate-500">L:</span> ₹{hoveredCandle.low.toFixed(2)}</span>
          <span><span className="text-slate-500">C:</span> ₹{hoveredCandle.close.toFixed(2)}</span>
          <span><span className="text-slate-500">VOL:</span> {hoveredCandle.volume.toLocaleString()}</span>
          {showEma20 && hoveredEma20 && <span className="text-amber-400">EMA20: ₹{hoveredEma20.toFixed(2)}</span>}
          {showEma50 && hoveredEma50 && <span className="text-cyan-400">EMA50: ₹{hoveredEma50.toFixed(2)}</span>}
          {activeSubPanel === 'rsi' && hoveredRsi && <span className="text-blue-400">RSI: {hoveredRsi.toFixed(1)}</span>}
        </div>
      )}

      {/* SVG Candlestick & Indicator Area */}
      <div className="relative w-full overflow-x-auto">
        <svg 
          viewBox={`0 0 ${svgWidth} ${totalSvgHeight}`} 
          className="w-full h-auto select-none cursor-crosshair font-mono text-[10px]"
          onMouseLeave={() => setHoverIndex(null)}
        >
          {/* Horizontal Grid lines */}
          {[0.2, 0.4, 0.6, 0.8].map((pct, i) => {
            const y = 15 + pct * (mainHeight - 30);
            const priceVal = maxPrice - pct * pricesSpan;
            return (
              <g key={i}>
                <line x1={0} y1={y} x2={svgWidth - 55} y2={y} stroke="#1E293B" strokeDasharray="3 3" />
                <text x={svgWidth - 50} y={y + 3} fill="#64748B" fontSize="9">{priceVal.toFixed(1)}</text>
              </g>
            );
          })}

          {/* Volume sub-chart background in main pane */}
          {candles.map((c, i) => {
            const x = i * candleWidth + (candleGap / 2);
            const volHeight = (c.volume / maxVolume) * 45;
            const isBull = c.close >= c.open;
            return (
              <rect
                key={`vol-${i}`}
                x={x}
                y={mainHeight - volHeight - 5}
                width={barWidth}
                height={volHeight}
                fill={isBull ? '#10B981' : '#EF4444'}
                opacity={0.18}
              />
            );
          })}

          {/* Bollinger Bands Fill & Lines */}
          {showBollinger && series?.bb_upper && series?.bb_lower && (
            <g>
              {/* Upper Line */}
              <path
                d={series.bb_upper.map((val, i) => {
                  if (val === null) return '';
                  const x = i * candleWidth + (candleWidth / 2);
                  const y = getY(val);
                  return `${i === 0 || !series.bb_upper?.[i-1] ? 'M' : 'L'} ${x} ${y}`;
                }).join(' ')}
                fill="none"
                stroke="#A855F7"
                strokeWidth="1"
                opacity="0.6"
              />
              {/* Lower Line */}
              <path
                d={series.bb_lower.map((val, i) => {
                  if (val === null) return '';
                  const x = i * candleWidth + (candleWidth / 2);
                  const y = getY(val);
                  return `${i === 0 || !series.bb_lower?.[i-1] ? 'M' : 'L'} ${x} ${y}`;
                }).join(' ')}
                fill="none"
                stroke="#A855F7"
                strokeWidth="1"
                opacity="0.6"
              />
            </g>
          )}

          {/* EMA 20 line */}
          {showEma20 && series?.ema20 && (
            <path
              d={series.ema20.map((val, i) => {
                if (val === null) return '';
                const x = i * candleWidth + (candleWidth / 2);
                const y = getY(val);
                return `${i === 0 || !series.ema20?.[i-1] ? 'M' : 'L'} ${x} ${y}`;
              }).join(' ')}
              fill="none"
              stroke="#F59E0B"
              strokeWidth="1.5"
            />
          )}

          {/* EMA 50 line */}
          {showEma50 && series?.ema50 && (
            <path
              d={series.ema50.map((val, i) => {
                if (val === null) return '';
                const x = i * candleWidth + (candleWidth / 2);
                const y = getY(val);
                return `${i === 0 || !series.ema50?.[i-1] ? 'M' : 'L'} ${x} ${y}`;
              }).join(' ')}
              fill="none"
              stroke="#06B6D4"
              strokeWidth="1.5"
            />
          )}

          {/* Candlesticks */}
          {candles.map((c, i) => {
            const x = i * candleWidth + (candleGap / 2);
            const centerX = x + (barWidth / 2);
            const isBull = c.close >= c.open;
            const openY = getY(c.open);
            const closeY = getY(c.close);
            const highY = getY(c.high);
            const lowY = getY(c.low);
            const bodyY = Math.min(openY, closeY);
            const bodyH = Math.max(2, Math.abs(openY - closeY));
            const color = isBull ? '#10B981' : '#EF4444';

            return (
              <g 
                key={i}
                onMouseEnter={() => setHoverIndex(i)}
                className="cursor-pointer"
              >
                {/* Wick */}
                <line x1={centerX} y1={highY} x2={centerX} y2={lowY} stroke={color} strokeWidth="1.2" />
                {/* Body */}
                <rect
                  x={x}
                  y={bodyY}
                  width={barWidth}
                  height={bodyH}
                  fill={isBull ? '#10B981' : '#EF4444'}
                  rx="1"
                />
              </g>
            );
          })}

          {/* Subpanel Divider & Charts */}
          {activeSubPanel !== 'none' && (
            <g transform={`translate(0, ${mainHeight + 10})`}>
              {/* Divider */}
              <line x1={0} y1={0} x2={svgWidth} y2={0} stroke="#334155" strokeWidth="1" />
              
              {/* RSI Subpanel */}
              {activeSubPanel === 'rsi' && series?.rsi && (
                <g>
                  {/* Labels and lines for 70, 50, 30 */}
                  <line x1={0} y1={25} x2={svgWidth - 55} y2={25} stroke="#EF4444" strokeDasharray="2 2" opacity="0.4" />
                  <text x={svgWidth - 50} y={28} fill="#EF4444" fontSize="8">70 (OB)</text>
                  
                  <line x1={0} y1={55} x2={svgWidth - 55} y2={55} stroke="#64748B" strokeDasharray="2 2" opacity="0.3" />
                  <text x={svgWidth - 50} y={58} fill="#64748B" fontSize="8">50</text>
                  
                  <line x1={0} y1={85} x2={svgWidth - 55} y2={85} stroke="#10B981" strokeDasharray="2 2" opacity="0.4" />
                  <text x={svgWidth - 50} y={88} fill="#10B981" fontSize="8">30 (OS)</text>

                  {/* RSI Curve */}
                  <path
                    d={series.rsi.map((val, i) => {
                      if (val === null) return '';
                      const x = i * candleWidth + (candleWidth / 2);
                      const y = 100 - (val / 100) * 80;
                      return `${i === 0 || !series.rsi?.[i-1] ? 'M' : 'L'} ${x} ${y}`;
                    }).join(' ')}
                    fill="none"
                    stroke="#3B82F6"
                    strokeWidth="1.8"
                  />
                  <text x={10} y={15} fill="#94A3B8" fontSize="9" fontWeight="bold">RSI (14)</text>
                </g>
              )}

              {/* MACD Subpanel */}
              {activeSubPanel === 'macd' && series?.macd && series?.macd_signal && series?.macd_hist && (
                <g>
                  <line x1={0} y1={55} x2={svgWidth - 55} y2={55} stroke="#475569" strokeDasharray="2 2" />
                  <text x={10} y={15} fill="#94A3B8" fontSize="9" fontWeight="bold">MACD (12, 26, 9)</text>

                  {/* Histogram bars */}
                  {series.macd_hist.map((hist, i) => {
                    if (hist === null) return null;
                    const x = i * candleWidth + (candleGap / 2);
                    const h = Math.min(40, Math.abs(hist) * 2);
                    const y = hist >= 0 ? 55 - h : 55;
                    const fill = hist >= 0 ? '#10B981' : '#EF4444';
                    return (
                      <rect key={i} x={x} y={y} width={barWidth} height={h} fill={fill} opacity={0.6} />
                    );
                  })}
                </g>
              )}
            </g>
          )}

          {/* Crosshair on Hover */}
          {hoverIndex !== null && (
            <g>
              <line
                x1={hoverIndex * candleWidth + (candleWidth / 2)}
                y1={0}
                x2={hoverIndex * candleWidth + (candleWidth / 2)}
                y2={totalSvgHeight}
                stroke="#94A3B8"
                strokeWidth="0.8"
                strokeDasharray="2 2"
              />
            </g>
          )}
        </svg>
      </div>

    </div>
  );
};
