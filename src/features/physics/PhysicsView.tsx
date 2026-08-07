import React, { useMemo } from 'react';
import { Panel } from '@/components';
import { Activity, Thermometer, Zap, Wind } from 'lucide-react';
import { useMissionStore } from '@/stores/useMissionStore';
import { useAnimatedValue } from '@/hooks/useAnimatedValue';

export const PhysicsView: React.FC = React.memo(() => {
  const tel = useMissionStore((s) => s.telemetry);
  const env = useMissionStore((s) => s.flightEnvelope);
  const stages = useMissionStore((s) => s.subsystemStages);

  const t3C = Math.round(tel.t3Kelvin - 273.15);
  const t4C = Math.round(tel.t4Kelvin - 273.15);
  const egtC = Math.round(tel.egtKelvin - 273.15);

  // Brayton cycle derived values
  const opr = useMemo(() => Number((tel.p3Bar / tel.p2Bar).toFixed(1)), [tel.p2Bar, tel.p3Bar]);
  const compressorWork = useMemo(() => Number(((t3C + 273.15) / (15 + 273.15)).toFixed(3)), [t3C]);
  const turbineExpRatio = useMemo(() => Number((tel.t4Kelvin / tel.egtKelvin).toFixed(3)), [tel.t4Kelvin, tel.egtKelvin]);
  const thermalEff = useMemo(() => Number((1 - (1 / Math.pow(opr, (1.4 - 1) / 1.4))) * 100).toFixed(1), [opr]);

  const animEgt = useAnimatedValue(egtC, 600);
  const animT4 = useAnimatedValue(t4C, 600);
  const animP3 = useAnimatedValue(tel.p3Bar, 600);
  const animOpr = useAnimatedValue(opr, 600);

  const stationData = [
    { label: 'Station 1: Intake', temp: Math.round((15 + 273.15 + ((env.mach ** 2) * 0.2 * 288)) - 273.15), pressure: Number((1.013 * Math.pow(1 + 0.2 * env.mach ** 2, 3.5)).toFixed(3)), note: 'Ram recovery' },
    { label: 'Station 2: Fan Exit', temp: Math.round(tel.t3Kelvin * 0.28 - 273.15), pressure: Number(tel.p2Bar.toFixed(3)), note: 'LP compression' },
    { label: 'Station 3: HPC Exit', temp: t3C, pressure: Number(tel.p3Bar.toFixed(2)), note: 'HP compression' },
    { label: 'Station 4: Combustor', temp: t4C, pressure: Number((tel.p3Bar * 0.96).toFixed(2)), note: 'Heat addition' },
    { label: 'Station 5: HPT Exit', temp: Math.round(tel.egtKelvin - 273.15 + 55), pressure: Number((tel.p3Bar * 0.42).toFixed(2)), note: 'HP expansion' },
    { label: 'Station 6: LPT Exit / EGT', temp: egtC, pressure: Number((tel.p2Bar * 1.05).toFixed(3)), note: 'LP expansion' },
    { label: 'Station 7: Nozzle', temp: egtC - 110, pressure: Number((tel.p2Bar * 0.58).toFixed(3)), note: 'Thrust generation' },
  ];

  return (
    <div className="p-3 h-full overflow-y-auto space-y-3 bg-[#0B132B]">
      {/* ── Brayton Cycle Summary ─────────────────────────────────────────────── */}
      <Panel title="GE F404-IN20 Brayton Cycle — Real-Time Thermodynamic Analysis" icon={Zap}>
        <div className="space-y-3 font-mono text-xs">
          <div className="grid grid-cols-4 gap-3">
            {[
              { label: 'Overall Pressure Ratio', val: `${animOpr.toFixed(1)} : 1`, sub: `P3: ${animP3.toFixed(1)} Bar | P2: ${tel.p2Bar.toFixed(2)} Bar`, warn: opr > 27, crit: opr > 29 },
              { label: 'T4 Turbine Inlet Temp', val: `${Math.round(animT4)}°C`, sub: `T3: ${t3C}°C | Limit: 1650°C`, warn: t4C > 1450, crit: t4C > 1600 },
              { label: 'Brayton Thermal Efficiency', val: `${thermalEff}%`, sub: `Isentropic Eff: ${env.isentropicEffPct.toFixed(1)}%`, warn: Number(thermalEff) < 30, crit: Number(thermalEff) < 25 },
              { label: 'EGT (Station 6)', val: `${Math.round(animEgt)}°C`, sub: `Kelvin: ${tel.egtKelvin.toFixed(0)} K | Limit: 1100°C`, warn: egtC > 900, crit: egtC > 1050 },
            ].map((m, i) => (
              <div key={i} className={`p-2.5 rounded-sm border shadow-sm ${m.crit ? 'bg-red-950/80 border-red-800' : m.warn ? 'bg-amber-950/80 border-amber-800' : 'bg-slate-950/80 border-slate-800'}`}>
                <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">{m.label}</div>
                <div className={`text-lg font-bold mt-0.5 font-mono ${m.crit ? 'text-red-400' : m.warn ? 'text-amber-400' : 'text-white'}`}>{m.val}</div>
                <div className="text-[9px] text-slate-400 mt-0.5">{m.sub}</div>
              </div>
            ))}
          </div>

          {/* Cycle efficiency indicators */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Compressor Temperature Ratio', val: compressorWork.toFixed(3), unit: 'T3/T1', desc: 'Total compression work' },
              { label: 'Turbine Expansion Ratio', val: turbineExpRatio.toFixed(3), unit: 'T4/EGT', desc: 'Turbine enthalpy drop' },
              { label: 'Specific Fuel Consumption', val: (env.fuelFlowKgH / Math.max(1, env.isentropicEffPct * 0.5)).toFixed(2), unit: 'kg/daN·h', desc: 'Thrust-specific fuel use' },
            ].map((m, i) => (
              <div key={i} className="p-2 bg-slate-950/80 border border-slate-800 rounded-sm shadow-sm">
                <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">{m.label}</div>
                <div className="text-sm font-bold text-white mt-0.5">{m.val} <span className="text-[10px] font-normal text-sky-400">{m.unit}</span></div>
                <div className="text-[9px] text-slate-400 mt-0.5">{m.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </Panel>

      {/* ── Station-by-Station T-S Table ─────────────────────────────────────── */}
      <Panel title="Gas Path Station Analysis — ARINC-429 Thermal & Pressure Matrix" icon={Thermometer} noPad>
        <div className="overflow-x-auto font-mono text-xs">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-800 text-sky-400 font-bold uppercase tracking-wider text-[10px] border-b border-slate-700">
                <th className="p-2">Station</th>
                <th className="p-2 text-right">Temperature (°C)</th>
                <th className="p-2 text-right">Pressure (Bar)</th>
                <th className="p-2 text-right">Temp Rise (ΔT)</th>
                <th className="p-2">Thermodynamic Process</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {stationData.map((st, i) => {
                const prevTemp = i > 0 ? stationData[i - 1].temp : st.temp;
                const delta = st.temp - prevTemp;
                const isHot = st.temp > 1000;
                const isCrit = st.temp > 1450;
                return (
                  <tr key={i} className={`transition-colors ${isCrit ? 'bg-red-950/70 hover:bg-red-900/90' : isHot ? 'bg-amber-950/70 hover:bg-amber-900/90' : 'hover:bg-slate-800/80'}`}>
                    <td className="p-2 font-bold text-sky-300">{st.label}</td>
                    <td className={`p-2 text-right font-bold ${isCrit ? 'text-red-400' : isHot ? 'text-amber-400' : 'text-white'}`}>{st.temp.toLocaleString()} °C</td>
                    <td className="p-2 text-right text-slate-300 font-medium">{st.pressure} Bar</td>
                    <td className={`p-2 text-right font-bold ${delta > 0 ? 'text-amber-400' : delta < 0 ? 'text-sky-400' : 'text-slate-400'}`}>
                      {i > 0 ? `${delta > 0 ? '+' : ''}${delta}°C` : '—'}
                    </td>
                    <td className="p-2 text-slate-400 text-[10px]">{st.note}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>

      {/* ── Engine Stage Efficiency Grid ─────────────────────────────────────── */}
      <Panel title="Subsystem Stage Operating Line & Health Index" icon={Activity}>
        <div className="grid grid-cols-4 gap-2 font-mono text-xs">
          {stages.map((stg) => {
            const healthColor = stg.health >= 90 ? 'text-emerald-300 bg-emerald-950 border-emerald-800'
              : stg.health >= 75 ? 'text-amber-300 bg-amber-950 border-amber-800'
              : 'text-red-300 bg-red-950 border-red-800';
            return (
              <div key={stg.ref} className="p-2 bg-slate-950/80 border border-slate-800 rounded-sm shadow-sm space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sky-300 text-[10px] uppercase">{stg.ref}</span>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-xs border ${healthColor}`}>{stg.health.toFixed(0)}%</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full transition-all duration-500 ${stg.health >= 90 ? 'bg-emerald-500' : stg.health >= 75 ? 'bg-amber-500' : 'bg-red-500'}`}
                    style={{ width: `${stg.health}%` }}
                  />
                </div>
                <div className="text-[9px] text-slate-400 space-y-0.5">
                  <div>T: <span className="font-bold text-white">{stg.temp}°C</span></div>
                  <div>P: <span className="font-bold text-white">{stg.pressure} Bar</span></div>
                  <div>V: <span className="font-bold text-white">{stg.vibration}G</span></div>
                </div>
                <div className={`text-[9px] font-bold uppercase tracking-wider ${stg.status === 'NOMINAL' ? 'text-emerald-400' : stg.status === 'WARNING' ? 'text-amber-400' : 'text-red-400'}`}>
                  {stg.status}
                </div>
              </div>
            );
          })}
        </div>
      </Panel>

      {/* ── Real-Time Operating Parameters ────────────────────────────────────── */}
      <Panel title="Real-Time Aerodynamic & Propulsion Operating Parameters" icon={Wind}>
        <div className="grid grid-cols-4 gap-2 font-mono text-xs">
          {[
            { l: 'Mach Number', v: env.mach.toFixed(3), u: 'M' },
            { l: 'Altitude MSL', v: Math.round(env.altitudeFt).toLocaleString(), u: 'Ft' },
            { l: 'True Airspeed', v: Math.round(env.tasKts).toString(), u: 'Kts' },
            { l: 'Throttle Lever (TLA)', v: env.throttlePct.toFixed(1), u: '%' },
            { l: 'Angle of Attack', v: env.aoaDeg.toFixed(1), u: '°' },
            { l: 'G-Load Factor', v: `${env.gLoad >= 0 ? '+' : ''}${env.gLoad.toFixed(2)}`, u: 'G' },
            { l: 'N1 Spool Speed', v: tel.n1Rpm.toLocaleString(), u: 'RPM' },
            { l: 'N2 Spool Speed', v: tel.n2Rpm.toLocaleString(), u: 'RPM' },
            { l: 'Vibration RMS', v: tel.vibrationG.toFixed(2), u: 'G' },
            { l: 'Oil Pressure', v: tel.oilPressurePsi.toFixed(1), u: 'PSI' },
            { l: 'Fuel Flow Rate', v: Math.round(env.fuelFlowKgH).toLocaleString(), u: 'kg/h' },
            { l: 'Isentropic Efficiency', v: env.isentropicEffPct.toFixed(1), u: '%' },
          ].map((m, i) => (
            <div key={i} className="p-2 bg-slate-950/80 border border-slate-800 rounded-sm shadow-sm">
              <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">{m.l}</div>
              <div className="text-sm font-bold text-white mt-0.5 font-mono">{m.v} <span className="text-[10px] font-normal text-sky-400">{m.u}</span></div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
});
PhysicsView.displayName = 'PhysicsView';
