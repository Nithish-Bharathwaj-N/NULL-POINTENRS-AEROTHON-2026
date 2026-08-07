import React from 'react';
import { FleetMember } from '@/types';
import { Panel, StatusBadge, HealthRing } from '@/components';
import { Plane, AlertTriangle } from 'lucide-react';

interface FleetMatrixPanelProps {
  fleet: FleetMember[];
  selectedTail: string;
  onSelectTail: (tail: string) => void;
}

export const FleetMatrixPanel: React.FC<FleetMatrixPanelProps> = React.memo(({ fleet, selectedTail, onSelectTail }) => {
  const squadrons = [
    { name: 'No. 45 Sqn (Flying Daggers)', base: 'Jodhpur (Forward Air Base)', filter: 'No. 45 Sqn' },
    { name: 'No. 18 Sqn (Flying Bullets)', base: 'Sulur (Southern Air Command)', filter: 'No. 18 Sqn' },
    { name: 'HAL Flight Test Center (FTC)', base: 'Ambala (Test Flight Corridor)', filter: 'HAL Flight Test' },
  ];

  return (
    <Panel title="IAF Operational Squadron Matrix (3 Squadrons • 10 Aircraft)" icon={Plane} className="h-full">
      <div className="space-y-4 font-mono select-none">
        {squadrons.map((sqn, idx) => {
          const sqnAc = fleet.filter((a) => a.squadron.includes(sqn.filter));
          const sqnAvgHealth = Math.round(sqnAc.reduce((acc, a) => acc + a.health, 0) / (sqnAc.length || 1));
          const readyCount = sqnAc.filter((a) => !a.status.includes('Grounded')).length;

          return (
            <div key={idx} className="bg-slate-950/80 border border-slate-800 rounded-sm p-3 shadow-sm space-y-2.5">
              {/* Squadron Header Bar */}
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <div>
                  <div className="font-rajdhani font-bold text-sm text-white uppercase tracking-wider flex items-center gap-2">
                    <span>{sqn.name}</span>
                    <span className="text-[10px] font-mono font-semibold bg-sky-950 text-sky-300 px-2 py-0.5 rounded-xs border border-sky-800">
                      BASE: {sqn.base}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 font-bold uppercase">MISSION READINESS</span>
                    <div className="text-xs font-bold text-white">{readyCount} / {sqnAc.length} A/C Operational</div>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-sky-950 text-sky-300 border border-sky-800 flex items-center justify-center font-bold text-xs shadow-sm">
                    {sqnAvgHealth}%
                  </div>
                </div>
              </div>

              {/* Aircraft Matrix Grid Cards */}
              <div className="grid grid-cols-4 gap-2.5">
                {sqnAc.map((ac) => {
                  const isSelected = selectedTail === ac.tail;
                  return (
                    <div
                      key={ac.id}
                      onClick={() => onSelectTail(ac.tail)}
                      className={`p-2.5 rounded-sm border transition-all cursor-pointer flex flex-col justify-between gap-2 relative overflow-hidden group ${
                        isSelected
                          ? 'bg-sky-950/90 text-white border-sky-400 shadow-md ring-1 ring-sky-400'
                          : 'bg-slate-900 border-slate-800 text-slate-200 hover:border-sky-500 hover:shadow-sm'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-1">
                        <div>
                          <div className={`font-rajdhani font-bold text-sm uppercase tracking-wider ${isSelected ? 'text-sky-300' : 'text-white'}`}>
                            {ac.tail}
                          </div>
                          <div className={`text-[10px] ${isSelected ? 'text-sky-300 font-semibold' : 'text-slate-400'}`}>
                            {ac.pilot}
                          </div>
                        </div>
                        <HealthRing health={ac.health} size={36} stroke={3} />
                      </div>

                      <div className="space-y-1 pt-1 border-t border-slate-800 text-[10px]">
                        <div className="flex items-center justify-between">
                          <span className="text-slate-400 font-semibold">STATUS:</span>
                          <StatusBadge status={ac.status} size="sm" />
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-400 font-semibold">LOCATION:</span>
                          <span className="font-bold truncate max-w-[100px] text-white">{ac.location}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-400 font-semibold">TBO RUL:</span>
                          <span className={`font-bold ${ac.tboRulHrs < 300 ? 'text-amber-400 font-extrabold' : 'text-white'}`}>
                            {ac.tboRulHrs} Hrs
                          </span>
                        </div>
                      </div>

                      {ac.warning && (
                        <div className={`mt-1 p-1 rounded-xs text-[9px] font-bold flex items-center gap-1 leading-tight ${
                          isSelected ? 'bg-red-950 text-red-200 border border-red-800' : 'bg-red-950/80 text-red-300 border border-red-900'
                        }`}>
                          <AlertTriangle className="w-3 h-3 text-red-400 shrink-0" />
                          <span className="truncate">{ac.warning}</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
});
FleetMatrixPanel.displayName = 'FleetMatrixPanel';
