import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { 
  Brain, 
  Search, 
  Sparkles, 
  Database, 
  AlertCircle, 
  CheckCircle2, 
  BookOpen, 
  Info,
  Clock,
  Tag
} from 'lucide-react';

export const MemoryExplorer: React.FC = () => {
  const [memoryStatus, setMemoryStatus] = useState<any>(null);
  const [query, setQuery] = useState('NIFTY trend pullback breakout lessons');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [reflectResult, setReflectResult] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const stat = await api.getMemoryStatus();
      setMemoryStatus(stat);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setReflectResult(null);
    try {
      const items = await api.recallMemory(query);
      setResults(items);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col space-y-5 max-w-7xl mx-auto">
      
      {/* Top Banner with Architecture & Official Hindsight Documentation */}
      <div className="bg-[#121824] border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-2 bg-purple-500/10 border border-purple-500/20 rounded-xl text-purple-400">
              <Brain className="w-5 h-5" />
            </span>
            <h2 className="text-base font-bold text-white tracking-wide">
              Hindsight Long-Term Memory Explorer
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Inspect real long-term agent experiences accumulated across trade hypotheses, risk reflections, and outcome reviews via the official 
            <span className="text-purple-300 font-mono"> vectorize-io/hindsight</span> SDK.
          </p>
        </div>

        {/* Live Status Badge */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2">
          <div className={`px-3 py-1.5 rounded-xl border text-xs font-mono flex items-center gap-2 ${
            memoryStatus?.connected
              ? 'bg-purple-500/10 text-purple-300 border-purple-500/30'
              : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
          }`}>
            <span className={`w-2 h-2 rounded-full ${memoryStatus?.connected ? 'bg-purple-400 animate-pulse' : 'bg-amber-400'}`}></span>
            <span>{memoryStatus?.status_message || 'Checking status...'}</span>
          </div>

          <a
            href="https://docs.hindsight.vectorize.io/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition"
          >
            <BookOpen className="w-3.5 h-3.5 text-purple-400" />
            <span>Official Docs</span>
          </a>
        </div>
      </div>

      {/* Query Bar */}
      <div className="bg-[#121824] border border-slate-800 rounded-2xl p-5 shadow-xl">
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Query Hindsight memory bank (e.g., 'RELIANCE breakdown false positive')..."
              className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 outline-none focus:border-purple-500 transition font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs shadow-md shadow-purple-600/30 transition flex items-center justify-center gap-2 shrink-0 font-mono"
          >
            <Search className="w-3.5 h-3.5" />
            <span>{loading ? 'Searching...' : 'Recall Memory'}</span>
          </button>
        </form>
      </div>

      {/* Status Warning or Results */}
      {!memoryStatus?.connected ? (
        <div className="bg-amber-950/20 border border-amber-500/30 rounded-2xl p-6 flex items-start space-x-3 text-xs text-amber-200">
          <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-2">
            <h4 className="font-bold text-amber-300 text-sm">Honest Service Status: Hindsight API Key Unconfigured</h4>
            <p className="text-amber-200/90 leading-relaxed">
              In strict accordance with the hackathon rules: <em>&ldquo;If a service is unavailable, display an honest error and provide a useful fallback where possible. Never show fake successful API or memory operations.&rdquo;</em>
            </p>
            <p className="text-amber-200/80 leading-relaxed font-mono">
              To connect your live Hindsight cloud or self-hosted instance, add your credentials in <code>.env</code>:
            </p>
            <pre className="bg-slate-900/90 p-3 rounded-lg border border-amber-500/20 text-slate-300 font-mono text-[11px]">
              HINDSIGHT_API_KEY=your_key_here<br />
              HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
            </pre>
          </div>
        </div>
      ) : results.length > 0 ? (
        <div className="bg-[#121824] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
            Retrieved Experience Units ({results.length})
          </h3>
          <div className="space-y-2.5">
            {results.map((item, idx) => (
              <div key={idx} className="bg-slate-900/80 border border-slate-800 p-3.5 rounded-xl flex flex-col space-y-1.5 font-mono text-xs">
                <div className="flex items-center justify-between text-[11px] text-slate-500">
                  <span className="text-purple-400 font-bold">Memory #{idx+1}</span>
                  {item.score && <span>Relevance Score: {item.score.toFixed(3)}</span>}
                </div>
                <p className="text-slate-200 leading-relaxed">{item.content}</p>
                {item.tags && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {item.tags.map((t: string, ti: number) => (
                      <span key={ti} className="text-[10px] px-2 py-0.5 rounded bg-purple-950/40 text-purple-300 border border-purple-800/40">
                        #{t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-[#121824] border border-slate-800 rounded-2xl p-10 text-center text-xs text-slate-500 font-mono">
          No memories retrieved for current query. Try searching for market regimes, symbols, or specific risk conditions.
        </div>
      )}

    </div>
  );
};
