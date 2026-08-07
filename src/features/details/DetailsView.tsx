import React, { useMemo } from 'react';
import { Panel, ValueBadge, StatusBadge, MiniSparkline } from '@/components';
import { FileText, Download, Activity, ShieldCheck, Wrench } from 'lucide-react';
import { useAircraftStore, useMissionStore, useTelemetryStore } from '@/stores';

export const DetailsView: React.FC = React.memo(() => {
  const { selectedAircraft } = useAircraftStore();
  const ac = selectedAircraft;
  const telemetry = useMissionStore((s) => s.telemetry);
  const { historyBuffer } = useTelemetryStore();

  const records = [
    { label: 'Airframe Serial Number', val: `HAL-LCA-${ac.tail}`, status: 'NOMINAL' },
    { label: 'Propulsion Unit Serial', val: 'GE-F404-IN20 #88219', status: 'NOMINAL' },
    { label: 'Total Sorties Completed', val: '142 Combat & Test Sorties', status: 'NOMINAL' },
    { label: 'Airframe Fatigue Cycles', val: `${Math.round(ac.sortieHours * 1.8)} LCF Cycles`, status: 'NOMINAL' },
    { label: 'Next Scheduled Inspection', val: 'Borescope Stage 1-2 (in 210 Hrs)', status: 'WARNING' },
    { label: 'Airworthiness Certificate', val: 'VALID — HAL QA CERT #2026-99', status: 'NOMINAL' },
  ];

  // Live component aging metrics
  const modules = useMemo(() => {
    const vibHist = historyBuffer.slice(-20).map((p) => Number(p.sensors.vibrationG.toFixed(2)));
    const t4Hist = historyBuffer.slice(-20).map((p) => Math.round(p.sensors.t4Kelvin - 273.15));
    const p3Hist = historyBuffer.slice(-20).map((p) => Number(p.sensors.p3Bar.toFixed(1)));

    return [
      { name: 'Low Pressure Fan Module', ref: 'TJ04-LP', expended: 34, stress: '640 MPa (Nominal)', history: vibHist, warn: 1.6, crit: 2.0 },
      { name: 'High Pressure Core Compressor', ref: 'TJ04-HP', expended: 62, stress: `${telemetry.p3Bar.toFixed(1)} Bar (Static)`, history: p3Hist, warn: 27, crit: 30 },
      { name: 'Annular Combustor Sector #4', ref: 'TJ04-CB', expended: 78, stress: `${Math.round(telemetry.t4Kelvin - 273.15)} °C (Peak)`, history: t4Hist, warn: 1400, crit: 1500 },
      { name: 'HPT Stage 1 Cooled Rotor', ref: 'TJ04-HP-R1', expended: 54, stress: '480 MPa / 920 °C', history: t4Hist, warn: 1400, crit: 1500 },
      { name: 'Exhaust Afterburner Sector', ref: 'TJ04-AB', expended: 28, stress: '210 kPa (Max Thrust)', history: vibHist, warn: 1.6, crit: 2.0 },
    ];
  }, [telemetry, historyBuffer]);

  return (
    <div className="p-3 h-full overflow-y-auto space-y-3 bg-[#0B132B]">
      <Panel
        title={`Aircraft Logbook & Airworthiness Record: ${ac.tail}`}
        icon={FileText}
        right={
          <button
            onClick={() => alert(`Downloading Logbook Report for ${ac.tail}...`)}
            className="flex items-center gap-1.5 px-3 py-1 bg-[#003366] text-white hover:bg-[#002244] rounded-xs font-rajdhani font-bold text-xs uppercase tracking-wider transition-colors shadow-xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Digital Logbook</span>
          </button>
        }
      >
        <div className="space-y-4 font-mono text-xs">
          <div className="p-3 bg-slate-900 text-white rounded-sm border border-slate-800 flex items-center justify-between">
            <div>
              <div className="text-[10px] text-sky-400 font-bold uppercase flex items-center gap-2">
                <span>OFFICIAL IAF / HAL FLIGHT RECORD</span>
                <span className="bg-emerald-950 text-emerald-400 border border-emerald-700 px-1.5 py-0.5 rounded-xs text-[9px]">
                  ● AIRWORTHINESS VALIDATED
                </span>
              </div>
              <div className="text-lg font-bold font-rajdhani text-white uppercase tracking-wider mt-0.5">
                {ac.tail} • {ac.squadron} • {ac.base}
              </div>
              <div className="text-[10px] text-slate-300 mt-0.5">
                PRIMARY PILOT: {ac.pilot} • PROPULSION TEAM: {ac.crew}
              </div>
            </div>
            <div className="text-right flex flex-col items-end gap-1">
              <StatusBadge status={ac.status} size="md" />
              <div className="text-[10px] text-slate-400 font-mono">POLL RATE: 100ms • ARINC CH-1</div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {records.map((r, i) => (
              <ValueBadge key={i} label={r.label} value={r.val} status={r.status} />
            ))}
          </div>

          {/* Component Aging & Airworthiness Life-Cycle Matrix */}
          <div className="space-y-2 bg-slate-950/80 border border-slate-800 rounded-sm p-3 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
              <div className="font-bold text-sky-400 text-xs uppercase flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-sky-400" />
                <span>PROPULSION MODULE AGING & TBO LIFE EXPENDITURE</span>
              </div>
              <span className="text-[10px] text-slate-400 font-bold">MIL-STD-1530C Airworthiness Standard</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-800 uppercase text-[9px] font-bold text-sky-400 border-b border-slate-700">
                    <th className="p-2">Module Name & Ref</th>
                    <th className="p-2">TBO Life Expended</th>
                    <th className="p-2">Live Operating Stress</th>
                    <th className="p-2 text-center">30s Stress Waveform</th>
                    <th className="p-2 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {modules.map((mod, idx) => {
                    const isHigh = mod.expended > 75;
                    const isMed = mod.expended > 55;
                    return (
                      <tr key={idx} className="hover:bg-slate-800/80 transition-colors">
                        <td className="p-2 font-bold text-white">
                          <div>{mod.name}</div>
                          <div className="text-[10px] font-normal text-slate-400 uppercase">{mod.ref}</div>
                        </td>
                        <td className="p-2 w-48">
                          <div className="flex items-center justify-between text-[10px] mb-0.5">
                            <span className="font-bold text-slate-200">{mod.expended}% Expended</span>
                            <span className="text-slate-400">{100 - mod.expended}% Remain</span>
                          </div>
                          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-300 ${isHigh ? 'bg-red-500' : isMed ? 'bg-amber-500' : 'bg-emerald-500'}`}
                              style={{ width: `${mod.expended}%` }}
                            />
                          </div>
                        </td>
                        <td className="p-2 font-mono font-bold text-white">{mod.stress}</td>
                        <td className="p-2 text-center">
                          <MiniSparkline data={mod.history} width={80} height={20} thresholdWarn={mod.warn} thresholdCrit={mod.crit} />
                        </td>
                        <td className="p-2 text-center">
                          <StatusBadge status={isHigh ? 'WARNING' : 'NOMINAL'} size="sm" />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-sm space-y-2">
            <div className="font-bold text-sky-400 text-xs uppercase border-b border-slate-800 pb-1 flex items-center justify-between">
              <span>RECENT MAINTENANCE & ENGINEERING REMARKS</span>
              <span className="flex items-center gap-1 text-emerald-400 text-[10px]"><ShieldCheck className="w-3 h-3" /> QA SIGN-OFF COMPLETE</span>
            </div>
            <div className="space-y-1.5 text-slate-300 text-[11px]">
              <div className="flex justify-between border-b border-slate-800 pb-1">
                <span className="flex items-center gap-1.5">
                  <Wrench className="w-3 h-3 text-slate-400" />
                  <span>[2026-07-20] Routine N1/N2 vibration calibration performed at Jodhpur Bay 2.</span>
                </span>
                <span className="font-bold text-slate-400">SIGN-OFF: HAL-ENG-LEAD</span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-1">
                <span className="flex items-center gap-1.5">
                  <Wrench className="w-3 h-3 text-slate-400" />
                  <span>[2026-07-15] Replaced thermocouple harness on combustor sector 4.</span>
                </span>
                <span className="font-bold text-slate-400">SIGN-OFF: IAF-PROP-1</span>
              </div>
              <div className="flex justify-between">
                <span className="flex items-center gap-1.5">
                  <Wrench className="w-3 h-3 text-slate-400" />
                  <span>[2026-07-02] Supersonic envelope validation sortie (Mach 1.24) completed nominally.</span>
                </span>
                <span className="font-bold text-slate-400">SIGN-OFF: FTC-QA</span>
              </div>
            </div>
          </div>
        </div>
      </Panel>
    </div>
  );
});
DetailsView.displayName = 'DetailsView';
