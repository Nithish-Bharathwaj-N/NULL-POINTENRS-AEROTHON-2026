import React from 'react';
import { Panel, ValueBadge } from '@/components';
import { Plane, Radio } from 'lucide-react';
import { FleetMember } from '@/types';

interface MissionOperationsPanelProps {
  ac: FleetMember;
}

export const MissionOperationsPanel: React.FC<MissionOperationsPanelProps> = React.memo(({ ac }) => {
  const opsData = [
    { label: 'Air Base / Sector', value: ac.base, unit: '' },
    { label: 'Assigned Pilot', value: ac.pilot, unit: '' },
    { label: 'HAL Propulsion Team', value: ac.crew, unit: '' },
    { label: 'Fuel Remaining', value: `${ac.fuelKg} kg`, unit: `(${ac.fuelPct}%)`, status: ac.fuelPct > 30 ? 'NOMINAL' : 'WARNING' },
    { label: 'Airframe Hours', value: ac.sortieHours, unit: 'Hrs', status: 'NOMINAL' },
    { label: 'TBO RUL Remaining', value: ac.tboRulHrs, unit: 'Hrs', status: ac.tboRulHrs > 300 ? 'NOMINAL' : 'WARNING' },
    { label: 'Sortie Status', value: ac.status, unit: '', status: ac.status.includes('Combat') ? 'ACTIVE' : 'STANDBY' },
    { label: 'Link-17 Crypto Key', value: 'VAL-88219-SEC', unit: 'LOCKED', status: 'ACTIVE' },
  ];

  return (
    <Panel title="Sortie & SATCOM Operations Log" icon={Plane} className="h-full">
      <div className="space-y-2 font-mono">
        <div className="p-2 bg-sky-950/80 text-sky-300 rounded-sm border border-sky-800 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-sky-400 animate-pulse" />
            <div>
              <div className="text-xs font-bold font-rajdhani uppercase tracking-wider text-sky-300">LINK-17 TACTICAL SATCOM ACTIVE</div>
              <div className="text-[9px] text-sky-400 font-semibold">DOWNLINK: 100 Hz ARINC-429 • ENCRYPTION: AES-256-GCM</div>
            </div>
          </div>
          <span className="px-1.5 py-0.5 bg-emerald-600 text-white text-[9px] font-bold rounded-xs uppercase">LOCKED</span>
        </div>

        <div className="grid grid-cols-2 gap-2 pt-1">
          {opsData.map((d, i) => (
            <ValueBadge key={i} label={d.label} value={d.value} unit={d.unit} status={d.status} />
          ))}
        </div>
      </div>
    </Panel>
  );
});
MissionOperationsPanel.displayName = 'MissionOperationsPanel';
