import React from 'react';
import { IndicatorSummary } from '../types';
import { Activity, Gauge, TrendingUp, AlertCircle, ShieldCheck } from 'lucide-react';

interface IndicatorControlsProps {
  indicators: IndicatorSummary | undefined;
  currentPrice: number;
}

export const IndicatorControls: React.FC<IndicatorControlsProps> = ({ indicators, currentPrice }) => {
  if (!indicators) return null;

  const rsi = indicators.rsi;
  const getRsiColor = (val?: number) => {
    if (!val) return 'text-slate-400';
    if (val >= 70) return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
    if (val <= 30) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
  };

  const getTrendColor = (trend?: string) => {
    if (trend?.includes('BULLISH')) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    if (trend?.includes('BEARISH')) return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
    return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
  };

  return (
    <div className="bg-[#121824] border border-slate-800 rounded-2xl p-4 shadow-xl flex flex-col space-y-3">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-blue-400" />
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">
            Deterministic Technical Indicators
          </h3>
        </div>
        <div className="flex items-center space-x-1.5 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
          <ShieldCheck className="w-3 h-3" />
          <span>Python Calculated</span>
        </div>
      </div>

      {/* Grid of indicators */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2.5">
        
        {/* Trend Summary */}
        <div className="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-slate-400">TREND REGIME</span>
          <span className={`text-xs font-bold px-2 py-0.5 rounded-md border mt-1 text-center font-mono ${getTrendColor(indicators.trend_summary)}`}>
            {indicators.trend_summary || 'NEUTRAL'}
          </span>
        </div>

        {/* RSI (14) */}
        <div className="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-slate-400">RSI (14)</span>
          <div className="flex items-baseline justify-between mt-1">
            <span className={`text-sm font-bold font-mono px-1.5 py-0.5 rounded border ${getRsiColor(rsi)}`}>
              {rsi !== undefined ? rsi : 'N/A'}
            </span>
            <span className="text-[10px] text-slate-500 font-mono">
              {rsi && rsi > 70 ? 'Overbought' : rsi && rsi < 30 ? 'Oversold' : 'Neutral'}
            </span>
          </div>
        </div>

        {/* EMA 20 & 50 */}
        <div className="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-slate-400">EMA 20 / 50</span>
          <div className="text-xs font-mono font-medium text-slate-200 mt-1">
            <div className="text-amber-400">₹{indicators.ema20?.toFixed(1) || 'N/A'}</div>
            <div className="text-cyan-400">₹{indicators.ema50?.toFixed(1) || 'N/A'}</div>
          </div>
        </div>

        {/* MACD */}
        <div className="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-slate-400">MACD / SIGNAL</span>
          <div className="text-xs font-mono font-medium mt-1">
            <span className={indicators.macd && indicators.macd > 0 ? 'text-emerald-400' : 'text-rose-400'}>
              {indicators.macd?.toFixed(1) || 'N/A'}
            </span>
            <span className="text-slate-500"> / </span>
            <span className="text-slate-400">{indicators.macd_signal?.toFixed(1) || 'N/A'}</span>
          </div>
        </div>

        {/* Bollinger Bands */}
        <div className="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-slate-400">BOLLINGER (20,2)</span>
          <div className="text-xs font-mono font-medium text-slate-300 mt-1">
            <span className="text-purple-400">₹{indicators.bb_upper?.toFixed(0) || 'N/A'}</span>
            <span className="text-slate-500"> - </span>
            <span className="text-purple-400">₹{indicators.bb_lower?.toFixed(0) || 'N/A'}</span>
          </div>
        </div>

        {/* Volatility / ATR */}
        <div className="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-slate-400">VOLATILITY (ATR)</span>
          <div className="flex items-center justify-between mt-1">
            <span className="text-xs font-bold font-mono text-slate-200">
              ₹{indicators.atr?.toFixed(1) || 'N/A'}
            </span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
              indicators.volatility_summary === 'HIGH' ? 'bg-rose-500/10 text-rose-300 border border-rose-500/20' : 'bg-slate-800 text-slate-400'
            }`}>
              {indicators.volatility_summary}
            </span>
          </div>
        </div>

      </div>
    </div>
  );
};
