import React from 'react';
import { Play, ShieldCheck, Square } from 'lucide-react';
import { useMissionDemo } from '@/hooks/useMissionDemo';
import { missionPlaybackEngine } from '@/services/missionPlaybackEngine';

export const QuickActionsBar: React.FC = React.memo(() => {
  const { isDemoRunning, demoPhase, demoProgress, startDemo, stopDemo } = useMissionDemo();

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-sm p-2 shadow-md flex items-center justify-between gap-3 select-none shrink-0 overflow-x-auto no-scrollbar text-slate-100">
      <div className="flex items-center gap-2 shrink-0">
        <div className="text-[10px] font-mono font-bold text-sky-400 uppercase tracking-wider px-2 border-r border-slate-800 flex items-center gap-1 shrink-0">
          <span>MISSION ACTIONS</span>
        </div>

        {/* Mission Demo Button — primary CTA */}
        {isDemoRunning ? (
          <button
            onClick={stopDemo}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-xs font-rajdhani font-bold text-xs uppercase tracking-wider transition-all shadow-sm shrink-0 bg-amber-600 text-white border border-amber-600 hover:bg-amber-700 cursor-pointer"
          >
            <Square className="w-3 h-3 text-white" />
            <span>STOP DEMO</span>
            <span className="bg-amber-800 text-white text-[9px] px-1.5 py-0.5 rounded-xs font-mono">
              {demoProgress}%
            </span>
          </button>
        ) : (
          <button
            onClick={startDemo}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xs font-rajdhani font-bold text-xs uppercase tracking-wider transition-all shadow-sm shrink-0 bg-[#16A34A] text-white border border-[#16A34A] hover:bg-[#15803d] animate-pulse cursor-pointer"
          >
            <Play className="w-3.5 h-3.5 text-white fill-white" />
            <span>RUN FULL MISSION DEMO</span>
          </button>
        )}

        {isDemoRunning && demoPhase && (
          <div className="px-2 py-1 bg-sky-950/80 border border-sky-800 rounded-xs font-mono text-[10px] font-bold text-sky-300 shrink-0 max-w-[200px] truncate">
            {demoPhase}
          </div>
        )}

        <button
          onClick={() => alert('Link-17 SATCOM Crypto Key Validated — AES-256-GCM LOCKED')}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xs font-rajdhani font-bold text-xs uppercase tracking-wider transition-all shadow-2xs shrink-0 bg-slate-800 border border-slate-700 text-slate-200 hover:bg-slate-700 hover:text-white cursor-pointer"
        >
          <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
          <span>Validate Link-17</span>
        </button>
      </div>

      {/* Playback speed control */}
      <div className="flex items-center gap-1 shrink-0 pl-3 border-l border-slate-800">
        <span className="text-[9px] font-mono font-bold text-slate-400 uppercase tracking-wider mr-1">SIM SPEED</span>
        {[1, 8, 20, 60].map((spd) => (
          <button
            key={spd}
            onClick={() => missionPlaybackEngine.setSpeed(spd)}
            className="px-2 py-0.5 rounded-xs font-mono text-[10px] font-bold bg-slate-800 border border-slate-700 text-slate-300 hover:bg-sky-950 hover:border-sky-500 hover:text-sky-300 transition-colors cursor-pointer"
          >
            {spd}x
          </button>
        ))}
      </div>
    </div>
  );
});
QuickActionsBar.displayName = 'QuickActionsBar';
