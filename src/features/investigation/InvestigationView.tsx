import React, { useMemo } from 'react';
import { Panel, StatusBadge, MiniSparkline } from '@/components';
import { GitPullRequest, AlertTriangle, ShieldCheck, ArrowRight, Activity, Cpu, Wrench } from 'lucide-react';
import { useMissionStore, useTelemetryStore, useUiStore } from '@/stores';

export const InvestigationView: React.FC = React.memo(() => {
  const alerts = useMissionStore((s) => s.alerts);
  const telemetry = useMissionStore((s) => s.telemetry);
  const stages = useMissionStore((s) => s.subsystemStages);
  const { historyBuffer } = useTelemetryStore();
  const { setSelectedStageRef, setView } = useUiStore();

  const isCrit = alerts.some((a) => a.severity === 'CRITICAL') || telemetry.t4Kelvin > 1750;
  const isWarn = !isCrit && (alerts.length > 0 || telemetry.egtKelvin > 1150);

  const t4History = useMemo(() => historyBuffer.slice(-30).map((p) => Math.round(p.sensors.t4Kelvin - 273.15)), [historyBuffer]);
  const p3History = useMemo(() => historyBuffer.slice(-30).map((p) => Number(p.sensors.p3Bar.toFixed(1))), [historyBuffer]);
  const vibHistory = useMemo(() => historyBuffer.slice(-30).map((p) => Number(p.sensors.vibrationG.toFixed(2))), [historyBuffer]);

  return (
    <div className="p-3 h-full overflow-y-auto space-y-3 bg-[#0B132B]">
      {/* Top Root Cause Triage Header */}
      <div className="grid grid-cols-4 gap-3 font-mono text-xs">
        <div className={`p-3 rounded-sm border shadow-sm flex items-center justify-between ${
          isCrit ? 'bg-red-950/80 border-red-800' : isWarn ? 'bg-amber-950/80 border-amber-800' : 'bg-slate-900/90 border-slate-800'
        }`}>
          <div>
            <div className="text-[10px] text-slate-400 font-bold uppercase">TRIAGE INVESTIGATION STATUS</div>
            <div className={`text-lg font-bold mt-0.5 ${isCrit ? 'text-red-400 animate-pulse' : isWarn ? 'text-amber-400' : 'text-emerald-400'}`}>
              {isCrit ? 'ACTIVE SURGE CASCADE' : isWarn ? 'THERMAL MARGIN WARNING' : 'ALL SYSTEMS NOMINAL'}
            </div>
            <div className="text-[9px] text-slate-400 mt-0.5">Primary Question: What caused the anomaly?</div>
          </div>
          {isCrit ? <AlertTriangle className="w-8 h-8 text-red-500/30 animate-pulse" /> : <ShieldCheck className="w-8 h-8 text-emerald-500/30" />}
        </div>

        <div className="p-3 bg-slate-900/90 border border-slate-800 rounded-sm shadow-sm flex items-center justify-between">
          <div>
            <div className="text-[10px] text-slate-400 font-bold uppercase">PROPAGATION VELOCITY</div>
            <div className="text-lg font-bold text-white mt-0.5">3.4 m/s Gas Vector</div>
            <div className="text-[9px] text-amber-400 font-bold mt-0.5">● STATION 4 → STATION 5 CASCADE</div>
          </div>
          <Activity className="w-8 h-8 text-amber-400/30" />
        </div>

        <div className="p-3 bg-slate-900/90 border border-slate-800 rounded-sm shadow-sm flex items-center justify-between">
          <div>
            <div className="text-[10px] text-slate-400 font-bold uppercase">AFFECTED SUBSYSTEMS</div>
            <div className="text-lg font-bold text-sky-300 mt-0.5">
              {stages.filter((s) => s.status !== 'NOMINAL').length} / {stages.length} DEGRADED
            </div>
            <div className="text-[9px] text-slate-400 mt-0.5">Combustor, HPT & Core Spool</div>
          </div>
          <Cpu className="w-8 h-8 text-sky-400/30" />
        </div>

        <div className="p-3 bg-slate-900/90 border border-slate-800 rounded-sm shadow-sm flex items-center justify-between">
          <div>
            <div className="text-[10px] text-slate-400 font-bold uppercase">CAUSAL MITIGATION CONFIDENCE</div>
            <div className="text-lg font-bold text-emerald-400 mt-0.5">98.2% ACCURACY</div>
            <div className="text-[9px] text-slate-400 mt-0.5">Physics-Informed Root Cause Model</div>
          </div>
          <Wrench className="w-8 h-8 text-emerald-400/30" />
        </div>
      </div>

      <div className="grid grid-cols-12 gap-3">
        {/* Left 8 Cols: Causal Fault Propagation Tree */}
        <div className="col-span-8 space-y-3">
          <Panel title="Causal Fault Propagation Tree & Anomaly Cascade Pathway" icon={GitPullRequest} highContrastHeader={isCrit}>
            <div className="space-y-4 font-mono text-xs p-2">
              <div className="p-2.5 bg-slate-950 text-slate-300 rounded-sm border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-sky-400 font-bold">AUTOMATED RCA TRIAGE SUMMARY:</span>
                  <span className="text-white ml-2">
                    {isCrit 
                      ? 'Combustor fuel injector overpressure triggered thermal runaway, cascading into HPT blade stress and compressor surge.'
                      : 'Thermodynamic residuals within design limits. Continuous multi-channel correlation active.'}
                  </span>
                </div>
                <span className="text-[10px] bg-sky-950 text-sky-300 border border-sky-700 px-2 py-0.5 rounded-xs shrink-0 font-bold">
                  AERONET-v4 RCA
                </span>
              </div>

              {/* Graphical Propagation Chain */}
              <div className="relative space-y-4 pl-4 border-l-2 border-dashed border-slate-700">
                {/* Level 1: Root Cause */}
                <div 
                  onClick={() => { setSelectedStageRef('TJ04-CB'); setView('twin'); }}
                  className={`p-3 rounded-sm border shadow-sm cursor-pointer transition-all hover:scale-[1.01] ${
                    isCrit ? 'bg-red-950/80 border-red-800 ring-2 ring-red-700' : 'bg-slate-950/80 border-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between border-b border-slate-800 pb-1.5 mb-2">
                    <div className="flex items-center gap-2">
                      <span className="bg-red-600 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-xs uppercase tracking-wider animate-pulse">
                        LEVEL 1: ROOT CAUSE ORIGIN
                      </span>
                      <span className="font-bold text-white text-sm">COMBUSTOR THERMAL RUNAWAY (TJ04-CB)</span>
                    </div>
                    <StatusBadge status={isCrit ? 'CRITICAL' : 'NOMINAL'} size="sm" />
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-xs items-center">
                    <div>
                      <div className="text-[10px] text-slate-400 font-bold">TRANSGRESSION PARAMETER</div>
                      <div className="font-bold text-red-400 mt-0.5">T4 INLET &gt; 1,500 °C ({Math.round(telemetry.t4Kelvin - 273.15)} °C NOW)</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-400 font-bold">30S TELEMETRY WAVEFORM</div>
                      <MiniSparkline data={t4History} width={120} height={22} thresholdWarn={1400} thresholdCrit={1500} />
                    </div>
                    <div className="text-right">
                      <button className="px-2 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded-xs text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 ml-auto shadow-xs cursor-pointer">
                        <span>Inspect in 3D Twin</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Level 2: Direct Propagation */}
                <div 
                  onClick={() => { setSelectedStageRef('TJ04-HP'); setView('twin'); }}
                  className={`p-3 rounded-sm border shadow-sm cursor-pointer transition-all hover:scale-[1.01] ${
                    isCrit || isWarn ? 'bg-amber-950/80 border-amber-800' : 'bg-slate-950/80 border-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between border-b border-slate-800 pb-1.5 mb-2">
                    <div className="flex items-center gap-2">
                      <span className="bg-amber-500 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-xs uppercase tracking-wider">
                        LEVEL 2: DIRECT CASCADE PROPAGATION
                      </span>
                      <span className="font-bold text-white text-sm">HPT TURBINE THERMAL FATIGUE (TJ04-HP)</span>
                    </div>
                    <StatusBadge status={isCrit ? 'WARNING' : 'NOMINAL'} size="sm" />
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-xs items-center">
                    <div>
                      <div className="text-[10px] text-slate-400 font-bold">SECONDARY SURGE EFFECT</div>
                      <div className="font-bold text-amber-400 mt-0.5">P3 BACKPRESS SURGE ({telemetry.p3Bar.toFixed(1)} BAR NOW)</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-400 font-bold">30S PRESSURE WAVEFORM</div>
                      <MiniSparkline data={p3History} width={120} height={22} thresholdWarn={27} thresholdCrit={30} />
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-slate-400 font-bold">AERODYNAMIC stall margin &lt; 4%</span>
                    </div>
                  </div>
                </div>

                {/* Level 3: Structural Vibrational Response */}
                <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-sm shadow-sm space-y-2">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="bg-slate-700 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-xs uppercase tracking-wider">
                        LEVEL 3: STRUCTURAL EXCITATION
                      </span>
                      <span className="font-bold text-white text-sm">CORE ROTOR SPOOL VIBRATION (N2 SHAFT)</span>
                    </div>
                    <StatusBadge status={telemetry.vibrationG > 1.8 ? 'CRITICAL' : telemetry.vibrationG > 1.6 ? 'WARNING' : 'NOMINAL'} size="sm" />
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-xs items-center">
                    <div>
                      <div className="text-[10px] text-slate-400 font-bold">HARMONIC VIBRATION PEAK</div>
                      <div className="font-bold text-white mt-0.5">{telemetry.vibrationG.toFixed(2)} G (ARINC CH-05)</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-400 font-bold">30S VIBRATION WAVEFORM</div>
                      <MiniSparkline data={vibHistory} width={120} height={22} thresholdWarn={1.6} thresholdCrit={2.0} />
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-red-400 font-bold">AI Weibull RUL Drop Triggered</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Panel>
        </div>

        {/* Right 4 Cols: Thermal Correlation Matrix & Mitigation Orders */}
        <div className="col-span-4 space-y-3">
          <Panel title="Cross-Stage Thermal Correlation" icon={Activity}>
            <div className="space-y-2 font-mono text-xs">
              <div className="text-[10px] text-slate-400 font-bold uppercase mb-1">
                PEARSON CORRELATION MATRIX (r-value)
              </div>
              <div className="grid grid-cols-4 gap-1 text-center font-bold text-[10px]">
                <div className="p-1.5 bg-slate-800 rounded-xs text-sky-400">STAGE</div>
                <div className="p-1.5 bg-slate-800 rounded-xs text-sky-400">CB</div>
                <div className="p-1.5 bg-slate-800 rounded-xs text-sky-400">HP</div>
                <div className="p-1.5 bg-slate-800 rounded-xs text-sky-400">LP</div>

                <div className="p-1.5 bg-slate-800 font-bold text-left text-sky-400">CB</div>
                <div className="p-1.5 bg-sky-950 border border-sky-800 text-white">1.00</div>
                <div className="p-1.5 bg-red-600 text-white animate-pulse">0.94</div>
                <div className="p-1.5 bg-amber-500 text-white">0.72</div>

                <div className="p-1.5 bg-slate-800 font-bold text-left text-sky-400">HP</div>
                <div className="p-1.5 bg-red-600 text-white">0.94</div>
                <div className="p-1.5 bg-sky-950 border border-sky-800 text-white">1.00</div>
                <div className="p-1.5 bg-amber-500 text-white">0.81</div>

                <div className="p-1.5 bg-slate-800 font-bold text-left text-sky-400">LP</div>
                <div className="p-1.5 bg-amber-500 text-white">0.72</div>
                <div className="p-1.5 bg-amber-500 text-white">0.81</div>
                <div className="p-1.5 bg-sky-950 border border-sky-800 text-white">1.00</div>
              </div>
              <p className="text-[10px] text-slate-400 mt-2 leading-normal">
                High correlation (r = 0.94) between Combustor (CB) and High Pressure Turbine (HP) confirms direct convective thermal transport across Station 4.
              </p>
            </div>
          </Panel>

          <Panel title="Mitigation Work Order Queue" icon={Wrench}>
            <div className="space-y-2 font-mono text-xs">
              {[
                { wo: 'WO-88219-A1', task: 'Inspect Combustor Fuel Nozzle #4 for overpressure spray distortion', pri: 'CRITICAL', est: '2.5h' },
                { wo: 'WO-88219-A2', task: 'Borescope inspection of HPT Stage 1 rotor blade tips', pri: 'HIGH', est: '4.0h' },
                { wo: 'WO-88219-A3', task: 'Recalibrate ARINC-429 P3 static pressure transducer zero-offset', pri: 'MED', est: '1.0h' },
              ].map((item, i) => (
                <div key={i} className="p-2.5 bg-slate-950/80 border border-slate-800 rounded-sm shadow-sm space-y-1 hover:border-sky-500 transition-colors">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sky-300 text-xs">{item.wo}</span>
                    <span className={`px-1.5 py-0.5 rounded-xs text-[9px] font-bold uppercase ${
                      item.pri === 'CRITICAL' ? 'bg-red-600 text-white' : item.pri === 'HIGH' ? 'bg-amber-500 text-white' : 'bg-slate-800 text-slate-300'
                    }`}>
                      {item.pri}
                    </span>
                  </div>
                  <div className="text-white text-[11px] font-medium leading-tight">{item.task}</div>
                  <div className="flex justify-between items-center pt-1 border-t border-slate-800 text-[10px] text-slate-400">
                    <span>EST TIME: {item.est}</span>
                    <button onClick={() => setView('maintenance')} className="text-sky-400 font-bold uppercase hover:underline cursor-pointer">
                      Dispatch WO →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
});
InvestigationView.displayName = 'InvestigationView';
