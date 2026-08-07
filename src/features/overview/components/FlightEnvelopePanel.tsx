import React from 'react';
import { Panel, ValueBadge } from '@/components';
import { Gauge } from 'lucide-react';
import { FleetMember } from '@/types';
import { useMissionStore } from '@/stores/useMissionStore';

interface FlightEnvelopePanelProps {
  ac: FleetMember;
}

export const FlightEnvelopePanel: React.FC<FlightEnvelopePanelProps> = React.memo(({ ac }) => {
  const env = useMissionStore((state) => state.flightEnvelope);

  const envData = [
    { label: 'Mach Number', value: env.mach.toFixed(2), unit: 'Mach', status: env.mach > 1.2 ? 'WARNING' : 'NOMINAL' },
    { label: 'Altitude (MSL)', value: Math.round(env.altitudeFt).toLocaleString(), unit: 'Ft', status: 'NOMINAL' },
    { label: 'True Airspeed (TAS)', value: Math.round(env.tasKts).toString(), unit: 'Kts', status: 'NOMINAL' },
    { label: 'Throttle Angle (TLA)', value: env.throttlePct.toFixed(1), unit: '%', status: env.throttlePct > 90 ? 'WARNING' : 'NOMINAL' },
    { label: 'G-Load Factor', value: `${env.gLoad >= 0 ? '+' : ''}${env.gLoad.toFixed(2)}`, unit: 'G', status: env.gLoad > 4.5 ? 'CRITICAL' : 'NOMINAL' },
    { label: 'Angle of Attack (α)', value: env.aoaDeg.toFixed(1), unit: 'Deg', status: env.aoaDeg > 15 ? 'WARNING' : 'NOMINAL' },
    { label: 'Fuel Flow Rate', value: Math.round(env.fuelFlowKgH).toLocaleString(), unit: 'kg/h', status: 'NOMINAL' },
    { label: 'Isentropic Eff', value: env.isentropicEffPct.toFixed(1), unit: '%', status: env.isentropicEffPct < 85 ? 'WARNING' : 'NOMINAL' },
  ];

  return (
    <Panel title={`Real-Time Flight Envelope (${ac.tail})`} icon={Gauge} className="h-full">
      <div className="grid grid-cols-2 gap-2 font-mono">
        {envData.map((d, i) => (
          <ValueBadge key={i} label={d.label} value={d.value} unit={d.unit} status={d.status} />
        ))}
      </div>
    </Panel>
  );
});
FlightEnvelopePanel.displayName = 'FlightEnvelopePanel';
