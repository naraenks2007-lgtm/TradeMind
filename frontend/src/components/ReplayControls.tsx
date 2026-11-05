import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  StepForward, 
  FastForward, 
  Clock, 
  ShieldAlert,
  Calendar
} from 'lucide-react';
import { ReplayState } from '../types';
import { api } from '../services/api';

interface ReplayControlsProps {
  currentSymbol: string;
  replayState: ReplayState | null;
  onStateChanged: () => void;
  onExitReplay: () => void;
}

export const ReplayControls: React.FC<ReplayControlsProps> = ({
  currentSymbol,
  replayState,
  onStateChanged,
  onExitReplay
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState<number>(replayState?.speed || 1);
  const [startDate, setStartDate] = useState('');

  // Auto-play timer
  useEffect(() => {
    let interval: any = null;
    if (isPlaying) {
      const delay = Math.max(100, Math.round(1500 / speed));
      interval = setInterval(async () => {
        try {
          const res = await api.stepReplay(1);
          if (res.current_index >= res.total_candles - 1) {
            setIsPlaying(false);
          }
          onStateChanged();
        } catch (e) {
          setIsPlaying(false);
        }
      }, delay);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying, speed, onStateChanged]);

  const handleStep = async () => {
    try {
      await api.stepReplay(1);
      onStateChanged();
    } catch (e) {
      console.error(e);
    }
  };

  const handleSpeedChange = async (newSpeed: number) => {
    setSpeed(newSpeed);
    try {
      await api.setReplaySpeed(newSpeed);
      onStateChanged();
    } catch (e) {
      console.error(e);
    }
  };

  const handleReset = async () => {
    setIsPlaying(false);
    try {
      await api.startReplay(currentSymbol, startDate || undefined);
      onStateChanged();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="bg-[#101623] border border-amber-500/30 rounded-2xl p-4 shadow-xl space-y-3">
      
      {/* Top Banner */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <div className="px-2.5 py-1 rounded-md bg-amber-500/20 text-amber-300 font-mono text-xs font-bold border border-amber-500/40 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping"></span>
            HISTORICAL REPLAY
          </div>
          <span className="text-xs text-slate-400">
            Strict Zero Look-Ahead Bias Mode
          </span>
        </div>

        <div className="flex items-center space-x-3">
          <div className="text-right">
            <span className="text-[10px] text-slate-500 font-mono uppercase block">Simulated Date</span>
            <span className="text-xs font-mono font-bold text-amber-400">
              {replayState?.current_date || 'Loading...'}
            </span>
          </div>

          <button
            onClick={onExitReplay}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg transition"
          >
            Exit Replay
          </button>
        </div>
      </div>

      {/* Control Buttons & Speed */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        
        {/* Playback Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center space-x-2 transition shadow-md ${
              isPlaying
                ? 'bg-amber-600 hover:bg-amber-500 text-white shadow-amber-600/30'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/30'
            }`}
          >
            {isPlaying ? (
              <>
                <Pause className="w-3.5 h-3.5" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Play</span>
              </>
            )}
          </button>

          <button
            onClick={handleStep}
            disabled={isPlaying}
            className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs font-medium flex items-center space-x-1.5 border border-slate-700"
          >
            <StepForward className="w-3.5 h-3.5 text-blue-400" />
            <span>Step Candle</span>
          </button>

          <button
            onClick={handleReset}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700"
            title="Reset to beginning"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Speed Selector */}
        <div className="flex items-center space-x-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
          <span className="text-[10px] text-slate-500 px-2 font-mono uppercase">Speed:</span>
          {[1, 2, 5, 10, 20, 50].map((s) => (
            <button
              key={s}
              onClick={() => handleSpeedChange(s)}
              className={`px-2 py-1 rounded-lg text-xs font-mono transition ${
                speed === s
                  ? 'bg-amber-500 text-black font-bold'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {s}x
            </button>
          ))}
        </div>

      </div>

      {/* Progress Scrubber */}
      <div className="space-y-1">
        <div className="flex justify-between text-[11px] font-mono text-slate-400">
          <span>Bar: {replayState?.current_index || 0} / {replayState?.total_candles || 0}</span>
          <span>Price: ₹{replayState?.current_price?.toFixed(2) || '0.00'}</span>
          <span>{replayState?.progress_pct || 0}% Completed</span>
        </div>
        <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
          <div 
            className="bg-gradient-to-r from-amber-500 to-orange-500 h-full transition-all duration-200"
            style={{ width: `${replayState?.progress_pct || 0}%` }}
          />
        </div>
      </div>

    </div>
  );
};
