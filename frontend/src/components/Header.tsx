import React from 'react';
import { 
  TrendingUp, 
  Brain, 
  Database, 
  Upload, 
  Cpu, 
  CheckCircle2, 
  AlertTriangle,
  RefreshCw
} from 'lucide-react';
import { SystemHealth } from '../types';

interface HeaderProps {
  health: SystemHealth | null;
  onOpenUpload: () => void;
  activeTab: 'terminal' | 'loop' | 'experiment' | 'portfolio' | 'memory';
  setActiveTab: (tab: 'terminal' | 'loop' | 'experiment' | 'portfolio' | 'memory') => void;
  onRefresh: () => void;
  loading: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  onOpenUpload,
  activeTab,
  setActiveTab,
  onRefresh,
  loading
}) => {
  const isGroqOnline = health?.groq?.connected;
  const isHindsightOnline = health?.hindsight?.connected;

  return (
    <header className="border-b border-slate-800 bg-[#0F141F]/80 backdrop-blur-md sticky top-0 z-40 px-4 lg:px-6 py-3">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 max-w-7xl mx-auto">
        
        {/* Brand & Title */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 p-[2px] shadow-lg shadow-blue-500/20">
            <div className="w-full h-full bg-[#0B0E14] rounded-[10px] flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-blue-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5">
                TradeMind <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono font-medium">AI v1.0</span>
              </h1>
            </div>
            <p className="text-xs text-slate-400">
              Quantitative Market Hypothesis & Long-Term Memory Engine
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800/80">
          <button
            onClick={() => setActiveTab('loop')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'loop'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-600/30 font-bold'
                : 'text-blue-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
            <span>Compelling AI Loop</span>
          </button>
          <button
            onClick={() => setActiveTab('terminal')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === 'terminal'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            Trading Terminal
          </button>
          <button
            onClick={() => setActiveTab('experiment')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'experiment'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <Brain className="w-3.5 h-3.5" />
            Memory vs No-Memory Lab
          </button>
          <button
            onClick={() => setActiveTab('portfolio')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === 'portfolio'
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            Paper Portfolio (₹1,00,000)
          </button>
          <button
            onClick={() => setActiveTab('memory')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === 'memory'
                ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            Hindsight Explorer
          </button>
        </nav>

        {/* Status Indicators & Upload */}
        <div className="flex items-center space-x-2">
          {/* Groq Status */}
          <div 
            title={`Groq LLM: ${health?.groq?.model || 'openai/gpt-oss-120b'} (${isGroqOnline ? 'Connected' : 'Offline'})`}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono ${
              isGroqOnline
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-red-500/10 text-red-400 border-red-500/30'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Groq:</span>
            <span>{health?.groq?.model?.split('/')[1] || 'gpt-oss-120b'}</span>
          </div>

          {/* Hindsight Status */}
          <div 
            title={`Hindsight Memory: ${health?.hindsight?.status_message}`}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono ${
              isHindsightOnline
                ? 'bg-purple-500/10 text-purple-400 border-purple-500/30'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
            }`}
          >
            <Brain className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Hindsight:</span>
            <span>{isHindsightOnline ? 'Active' : 'Unconfigured'}</span>
          </div>

          {/* Upload Button */}
          <button
            onClick={onOpenUpload}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition"
          >
            <Upload className="w-3.5 h-3.5 text-blue-400" />
            <span className="hidden md:inline">Upload CSV</span>
          </button>

          {/* Refresh */}
          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-400' : ''}`} />
          </button>
        </div>

      </div>
    </header>
  );
};
