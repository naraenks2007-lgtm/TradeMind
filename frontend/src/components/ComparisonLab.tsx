import React, { useState, useEffect } from 'react';
import { ExperimentReport, ScenarioEvaluation } from '../types';
import { api } from '../services/api';
import { 
  Brain, 
  Layers, 
  TrendingUp, 
  TrendingDown, 
  Award, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle,
  RefreshCw,
  Info
} from 'lucide-react';

interface ComparisonLabProps {
  currentSymbol: string;
}

export const ComparisonLab: React.FC<ComparisonLabProps> = ({ currentSymbol }) => {
  const [report, setReport] = useState<ExperimentReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [scenarioCount, setScenarioCount] = useState(6);
  const [selectedScenario, setSelectedScenario] = useState<ScenarioEvaluation | null>(null);

  const fetchExperiment = async () => {
    setLoading(true);
    try {
      const data = await api.getComparison(currentSymbol, scenarioCount);
      setReport(data);
      if (data.scenarios.length > 0) {
        setSelectedScenario(data.scenarios[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExperiment();
  }, [currentSymbol, scenarioCount]);

  return (
    <div className="flex flex-col space-y-5 max-w-7xl mx-auto">
      
      {/* Banner & Controls */}
      <div className="bg-[#121824] border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400">
              <Brain className="w-5 h-5" />
            </span>
            <h2 className="text-base font-bold text-white tracking-wide">
              Memory vs. No-Memory Quantitative Experiment Lab
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Controlled backtest evaluating the performance delta of <strong>Agent B (equipped with Hindsight long-term memory)</strong> against <strong>Agent A (standard memoryless technicals)</strong> across identical historical market slices with zero look-ahead bias.
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <div className="flex items-center space-x-2 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800 text-xs font-mono">
            <span className="text-slate-400">Slices:</span>
            <select
              value={scenarioCount}
              onChange={(e) => setScenarioCount(Number(e.target.value))}
              className="bg-transparent text-white font-bold outline-none cursor-pointer"
            >
              <option value={4} className="bg-slate-900">4 Slices</option>
              <option value={6} className="bg-slate-900">6 Slices</option>
              <option value={8} className="bg-slate-900">8 Slices</option>
              <option value={10} className="bg-slate-900">10 Slices</option>
            </select>
          </div>

          <button
            onClick={fetchExperiment}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-md shadow-indigo-600/30 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Rerun Experiment</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="w-full h-80 bg-[#121824] rounded-2xl border border-slate-800 flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-xs text-slate-400 font-mono">Simulating historical decision slices across Agent A & Agent B...</p>
        </div>
      ) : report ? (
        <>
          {/* Comparative KPI Scoreboard */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3.5">
            
            {/* Directional Accuracy */}
            <div className="bg-[#121824] border border-slate-800 p-4 rounded-2xl flex flex-col justify-between shadow-lg">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Directional Accuracy</span>
              <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-slate-800/80">
                <div>
                  <div className="text-[10px] text-slate-500 font-mono">Agent A (No Mem)</div>
                  <div className="text-lg font-bold font-mono text-slate-300">
                    {report.agent_a_metrics.directional_accuracy_pct}%
                  </div>
                </div>
                <div className="border-l border-slate-800 pl-2">
                  <div className="text-[10px] text-indigo-400 font-mono">Agent B (Hindsight)</div>
                  <div className="text-lg font-bold font-mono text-emerald-400 flex items-center gap-1">
                    <span>{report.agent_b_metrics.directional_accuracy_pct}%</span>
                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                  </div>
                </div>
              </div>
            </div>

            {/* Win Rate */}
            <div className="bg-[#121824] border border-slate-800 p-4 rounded-2xl flex flex-col justify-between shadow-lg">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Win Rate</span>
              <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-slate-800/80">
                <div>
                  <div className="text-[10px] text-slate-500 font-mono">Agent A</div>
                  <div className="text-lg font-bold font-mono text-slate-300">
                    {report.agent_a_metrics.win_rate_pct}%
                  </div>
                </div>
                <div className="border-l border-slate-800 pl-2">
                  <div className="text-[10px] text-indigo-400 font-mono">Agent B</div>
                  <div className="text-lg font-bold font-mono text-emerald-400">
                    {report.agent_b_metrics.win_rate_pct}%
                  </div>
                </div>
              </div>
            </div>

            {/* Cumulative Return */}
            <div className="bg-[#121824] border border-slate-800 p-4 rounded-2xl flex flex-col justify-between shadow-lg">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Simulated Return</span>
              <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-slate-800/80">
                <div>
                  <div className="text-[10px] text-slate-500 font-mono">Agent A</div>
                  <div className={`text-lg font-bold font-mono ${report.agent_a_metrics.total_return_pct >= 0 ? 'text-slate-300' : 'text-rose-400'}`}>
                    {report.agent_a_metrics.total_return_pct >= 0 ? '+' : ''}{report.agent_a_metrics.total_return_pct}%
                  </div>
                </div>
                <div className="border-l border-slate-800 pl-2">
                  <div className="text-[10px] text-indigo-400 font-mono">Agent B</div>
                  <div className={`text-lg font-bold font-mono ${report.agent_b_metrics.total_return_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {report.agent_b_metrics.total_return_pct >= 0 ? '+' : ''}{report.agent_b_metrics.total_return_pct}%
                  </div>
                </div>
              </div>
            </div>

            {/* Repeated Mistakes Count */}
            <div className="bg-[#121824] border border-slate-800 p-4 rounded-2xl flex flex-col justify-between shadow-lg">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Repeated Known Mistakes</span>
              <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-slate-800/80">
                <div>
                  <div className="text-[10px] text-slate-500 font-mono">Agent A</div>
                  <div className="text-lg font-bold font-mono text-rose-400">
                    {report.agent_a_metrics.repeated_mistakes_count}
                  </div>
                </div>
                <div className="border-l border-slate-800 pl-2">
                  <div className="text-[10px] text-indigo-400 font-mono">Agent B</div>
                  <div className="text-lg font-bold font-mono text-emerald-400">
                    {report.agent_b_metrics.repeated_mistakes_count}
                  </div>
                </div>
              </div>
            </div>

          </div>

          {/* Detailed Scenario Explorer */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            
            {/* Scenario List */}
            <div className="bg-[#121824] border border-slate-800 rounded-2xl p-4 shadow-xl flex flex-col space-y-2">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-1 font-mono">
                Historical Test Scenarios ({report.scenarios.length})
              </h3>
              <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
                {report.scenarios.map((scen) => (
                  <button
                    key={scen.scenario_id}
                    onClick={() => setSelectedScenario(scen)}
                    className={`w-full text-left p-3 rounded-xl border transition ${
                      selectedScenario?.scenario_id === scen.scenario_id
                        ? 'bg-indigo-950/30 border-indigo-500/50 shadow-md'
                        : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="font-bold text-white">{scen.scenario_id}</span>
                      <span className="text-slate-400">{scen.decision_date}</span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] font-mono mt-1 text-slate-400">
                      <span>Close: ₹{scen.decision_close_price.toFixed(1)}</span>
                      <span className={scen.actual_return_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                        Next 5D: {scen.actual_return_pct >= 0 ? '+' : ''}{scen.actual_return_pct}%
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Side-by-Side Agent Comparison for Selected Scenario */}
            {selectedScenario && (
              <div className="lg:col-span-2 bg-[#121824] border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <span>Scenario {selectedScenario.scenario_id}</span>
                      <span className="text-xs font-mono font-normal text-slate-400">({selectedScenario.decision_date})</span>
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Actual future 5-day market movement: <span className="text-white font-mono font-bold">{selectedScenario.actual_market_trend}</span> ({selectedScenario.actual_return_pct > 0 ? '+' : ''}{selectedScenario.actual_return_pct}%)
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  
                  {/* Agent A: No Memory */}
                  <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex flex-col justify-between space-y-3">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-300 font-mono">AGENT A (NO MEMORY)</span>
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                          selectedScenario.agent_a_no_memory.was_direction_correct
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                        }`}>
                          {selectedScenario.agent_a_no_memory.was_direction_correct ? 'Correct Direction' : 'Wrong Direction'}
                        </span>
                      </div>
                      <div className="text-sm font-bold font-mono text-white mt-2">
                        {selectedScenario.agent_a_no_memory.market_direction} (Conf: {(selectedScenario.agent_a_no_memory.confidence * 100).toFixed(0)}%)
                      </div>
                      <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                        {selectedScenario.agent_a_no_memory.hypothesis_summary}
                      </p>
                    </div>

                    {selectedScenario.agent_a_no_memory.repeated_known_mistake && (
                      <div className="bg-rose-950/30 border border-rose-800/40 p-2.5 rounded-lg text-xs text-rose-300 flex items-start gap-1.5 font-mono">
                        <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                        <span>Repeated overbought / squeeze trap due to absence of memory.</span>
                      </div>
                    )}
                  </div>

                  {/* Agent B: With Hindsight Memory */}
                  <div className="bg-indigo-950/20 border border-indigo-500/30 p-4 rounded-xl flex flex-col justify-between space-y-3">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-indigo-300 font-mono flex items-center gap-1.5">
                          <Brain className="w-3.5 h-3.5 text-indigo-400" />
                          <span>AGENT B (WITH HINDSIGHT)</span>
                        </span>
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                          selectedScenario.agent_b_with_memory.was_direction_correct
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                        }`}>
                          {selectedScenario.agent_b_with_memory.was_direction_correct ? 'Correct / Protected' : 'Neutral Position'}
                        </span>
                      </div>
                      <div className="text-sm font-bold font-mono text-emerald-400 mt-2">
                        {selectedScenario.agent_b_with_memory.market_direction} (Conf: {(selectedScenario.agent_b_with_memory.confidence * 100).toFixed(0)}%)
                      </div>
                      <p className="text-xs text-indigo-100/90 mt-2 leading-relaxed">
                        {selectedScenario.agent_b_with_memory.hypothesis_summary}
                      </p>
                    </div>

                    {/* Recalled Lesson */}
                    {selectedScenario.agent_b_with_memory.recalled_lessons_used.length > 0 && (
                      <div className="bg-indigo-900/30 border border-indigo-500/30 p-2.5 rounded-lg text-xs text-indigo-200 flex flex-col gap-1 font-mono">
                        <span className="text-[10px] text-indigo-400 font-bold uppercase">Hindsight Memory Applied:</span>
                        <span>{selectedScenario.agent_b_with_memory.recalled_lessons_used[0]}</span>
                      </div>
                    )}
                  </div>

                </div>
              </div>
            )}

          </div>

          {/* Legal / Experimental Disclaimer */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 flex items-start gap-2.5 text-xs text-slate-400">
            <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              {report.disclaimer}
            </p>
          </div>
        </>
      ) : null}

    </div>
  );
};
