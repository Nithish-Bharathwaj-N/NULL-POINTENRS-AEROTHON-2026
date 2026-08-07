import React from 'react';
import { FleetMember } from '@/types';
import { Panel, StatusBadge, HealthRing } from '@/components';
import { List } from 'lucide-react';

interface FleetListPanelProps {
  fleet: FleetMember[];
  selectedTail: string;
  onSelectTail: (tail: string) => void;
}

export const FleetListPanel: React.FC<FleetListPanelProps> = React.memo(({ fleet, selectedTail, onSelectTail }) => (
  <Panel title="IAF Operational Fleet Directory Table" icon={List} className="h-full" noPad>
    <div className="overflow-x-auto font-mono text-xs select-none">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-slate-100 text-slate-700 font-bold uppercase tracking-wider text-[10px] border-b border-slate-300">
            <th className="p-2.5">Tail Number</th>
            <th className="p-2.5">Squadron & Base</th>
            <th className="p-2.5">Operational Status</th>
            <th className="p-2.5">Assigned Pilot & Crew</th>
            <th className="p-2.5 text-center">Engine Health</th>
            <th className="p-2.5 text-center">Airframe Health</th>
            <th className="p-2.5 text-right">Fuel Pct</th>
            <th className="p-2.5 text-right">Sortie Hrs</th>
            <th className="p-2.5 text-right">TBO RUL</th>
            <th className="p-2.5">Active Diagnostic Warning</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200">
          {fleet.map((ac) => {
            const isSelected = selectedTail === ac.tail;
            return (
              <tr
                key={ac.id}
                onClick={() => onSelectTail(ac.tail)}
                className={`transition-colors cursor-pointer group ${
                  isSelected ? 'bg-sky-50 border-l-4 border-[#003366] font-bold text-slate-900' : 'hover:bg-slate-50 text-slate-700'
                }`}
              >
                <td className="p-2.5 font-bold font-rajdhani text-sm uppercase text-[#003366]">{ac.tail}</td>
                <td className="p-2.5">
                  <div className="font-bold text-slate-900">{ac.squadron}</div>
                  <div className="text-[10px] text-slate-500">{ac.base}</div>
                </td>
                <td className="p-2.5"><StatusBadge status={ac.status} size="sm" /></td>
                <td className="p-2.5">
                  <div className="font-bold text-slate-900">{ac.pilot}</div>
                  <div className="text-[10px] text-slate-500">{ac.crew}</div>
                </td>
                <td className="p-2.5 text-center">
                  <div className="flex justify-center"><HealthRing health={ac.engineHealth} size={32} stroke={3} /></div>
                </td>
                <td className="p-2.5 text-center">
                  <div className="flex justify-center"><HealthRing health={ac.airframeHealth} size={32} stroke={3} /></div>
                </td>
                <td className="p-2.5 text-right font-bold">{ac.fuelPct}%</td>
                <td className="p-2.5 text-right">{ac.sortieHours} Hrs</td>
                <td className={`p-2.5 text-right font-bold ${ac.tboRulHrs < 300 ? 'text-amber-600' : ''}`}>{ac.tboRulHrs} Hrs</td>
                <td className="p-2.5">
                  {ac.warning ? (
                    <span className="text-red-600 font-bold text-[11px] flex items-center gap-1">
                      <span>⚠️ {ac.warning}</span>
                    </span>
                  ) : (
                    <span className="text-emerald-600 text-[10px]">NOMINAL</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  </Panel>
));
FleetListPanel.displayName = 'FleetListPanel';
