import React, { useState } from 'react';
import { CompellingLoopResponse } from '../types';
import { api } from '../services/api';
import { 
  Play, 
  CheckCircle2, 
  ArrowRight, 
  Brain, 
  Cpu, 
  Activity, 
  Layers, 
  DollarSign, 
  MessageSquare, 
  ShieldCheck, 
  TrendingUp, 
  TrendingDown,
  RefreshCw,
  Sparkles,
  Zap,
  Clock,
  Gauge
} from 'lucide-react';

interface CompellingLoopProps {
  currentSymbol: string;
}

export const CompellingLoop: React.FC<CompellingLoopProps> = ({ currentSymbol }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CompellingLoopResponse | null>(null);
  const [activeStep, setActiveStep] = useState<number>(6);

  const handleRunLoop = async () => {
    setLoading(true);
    try {
      const data = await api.runCompellingLoop(currentSymbol);
      setResult(data);
      setActiveStep(6);
    } catch (err: any) {
      alert(`Loop failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { num: 1, title: "Market Data Comes In", icon: <Activity className="w-4 h-4 text-blue-400" />, desc: "OHLCV data ingestion & deterministic indicators" },
    { num: 2, title: "ML Analyzes It", icon: <Gauge className="w-4 h-4 text-emerald-400" />, desc: "Tabular models: Direction, Volatility, Sentiment" },
    { num: 3, title: "Hindsight Recalls", icon: <Brain className="w-4 h-4 text-purple-400" />, desc: "Memory bank recall of similar past regimes" },
    { num: 4, title: "Groq Explains", icon: <Cpu className="w-4 h-4 text-indigo-400" />, desc: "Reasoning & hypothesis formulation" },
    { num: 5, title: "Paper Trading Measures", icon: <DollarSign className="w-4 h-4 text-amber-400" />, desc: "Virtual execution & P&L measurement" },
    { num: 6, title: "Hindsight Remembers & Replies", icon: <MessageSquare className="w-4 h-4 text-pink-400" />, desc: "Outcome retention & conversational lesson reply" }
  ];

  return (
    <div className="flex flex-col space-y-5 max-w-7xl mx-auto">
      
      {/* Hero Banner */}
      <div className="bg-gradient-to-r from-[#121824] via-[#161F33] to-[#121824] border border-blue-500/20 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="p-2 bg-blue-500/10 border border-blue-500/30 rounded-xl text-blue-400">
                <Zap className="w-5 h-5" />
              </span>
              <h2 className="text-lg font-bold text-white tracking-wide flex items-center gap-2">
                The Complete TradeMind AI Loop
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-300 font-mono border border-blue-500/30">
                  End-to-End Autonomous Loop
                </span>
              </h2>
            </div>
            <p className="text-xs text-slate-300 max-w-3xl leading-relaxed">
              Demonstrates one compelling closed loop without hallucinated indicator values or forced frameworks:
              <br />
              <span className="font-mono text-blue-300 font-semibold">
                Market Data comes in → ML analyzes it → Hindsight recalls what happened before → Groq explains the decision → Paper Trading measures the result → Hindsight remembers the lesson and replies.
              </span>
            </p>
          </div>

          <button
            onClick={handleRunLoop}
            disabled={loading}
            className="px-6 py-3.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-bold text-xs shadow-lg shadow-blue-500/30 transition flex items-center justify-center gap-2 shrink-0 font-mono disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Executing 6-Stage Loop...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Run Complete Loop on {currentSymbol}</span>
              </>
            )}
          </button>
        </div>

        {/* Stepper Pipeline Bar */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-2 mt-6 pt-5 border-t border-slate-800/80">
          {steps.map((s) => (
            <button
              key={s.num}
              onClick={() => setActiveStep(s.num)}
              className={`p-3 rounded-xl border transition text-left flex flex-col justify-between ${
                activeStep === s.num
                  ? 'bg-blue-600/20 border-blue-500/50 shadow-md'
                  : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-mono text-slate-500">STAGE {s.num}</span>
                {result ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : s.icon}
              </div>
              <div className="text-xs font-bold text-white tracking-tight">{s.title}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Results Display */}
      {loading ? (
        <div className="w-full h-80 bg-[#121824] rounded-2xl border border-slate-800 flex flex-col items-center justify-center space-y-3">
          <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-xs text-slate-300 font-mono animate-pulse">
            Ingesting Data → Fitting Tabular ML → Recalling Memory → Reasoning with Groq → Executing Virtual Paper Trade → Retaining Lesson...
          </p>
        </div>
      ) : result ? (
        <div className="space-y-4">
          
          {/* Loop Summary Banner */}
          <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
            <div className="flex items-center space-x-2 text-emerald-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{result.summary_verdict}</span>
            </div>
            <div className="text-slate-400 shrink-0">
              Execution Time: <span className="text-white font-bold">{result.execution_time_seconds}s</span> | ID: <span className="text-blue-400">{result.loop_id}</span>
            </div>
          </div>

          {/* Detailed Stage Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            
            {/* Step 1: Market Data */}
            <div className={`bg-[#121824] border rounded-2xl p-4 shadow-xl flex flex-col justify-between ${activeStep === 1 ? 'border-blue-500' : 'border-slate-800'}`}>
              <div>
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="text-blue-400 font-bold flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5" />
                    <span>STAGE 1: MARKET DATA</span>
                  </span>
                  <span className="text-slate-500">{result.step1_market_data.timestamp}</span>
                </div>
                <div className="text-base font-bold text-white font-mono">
                  {result.instrument} @ ₹{result.step1_market_data.current_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
                <div className="text-[11px] font-mono text-slate-400 mt-1">
                  Source: {result.step1_market_data.data_source}
                </div>
                <div className="grid grid-cols-2 gap-1.5 mt-3 text-[11px] font-mono bg-slate-900/80 p-2.5 rounded-xl border border-slate-800">
                  <div>RSI: <span className="text-blue-400 font-bold">{result.step1_market_data.indicators.rsi}</span></div>
                  <div>Trend: <span className="text-emerald-400 font-bold">{result.step1_market_data.indicators.trend_regime}</span></div>
                  <div>EMA20: <span className="text-amber-400 font-bold">₹{result.step1_market_data.indicators.ema20?.toFixed(1)}</span></div>
                  <div>ATR: <span className="text-slate-200 font-bold">₹{result.step1_market_data.indicators.atr?.toFixed(1)}</span></div>
                </div>
              </div>
            </div>

            {/* Step 2: Tabular ML Analysis */}
            <div className={`bg-[#121824] border rounded-2xl p-4 shadow-xl flex flex-col justify-between ${activeStep === 2 ? 'border-emerald-500' : 'border-slate-800'}`}>
              <div>
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="text-emerald-400 font-bold flex items-center gap-1.5">
                    <Gauge className="w-3.5 h-3.5" />
                    <span>STAGE 2: TABULAR ML MODELS</span>
                  </span>
                  <span className="text-[10px] bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/20">Scikit-Learn</span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-sm font-bold font-mono text-white">
                    {result.step2_ml_analysis.direction.direction} ({(result.step2_ml_analysis.direction.confidence * 100).toFixed(0)}%)
                  </span>
                  <span className="text-xs font-mono text-purple-300">
                    Vol: {result.step2_ml_analysis.volatility.predicted_volatility_pct}%
                  </span>
                </div>
                <div className="text-[11px] font-mono text-slate-400 mt-2 space-y-1 bg-slate-900/80 p-2.5 rounded-xl border border-slate-800">
                  <div className="flex justify-between">
                    <span>Sentiment:</span>
                    <span className="text-blue-400 font-bold">{result.step2_ml_analysis.sentiment.sentiment_label} ({result.step2_ml_analysis.sentiment.sentiment_score})</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Buying Pressure:</span>
                    <span className="text-emerald-400 font-bold">{result.step2_ml_analysis.sentiment.buying_pressure_pct}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Volatility Regime:</span>
                    <span className="text-amber-400 font-bold">{result.step2_ml_analysis.volatility.volatility_regime}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 3: Hindsight Recall */}
            <div className={`bg-[#121824] border rounded-2xl p-4 shadow-xl flex flex-col justify-between ${activeStep === 3 ? 'border-purple-500' : 'border-slate-800'}`}>
              <div>
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="text-purple-400 font-bold flex items-center gap-1.5">
                    <Brain className="w-3.5 h-3.5" />
                    <span>STAGE 3: HINDSIGHT RECALL</span>
                  </span>
                  <span className="text-[10px] text-purple-300 font-mono">
                    {result.step3_hindsight_recall.recalled_items_count} memory items
                  </span>
                </div>
                <div className="text-[11px] font-mono text-slate-300 bg-purple-950/20 border border-purple-500/20 p-2.5 rounded-xl leading-relaxed">
                  {result.step3_hindsight_recall.recalled_lessons[0] || "No prior precedents."}
                </div>
              </div>
            </div>

            {/* Step 4: Groq Reasoning */}
            <div className={`bg-[#121824] border rounded-2xl p-4 shadow-xl flex flex-col justify-between ${activeStep === 4 ? 'border-indigo-500' : 'border-slate-800'}`}>
              <div>
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="text-indigo-400 font-bold flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5" />
                    <span>STAGE 4: GROQ REASONING</span>
                  </span>
                  <span className="text-[10px] text-indigo-300 font-mono">openai/gpt-oss-120b</span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed bg-indigo-950/20 border border-indigo-500/20 p-2.5 rounded-xl">
                  {result.step4_groq_explanation.hypothesis}
                </p>
                <div className="grid grid-cols-3 gap-1 mt-2 text-center text-[10px] font-mono">
                  <div className="bg-slate-900 p-1 rounded">Entry: ₹{result.step4_groq_explanation.entry_assumption.toFixed(0)}</div>
                  <div className="bg-rose-950/40 p-1 rounded text-rose-300">SL: ₹{result.step4_groq_explanation.stop_loss_assumption.toFixed(0)}</div>
                  <div className="bg-emerald-950/40 p-1 rounded text-emerald-300">Tgt: ₹{result.step4_groq_explanation.target_assumption.toFixed(0)}</div>
                </div>
              </div>
            </div>

            {/* Step 5: Paper Trading Result */}
            <div className={`bg-[#121824] border rounded-2xl p-4 shadow-xl flex flex-col justify-between ${activeStep === 5 ? 'border-amber-500' : 'border-slate-800'}`}>
              <div>
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="text-amber-400 font-bold flex items-center gap-1.5">
                    <DollarSign className="w-3.5 h-3.5" />
                    <span>STAGE 5: PAPER TRADING MEASUREMENT</span>
                  </span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded font-mono ${
                    result.step5_paper_trading_result.verdict === 'WIN' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                  }`}>
                    {result.step5_paper_trading_result.verdict}
                  </span>
                </div>
                <div className="text-base font-bold font-mono text-white">
                  Net P&L: <span className={result.step5_paper_trading_result.net_realized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                    {result.step5_paper_trading_result.net_realized_pnl >= 0 ? '+' : ''}₹{result.step5_paper_trading_result.net_realized_pnl}
                  </span>
                </div>
                <div className="text-[11px] font-mono text-slate-400 mt-2 space-y-1 bg-slate-900/80 p-2.5 rounded-xl border border-slate-800">
                  <div className="flex justify-between">
                    <span>Executed:</span>
                    <span className="text-white">{result.step5_paper_trading_result.side} {result.step5_paper_trading_result.quantity} Qty</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Entry → Exit:</span>
                    <span>₹{result.step5_paper_trading_result.entry_price} → ₹{result.step5_paper_trading_result.exit_price}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total Equity:</span>
                    <span className="text-emerald-400">₹{result.step5_paper_trading_result.portfolio_equity.toLocaleString('en-IN')}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 6: Hindsight Remembers & Replies */}
            <div className={`bg-[#121824] border rounded-2xl p-4 shadow-xl flex flex-col justify-between ${activeStep === 6 ? 'border-pink-500' : 'border-slate-800'}`}>
              <div>
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="text-pink-400 font-bold flex items-center gap-1.5">
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>STAGE 6: HINDSIGHT REMEMBERS & REPLIES</span>
                  </span>
                  <span className="text-[10px] text-pink-300 font-mono">Retained ✓</span>
                </div>
                <div className="text-xs text-pink-100/90 bg-pink-950/20 border border-pink-500/20 p-2.5 rounded-xl font-mono leading-relaxed">
                  &ldquo;{result.step6_hindsight_lesson_reply.hindsight_reply}&rdquo;
                </div>
                <div className="text-[10px] font-mono text-slate-500 mt-2">
                  Memory Bank: {result.step6_hindsight_lesson_reply.memory_bank}
                </div>
              </div>
            </div>

          </div>

        </div>
      ) : (
        <div className="bg-[#121824] border border-slate-800 rounded-2xl p-12 text-center space-y-3">
          <Zap className="w-10 h-10 text-blue-500/40 mx-auto" />
          <h3 className="text-sm font-bold text-white tracking-wide">
            Ready to execute the complete closed loop
          </h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
            Click &ldquo;Run Complete Loop&rdquo; above to stream market data through Tabular ML, recall previous experiences from Hindsight, synthesize with Groq, execute virtual paper trade, and retain the resulting lesson.
          </p>
        </div>
      )}

    </div>
  );
};
