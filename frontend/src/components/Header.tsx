import React from 'react';
import { 
  TrendingUp, 
  Brain, 
  Database, 
  Upload, 
  Cpu, 
  CheckCircle2, 
  AlertTriangle,
  RefreshCw,
  PlayCircle,
  MessageSquare,
  Key
} from 'lucide-react';
import { SystemHealth } from '../types';

interface HeaderProps {
  health: SystemHealth | null;
  onOpenUpload: () => void;
  onOpenUpstox: () => void;
  activeTab: 'terminal' | 'loop' | 'chat' | 'experiment' | 'portfolio' | 'memory';
  setActiveTab: (tab: 'terminal' | 'loop' | 'chat' | 'experiment' | 'portfolio' | 'memory') => void;
  isReplayActive: boolean;
  onToggleReplay: () => void;
  onRefresh: () => void;
  loading: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  onOpenUpload,
  onOpenUpstox,
  activeTab,
  setActiveTab,
  isReplayActive,
  onToggleReplay,
  onRefresh,
  loading
}) => {
  const isGroqOnline = health?.groq?.connected;
  const isHindsightOnline = health?.hindsight?.connected;
  const isUpstoxOnline = health?.upstox?.authenticated;

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
        <nav className="flex items-center space-x-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800/80 overflow-x-auto scrollbar-none">
          <button
            onClick={() => setActiveTab('loop')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 shrink-0 ${
              activeTab === 'loop'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-600/30 font-bold'
                : 'text-blue-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
            <span>AI Workflow Loop</span>
          </button>
          
          <button
            onClick={() => setActiveTab('terminal')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 ${
              activeTab === 'terminal'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30 font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            Trading Terminal
          </button>

          <button
            onClick={() => setActiveTab('chat')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 shrink-0 ${
              activeTab === 'chat'
                ? 'bg-cyan-600 text-white shadow-md shadow-cyan-600/30 font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>AI Market Chat</span>
          </button>

          <button
            onClick={() => setActiveTab('experiment')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 shrink-0 ${
              activeTab === 'experiment'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <Brain className="w-3.5 h-3.5" />
            <span>Memory vs No-Memory Lab</span>
          </button>

          <button
            onClick={() => setActiveTab('portfolio')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 ${
              activeTab === 'portfolio'
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30 font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            Paper Portfolio
          </button>

          <button
            onClick={() => setActiveTab('memory')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 ${
              activeTab === 'memory'
                ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30 font-bold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            Hindsight Memory
          </button>
        </nav>

        {/* Action Controls & Health */}
        <div className="flex items-center space-x-2">
          
          {/* Replay Mode Toggle */}
          <button
            onClick={onToggleReplay}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition ${
              isReplayActive
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-md shadow-amber-500/20'
                : 'bg-slate-900 text-slate-300 hover:text-white border-slate-700'
            }`}
          >
            <PlayCircle className="w-3.5 h-3.5 text-amber-400" />
            <span>{isReplayActive ? 'Replay Mode (Active)' : 'Start Replay'}</span>
          </button>

          {/* Upstox Status & Connect Button */}
          <button
            onClick={onOpenUpstox}
            title={health?.upstox?.message || 'Upstox Connection'}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border text-xs font-mono font-medium transition ${
              isUpstoxOnline
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-purple-500/10 text-purple-300 hover:bg-purple-500/20 border-purple-500/30'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${isUpstoxOnline ? 'bg-emerald-400' : 'bg-purple-400 animate-pulse'}`}></span>
            <span>{isUpstoxOnline ? 'Upstox Live' : 'Connect Upstox'}</span>
          </button>

          {/* Groq Status */}
          <div 
            title={`Groq LLM: ${health?.groq?.model || 'gpt-oss-120b'} (${isGroqOnline ? 'Connected' : 'Offline'})`}
            className={`hidden xl:flex items-center space-x-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono ${
              isGroqOnline
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-red-500/10 text-red-400 border-red-500/30'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>Groq</span>
          </div>

          {/* Hindsight Status */}
          <div 
            title={`Hindsight Memory: ${health?.hindsight?.status_message}`}
            className={`hidden xl:flex items-center space-x-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono ${
              isHindsightOnline
                ? 'bg-purple-500/10 text-purple-400 border-purple-500/30'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
            }`}
          >
            <Brain className="w-3.5 h-3.5" />
            <span>Memory</span>
          </div>

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
