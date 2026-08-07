import React, { useMemo } from 'react';
import { FleetMember } from '@/types';
import { Panel, ValueBadge, MiniSparkline } from '@/components';
import { Shield, ArrowRight, Activity, Zap } from 'lucide-react';
import { useUiStore, useMissionStore, useTelemetryStore, useAircraftStore } from '@/stores';

interface FleetSelectionPanelProps {
  ac: FleetMember;
}

export const FleetSelectionPanel: React.FC<FleetSelectionPanelProps> = React.memo(({ ac }) => {
  const { setView } = useUiStore();
  const { selectedTail } = useAircraftStore();
  const telemetry = useMissionStore((s) => s.telemetry);
  const { historyBuffer } = useTelemetryStore();

  const isCurrentActive = ac.tail === selectedTail;

  const egtHistory = useMemo(() => {
    if (!isCurrentActive) return [680, 682, 681, 683, 680];
    return historyBuffer.slice(-20).map((p) => Math.round(p.sensors.egtKelvin - 273.15));
  }, [isCurrentActive, historyBuffer]);

  const vibHistory = useMemo(() => {
    if (!isCurrentActive) return [0.42, 0.44, 0.43, 0.45, 0.44];
    return historyBuffer.slice(-20).map((p) => Number(p.sensors.vibrationG.toFixed(2)));
  }, [isCurrentActive, historyBuffer]);

  const specs = [
    { label: 'Airframe Serial', value: `HAL-LCA-${ac.tail}`, unit: '' },
    { label: 'Propulsion Unit', value: 'GE F404-IN20', unit: '#88219' },
    { label: 'Current Location', value: ac.location, unit: '' },
    { label: 'Assigned Squadron', value: ac.squadron, unit: '' },
    { label: 'Fuel Load Weight', value: `${ac.fuelKg} kg`, unit: `(${ac.fuelPct}%)`, status: ac.fuelPct > 30 ? 'NOMINAL' : 'WARNING' },
    { label: 'Total Flight Hours', value: ac.sortieHours, unit: 'Hrs', status: 'NOMINAL' },
    { label: 'Time To Overhaul', value: ac.tboRulHrs, unit: 'Hrs', status: ac.tboRulHrs > 300 ? 'NOMINAL' : 'WARNING' },
    { label: 'Active Warning', value: ac.warning ? 'YES' : 'NONE', unit: '', status: ac.warning ? 'CRITICAL' : 'NOMINAL' },
  ];

  return (
    <Panel
      title={`Selected Aircraft: ${ac.tail} Command Center`}
      icon={Shield}
      className="h-full"
      highContrastHeader
      right={
        <button
          onClick={() => setView('overview')}
          className="text-xs font-bold font-rajdhani uppercase tracking-wider text-[#2563EB] hover:underline flex items-center gap-1"
        >
          <span>Launch Workstation</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      }
    >
      <div className="space-y-3 font-mono text-xs">
        <div className="p-2.5 bg-[#EAF1FE] text-slate-900 rounded-sm border border-blue-200 shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-[10px] font-bold text-[#2563EB] uppercase tracking-widest flex items-center gap-1.5">
              <span>AIRCRAFT COMMAND PROTOCOL</span>
              {isCurrentActive && <span className="bg-emerald-600 text-white px-1 py-0.5 rounded-xs text-[8px] animate-pulse">LIVE LINK</span>}
            </div>
            <div className="text-base font-bold font-rajdhani text-slate-900 uppercase tracking-wider mt-0.5">
              {ac.tail} • {ac.pilot}
            </div>
            <div className="text-[10px] text-blue-800 font-medium mt-0.5">STATUS: {ac.status} • BASE: {ac.base}</div>
          </div>
          <button
            onClick={() => setView('overview')}
            className="px-3 py-1.5 bg-[#2563EB] hover:bg-[#1D4ED8] text-white rounded-xs font-rajdhani font-bold text-xs uppercase tracking-wider shadow-md transition-colors"
          >
            Launch Workstation →
          </button>
        </div>

        <div className="grid grid-cols-2 gap-2">
          {specs.map((s, i) => (
            <ValueBadge key={i} label={s.label} value={s.value} unit={s.unit} status={s.status} />
          ))}
        </div>

        {/* Live Telemetry Triage Strip for Selected Aircraft */}
        <div className="p-2.5 bg-slate-900 text-slate-200 rounded-sm border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-sky-400 text-[10px] font-bold border-b border-slate-800 pb-1">
            <span className="flex items-center gap-1"><Activity className="w-3 h-3 text-emerald-400" /> LIVE PROPULSION TELEMETRY ({ac.tail})</span>
            <span className="text-slate-500">1Hz ARINC-429</span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-[9px] text-slate-400 font-bold">EXHAUST EGT</div>
                <div className="font-bold text-white mt-0.5">
                  {isCurrentActive ? Math.round(telemetry.egtKelvin - 273.15) : 680} °C
                </div>
              </div>
              <MiniSparkline data={egtHistory} width={60} height={20} thresholdWarn={850} thresholdCrit={950} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-[9px] text-slate-400 font-bold">CORE VIB</div>
                <div className="font-bold text-white mt-0.5">
                  {isCurrentActive ? telemetry.vibrationG.toFixed(2) : '0.44'} G
                </div>
              </div>
              <MiniSparkline data={vibHistory} width={60} height={20} thresholdWarn={1.6} thresholdCrit={2.0} />
            </div>
          </div>
          <div className="text-[9px] text-slate-500 flex items-center justify-between pt-1 border-t border-slate-800/80">
            <span>POLL RATE: <span className="text-white font-bold">100 ms</span></span>
            <span className="flex items-center gap-1 text-emerald-400"><Zap className="w-2.5 h-2.5" /> TRANSDUCERS HEALTHY</span>
          </div>
        </div>
      </div>
    </Panel>
  );
});
FleetSelectionPanel.displayName = 'FleetSelectionPanel';
