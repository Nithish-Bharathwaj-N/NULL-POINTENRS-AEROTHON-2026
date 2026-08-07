import React from 'react';
import { Panel } from '@/components';
import { Settings, Globe, Monitor, Zap, PlayCircle } from 'lucide-react';
import { useUiStore } from '@/stores';
import { useMissionStore } from '@/stores/useMissionStore';

export const SettingsView: React.FC = React.memo(() => {
  const { hudUnits, toggleHudUnits, timeRangeSec, setTimeRangeSec } = useUiStore();
  const { activeScenario, triggerScenario } = useMissionStore();

  const scenarios = [
    {
      id: 'NORMAL_PATROL',
      title: '1. Normal Combat Patrol',
      desc: 'Mach 0.88 • Alt 28,450 Ft • Nominal thermal & mechanical stresses across all 8 engine stages.',
      phase: 'COMBAT PATROL (MACH 0.88)',
      overrides: { flightEnvelope: { mach: 0.88, altitudeFt: 28450, tasKts: 512, throttlePct: 74.0, gLoad: 1.42, aoaDeg: 4.8, fuelFlowKgH: 2450.0, isentropicEffPct: 92.4 } },
    },
    {
      id: 'SUPERSONIC_INTERCEPT',
      title: '2. Supersonic Intercept (Dash)',
      desc: 'Mach 1.45 • Alt 36,000 Ft • Afterburner engaged, high EGT (1350°C), rapid fuel burn rate.',
      phase: 'SUPERSONIC DASH (MACH 1.45)',
      overrides: { flightEnvelope: { mach: 1.45, altitudeFt: 36000, tasKts: 840, throttlePct: 100.0, gLoad: 2.10, aoaDeg: 3.2, fuelFlowKgH: 6800.0, isentropicEffPct: 88.5 } },
    },
    {
      id: 'COMBAT_MANEUVER',
      title: '3. High-G Air Combat Maneuver',
      desc: 'Mach 0.95 • 6.5G Defensive Turn • High AOA (18.4°), aerodynamic inlet distortion on Fan.',
      phase: 'HIGH-G COMBAT TURN (+6.5G)',
      overrides: { flightEnvelope: { mach: 0.95, altitudeFt: 18000, tasKts: 560, throttlePct: 92.0, gLoad: 6.50, aoaDeg: 18.4, fuelFlowKgH: 4200.0, isentropicEffPct: 86.0 } },
    },
    {
      id: 'BIRD_STRIKE',
      title: '4. Low Altitude Bird Strike',
      desc: 'Critical Fan vibration spike (2.85G), LPC spool degradation, automated AI triage work order.',
      phase: 'EMERGENCY: BIRD STRIKE INGESTION',
      overrides: { flightEnvelope: { mach: 0.42, altitudeFt: 2500, tasKts: 280, throttlePct: 65.0, gLoad: 1.10, aoaDeg: 6.5, fuelFlowKgH: 2100.0, isentropicEffPct: 74.2 } },
    },
    {
      id: 'FUEL_LEAK',
      title: '5. Rapid Fuel Tank Leakage',
      desc: 'Continuous 15kg/sec fuel loss from external drop tanks. Pre-warns pilot and mission control.',
      phase: 'ABORT: RAPID FUEL DEPLETION',
      overrides: { flightEnvelope: { mach: 0.75, altitudeFt: 22000, tasKts: 440, throttlePct: 70.0, gLoad: 1.00, aoaDeg: 4.0, fuelFlowKgH: 3100.0, isentropicEffPct: 91.0 } },
    },
    {
      id: 'COMPRESSOR_SURGE',
      title: '6. HPC Compressor Surge & Stall',
      desc: 'Severe P3 discharge pressure oscillations, high acoustic noise, stall warning in telemetry.',
      phase: 'CRITICAL: COMPRESSOR STALL / SURGE',
      overrides: { flightEnvelope: { mach: 0.82, altitudeFt: 31000, tasKts: 490, throttlePct: 88.0, gLoad: 1.25, aoaDeg: 9.5, fuelFlowKgH: 3800.0, isentropicEffPct: 78.0 } },
    },
    {
      id: 'COMBUSTOR_FAILURE',
      title: '7. Combustor Thermal Over-Temp',
      desc: 'T4 Peak exceeds 1950°C. Gas path thermal stress degrades Weibull RUL below 300 hrs.',
      phase: 'WARNING: THERMAL OVER-TEMPERATURE',
      overrides: { flightEnvelope: { mach: 0.90, altitudeFt: 29000, tasKts: 520, throttlePct: 95.0, gLoad: 1.50, aoaDeg: 5.2, fuelFlowKgH: 4600.0, isentropicEffPct: 84.5 } },
    },
    {
      id: 'OIL_PRESSURE_LOSS',
      title: '8. Bearing Oil Pressure Loss',
      desc: 'Hydro-Transducer pressure drops to critical 24.5 PSI. Bearing seizure risk imminent.',
      phase: 'CRITICAL: LUBE OIL PRESSURE LOSS',
      overrides: { flightEnvelope: { mach: 0.65, altitudeFt: 15000, tasKts: 380, throttlePct: 60.0, gLoad: 1.05, aoaDeg: 4.2, fuelFlowKgH: 1800.0, isentropicEffPct: 89.0 } },
    },
    {
      id: 'SENSOR_FAILURE',
      title: '9. ARINC-429 Bus Parity Error',
      desc: 'Simulated avionics communication glitch on Channel 2 (T4 Transducer). Requires diagnostics.',
      phase: 'AVIONICS FAULT: ARINC-429 BUS ERROR',
      overrides: { flightEnvelope: { mach: 0.88, altitudeFt: 28450, tasKts: 512, throttlePct: 74.0, gLoad: 1.42, aoaDeg: 4.8, fuelFlowKgH: 2450.0, isentropicEffPct: 92.4 } },
    },
    {
      id: 'EMERGENCY_LANDING',
      title: '10. Emergency Return & Landing',
      desc: 'Throttle idle (28%), landing gear down, descending altitude to base runway approach.',
      phase: 'EMERGENCY APPROACH & LANDING',
      overrides: { flightEnvelope: { mach: 0.28, altitudeFt: 1200, tasKts: 165, throttlePct: 28.0, gLoad: 1.00, aoaDeg: 11.0, fuelFlowKgH: 950.0, isentropicEffPct: 90.0 } },
    },
  ];

  return (
    <div className="p-3 h-full overflow-y-auto space-y-3 bg-[#0B132B]">
      {/* TIER 1: LIVE DEMONSTRATION SCENARIOS */}
      <Panel title="Aerothon Live Demonstration & Scenario Trigger Center (10 Operational Intelligence Scenarios)" icon={Zap} highContrastHeader>
        <div className="space-y-3 font-mono text-xs">
          <p className="text-slate-300 bg-slate-950/90 p-2.5 rounded-sm border border-slate-800">
            Select any 1-click operational scenario below to inject live telemetric disturbances, acoustic vibrations, thermal over-temperatures, and aerodynamic stalls into the engine simulation. All workstations, CAD schematic colors, and AI Weibull RUL predictions will synchronize instantaneously.
          </p>

          <div className="grid grid-cols-2 gap-3">
            {scenarios.map((scen) => {
              const isCurrent = activeScenario === scen.id;
              return (
                <div
                  key={scen.id}
                  onClick={() => triggerScenario(scen.id, { missionPhase: scen.phase, ...scen.overrides })}
                  className={`p-3 rounded-sm border transition-all cursor-pointer shadow-sm flex items-start justify-between gap-3 group ${
                    isCurrent
                      ? 'bg-sky-950 text-white border-sky-400 shadow-md ring-2 ring-sky-400/40'
                      : 'bg-slate-950/80 border-slate-800 hover:border-sky-500 hover:bg-slate-900 text-white'
                  }`}
                >
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2">
                      <PlayCircle className={`w-4 h-4 shrink-0 ${isCurrent ? 'text-sky-400 animate-pulse' : 'text-sky-400'}`} />
                      <span className="font-bold font-rajdhani text-sm uppercase tracking-wider">{scen.title}</span>
                    </div>
                    <p className={`text-[11px] leading-relaxed ${isCurrent ? 'text-slate-200' : 'text-slate-400'}`}>
                      {scen.desc}
                    </p>
                  </div>
                  <span className={`px-2 py-0.5 rounded-xs font-bold text-[10px] uppercase tracking-wider shrink-0 mt-1 ${
                    isCurrent ? 'bg-sky-600 text-white' : 'bg-slate-800 text-slate-300 border border-slate-700 group-hover:bg-sky-900 group-hover:text-white'
                  }`}>
                    {isCurrent ? 'ACTIVE SCENARIO' : 'TRIGGER LIVE'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </Panel>

      {/* TIER 2: HUD WORKSTATION CONFIGURATION */}
      <Panel title="HUD Workstation Display & Telemetry Refresh Configuration" icon={Settings}>
        <div className="space-y-4 font-mono text-xs">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-sm space-y-3">
              <div className="flex items-center gap-2 text-sky-400 font-bold font-rajdhani text-sm uppercase">
                <Globe className="w-4 h-4" />
                <span>ENGINEERING HUD UNITS SYSTEM</span>
              </div>
              <p className="text-slate-400 text-xs">
                Switch between Metric (IS) standard used by HAL / Dassault and Imperial (US) standard used by GE Aerospace.
              </p>
              <div className="flex items-center justify-between p-2 bg-slate-900 border border-slate-800 rounded-sm">
                <span className="font-bold text-white">ACTIVE SYSTEM:</span>
                <button
                  onClick={toggleHudUnits}
                  className="px-4 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xs font-bold uppercase text-xs cursor-pointer"
                >
                  {hudUnits === 'metric' ? 'METRIC (Bar / °C / kN)' : 'IMPERIAL (PSI / °F / lbf)'}
                </button>
              </div>
            </div>

            <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-sm space-y-3">
              <div className="flex items-center gap-2 text-sky-400 font-bold font-rajdhani text-sm uppercase">
                <Monitor className="w-4 h-4" />
                <span>TELEMETRY STREAM BUFFER WINDOW</span>
              </div>
              <p className="text-slate-400 text-xs">
                Select the default rolling ring-buffer time range for ARINC-429 live transducer chart rendering.
              </p>
              <div className="flex items-center justify-between p-2 bg-slate-900 border border-slate-800 rounded-sm">
                <span className="font-bold text-white">BUFFER RANGE:</span>
                <select
                  value={timeRangeSec}
                  onChange={(e) => setTimeRangeSec(Number(e.target.value))}
                  className="p-1 bg-slate-950 border border-slate-800 rounded-xs font-bold text-white cursor-pointer"
                >
                  <option value={600}>10 Minutes (High Freq)</option>
                  <option value={3600}>1 Hour (Standard Sortie)</option>
                  <option value={14400}>4 Hours (CAP Patrol)</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </Panel>
    </div>
  );
});
SettingsView.displayName = 'SettingsView';
