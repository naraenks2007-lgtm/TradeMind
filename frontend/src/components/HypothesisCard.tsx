import React from 'react';
import { 
  TradingHypothesis, 
  MarketDirection 
} from '../types';
import { 
  Sparkles, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  ShieldAlert, 
  CheckCircle2, 
  Brain, 
  ArrowRight,
  Target,
  DollarSign,
  AlertTriangle
} from 'lucide-react';

interface HypothesisCardProps {
  hypothesis: TradingHypothesis | null;
  loading: boolean;
  onGenerate: () => void;
  onExecutePaperTrade: (hypothesis: TradingHypothesis) => void;
  includeMemory: boolean;
  setIncludeMemory: (val: boolean) => void;
}

export const HypothesisCard: React.FC<HypothesisCardProps> = ({
  hypothesis,
  loading,
  onGenerate,
  onExecutePaperTrade,
  includeMemory,
  setIncludeMemory
}) => {
  const getDirectionBadge = (dir: string) => {
    switch (dir) {
      case 'BULLISH':
        return {
          icon: <TrendingUp className="w-4 h-4 text-emerald-400" />,
          classes: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
        };
      case 'BEARISH':
        return {
          icon: <TrendingDown className="w-4 h-4 text-rose-400" />,
          classes: 'bg-rose-500/10 text-rose-400 border-rose-500/30'
        };
      default:
        return {
          icon: <Minus className="w-4 h-4 text-amber-400" />,
          classes: 'bg-amber-500/10 text-amber-400 border-amber-500/30'
        };
    }
  };

  const badge = hypothesis ? getDirectionBadge(hypothesis.market_direction) : null;
  
  // Calculate Risk/Reward
  let riskReward = '1 : 2.0';
  if (hypothesis && hypothesis.entry_assumption && hypothesis.stop_loss_assumption && hypothesis.target_assumption) {
    const risk = Math.abs(hypothesis.entry_assumption - hypothesis.stop_loss_assumption);
    const reward = Math.abs(hypothesis.target_assumption - hypothesis.entry_assumption);
    if (risk > 0) {
      riskReward = `1 : ${(reward / risk).toFixed(2)}`;
    }
  }

  return (
    <div className="bg-[#121824] border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col space-y-4">
      
      {/* Header and Generate Button */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-blue-600/10 border border-blue-500/20 rounded-xl">
            <Sparkles className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide">
              AI Market Hypothesis Generator
            </h2>
            <p className="text-[11px] text-slate-400">
              Powered by Groq LLM (<span className="font-mono text-blue-400">openai/gpt-oss-120b</span>)
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Hindsight Memory Toggle */}
          <label className="flex items-center space-x-2 text-xs font-mono cursor-pointer bg-slate-900/80 px-2.5 py-1.5 rounded-lg border border-slate-800 hover:border-slate-700 transition">
            <input
              type="checkbox"
              checked={includeMemory}
              onChange={(e) => setIncludeMemory(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-purple-600 focus:ring-purple-500 focus:ring-offset-0"
            />
            <span className="flex items-center gap-1 text-purple-300">
              <Brain className="w-3.5 h-3.5" />
              <span>Hindsight Memory</span>
            </span>
          </label>

          {/* Generate Button */}
          <button
            onClick={onGenerate}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-md shadow-blue-600/30 transition disabled:opacity-50"
          >
            {loading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Synthesizing...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Formulate Hypothesis</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      {!hypothesis ? (
        <div className="py-12 flex flex-col items-center justify-center text-center space-y-2 text-slate-400">
          <Sparkles className="w-8 h-8 text-blue-500/40 mb-1" />
          <p className="text-sm font-medium text-slate-300">Ready to formulate a trading hypothesis.</p>
          <p className="text-xs text-slate-500 max-w-sm">
            Click &ldquo;Formulate Hypothesis&rdquo; to send the current Python-verified technical indicators and Hindsight memories to Groq.
          </p>
        </div>
      ) : (
        <div className="flex flex-col space-y-4">
          
          {/* Top Row: Direction, Confidence, Levels */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            
            {/* Market Direction & Confidence */}
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800 flex flex-col justify-between">
              <span className="text-[11px] font-mono text-slate-400">DIRECTION & CONFIDENCE</span>
              <div className="flex items-center justify-between mt-2">
                <div className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg border font-bold text-xs font-mono ${badge?.classes}`}>
                  {badge?.icon}
                  <span>{hypothesis.market_direction}</span>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold font-mono text-white">
                    {(hypothesis.confidence * 100).toFixed(0)}%
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">Calibrated</div>
                </div>
              </div>
              {/* Confidence bar */}
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-2">
                <div 
                  className={`h-full rounded-full ${
                    hypothesis.market_direction === 'BULLISH' ? 'bg-emerald-500' : hypothesis.market_direction === 'BEARISH' ? 'bg-rose-500' : 'bg-amber-500'
                  }`}
                  style={{ width: `${Math.min(100, Math.max(10, hypothesis.confidence * 100))}%` }}
                ></div>
              </div>
            </div>

            {/* Execution Assumption Levels */}
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono text-slate-400">PRICE ASSUMPTIONS</span>
                <span className="text-[10px] font-mono text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded border border-blue-500/20">
                  R:R {riskReward}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-1 mt-2 text-center font-mono">
                <div className="bg-slate-800/60 p-1.5 rounded-lg border border-slate-700/50">
                  <div className="text-[10px] text-slate-400">ENTRY</div>
                  <div className="text-xs font-bold text-slate-100">₹{hypothesis.entry_assumption?.toFixed(1)}</div>
                </div>
                <div className="bg-rose-950/30 p-1.5 rounded-lg border border-rose-800/40">
                  <div className="text-[10px] text-rose-400 font-semibold">STOP LOSS</div>
                  <div className="text-xs font-bold text-rose-300">₹{hypothesis.stop_loss_assumption?.toFixed(1)}</div>
                </div>
                <div className="bg-emerald-950/30 p-1.5 rounded-lg border border-emerald-800/40">
                  <div className="text-[10px] text-emerald-400 font-semibold">TARGET</div>
                  <div className="text-xs font-bold text-emerald-300">₹{hypothesis.target_assumption?.toFixed(1)}</div>
                </div>
              </div>
            </div>

            {/* Paper Trading Action */}
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800 flex flex-col justify-between">
              <span className="text-[11px] font-mono text-slate-400">SIMULATED EXECUTION</span>
              <p className="text-xs text-slate-400 mt-1">
                Virtual execution with ₹1,00,000 capital, 0.03% brokerage, and 0.02% slippage model.
              </p>
              <button
                onClick={() => onExecutePaperTrade(hypothesis)}
                className={`w-full py-2 px-3 rounded-xl font-bold text-xs flex items-center justify-center gap-1.5 shadow-lg transition mt-2 ${
                  hypothesis.market_direction === 'BULLISH'
                    ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/20'
                    : hypothesis.market_direction === 'BEARISH'
                    ? 'bg-rose-600 hover:bg-rose-500 text-white shadow-rose-600/20'
                    : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-600/20'
                }`}
              >
                <span>Execute Virtual {hypothesis.market_direction === 'BEARISH' ? 'SHORT' : 'BUY'} Order</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

          </div>

          {/* Thesis Statement */}
          <div className="bg-blue-950/20 border border-blue-500/20 rounded-xl p-3.5">
            <h4 className="text-xs font-bold text-blue-300 uppercase tracking-wider mb-1">
              Core Quantitative Thesis
            </h4>
            <p className="text-xs text-slate-200 leading-relaxed">
              {hypothesis.hypothesis}
            </p>
          </div>

          {/* Supporting Evidence & Invalidation Conditions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            
            {/* Supporting Evidence */}
            <div className="bg-slate-900/60 border border-slate-800 p-3.5 rounded-xl flex flex-col space-y-2">
              <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-300 uppercase">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Supporting Technical Evidence</span>
              </div>
              <ul className="space-y-1.5 text-xs text-slate-400">
                {hypothesis.supporting_evidence?.map((item, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-blue-400 font-bold">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Invalidation Conditions */}
            <div className="bg-slate-900/60 border border-slate-800 p-3.5 rounded-xl flex flex-col space-y-2">
              <div className="flex items-center space-x-1.5 text-xs font-bold text-rose-400 uppercase">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                <span>Thesis Invalidation Conditions</span>
              </div>
              <ul className="space-y-1.5 text-xs text-slate-400">
                {hypothesis.invalidation_conditions?.map((item, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-rose-400 font-bold">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

          </div>

          {/* Risk Explanation */}
          <div className="bg-slate-900/40 border border-slate-800/80 p-3 rounded-xl flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div className="text-xs text-slate-400 leading-relaxed">
              <span className="text-slate-200 font-semibold">Downside & Execution Risk: </span>
              {hypothesis.risk_explanation}
            </div>
          </div>

          {/* Recalled Hindsight Lessons Section */}
          {hypothesis.recalled_lessons && hypothesis.recalled_lessons.length > 0 && (
            <div className="bg-purple-950/20 border border-purple-500/30 p-3.5 rounded-xl">
              <div className="flex items-center space-x-1.5 text-xs font-bold text-purple-300 uppercase mb-2">
                <Brain className="w-4 h-4 text-purple-400" />
                <span>Lessons Recalled from Hindsight Long-Term Memory Bank</span>
              </div>
              <ul className="space-y-1.5 text-xs text-purple-200/90 font-mono">
                {hypothesis.recalled_lessons.map((lesson, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-purple-900/20 p-2 rounded-lg border border-purple-800/30">
                    <span className="text-purple-400 font-bold">L{idx+1}:</span>
                    <span>{lesson}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

        </div>
      )}

    </div>
  );
};
