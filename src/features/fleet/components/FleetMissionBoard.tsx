import React from 'react';
import { Panel, StatusBadge } from '@/components';
import { Radio } from 'lucide-react';
import { FleetMember } from '@/types';
import { useUiStore } from '@/stores';

interface FleetMissionBoardProps {
  fleet: FleetMember[];
  onSelectTail: (tail: string) => void;
}

export const FleetMissionBoard: React.FC<FleetMissionBoardProps> = React.memo(({ fleet, onSelectTail }) => {
  const { setView } = useUiStore();
  const airborne = fleet.filter((a) => a.status.includes('Combat') || a.status.includes('Supersonic') || a.status.includes('Escort'));

  return (
    <Panel
      title="Active Airborne Combat & Test Sorties Board"
      icon={Radio}
      className="h-full"
      right={
        <button
          onClick={() => setView('eventtimeline')}
          className="text-xs font-bold font-rajdhani uppercase tracking-wider text-sky-400 hover:underline cursor-pointer"
        >
          View Live Sortie Radar →
        </button>
      }
    >
      <div className="grid grid-cols-2 gap-2 font-mono text-xs">
        {airborne.map((ac) => (
          <div
            key={ac.id}
            onClick={() => onSelectTail(ac.tail)}
            className="p-2.5 bg-slate-950/80 border border-slate-800 hover:border-sky-500 rounded-sm shadow-sm transition-all cursor-pointer flex items-center justify-between group"
          >
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <span className="font-bold font-rajdhani text-sm uppercase text-sky-300">{ac.tail}</span>
                <StatusBadge status="ACTIVE" size="sm" />
              </div>
              <div className="font-bold text-white">{ac.missionType} • {ac.pilot}</div>
              <div className="text-[10px] text-slate-400">{ac.location}</div>
            </div>
            <div className="text-right">
              <div className="text-[10px] text-slate-400 font-bold uppercase">FUEL / RUL</div>
              <div className="font-bold text-white">{ac.fuelPct}% / {ac.tboRulHrs}h</div>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
});
FleetMissionBoard.displayName = 'FleetMissionBoard';
