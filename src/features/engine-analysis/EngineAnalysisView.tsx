import React, { useMemo } from 'react';
import { Panel, ValueBadge } from '@/components';
import { Cpu, Activity, Thermometer, Gauge } from 'lucide-react';
import { useMissionStore } from '@/stores/useMissionStore';
import { useUiStore } from '@/stores';
import { useAnimatedValue } from '@/hooks/useAnimatedValue';

export const EngineAnalysisView: React.FC = React.memo(() => {
  const tel = useMissionStore((s) => s.telemetry);
  const stages = useMissionStore((s) => s.subsystemStages);
  const { setSelectedStageRef } = useUiStore();

  const opr = useMemo(() => Number((tel.p3Bar / Math.max(0.1, tel.p2Bar)).toFixed(1)), [tel.p2Bar, tel.p3Bar]);
  const t4C = Math.round(tel.t4Kelvin - 273.15);
  const sfc = useMemo(() => Number((tel.fuelFlowKgH / Math.max(1, tel.n1Rpm * 0.0075)).toFixed(2)), [tel.fuelFlowKgH, tel.n1Rpm]);
  const thrust = useMemo(() => Number(((tel.n1Rpm / 15000) * 82.5).toFixed(1)), [tel.n1Rpm]);

  const animOpr = useAnimatedValue(opr, 400);
  const animT4 = useAnimatedValue(t4C, 400);
  const animSfc = useAnimatedValue(sfc, 400);
  const animThrust = useAnimatedValue(thrust, 400);

  return (
    <div className="p-3 h-full overflow-y-auto space-y-3 bg-[#0B132B]">
      {/* ── Propulsion Thermodynamics & Brayton Cycle Analysis ─────────────── */}
      <Panel title="Propulsion Thermodynamics & Live Brayton Cycle Analysis" icon={Cpu}>
        <div className="space-y-4 font-mono text-xs">
          <div className="p-3 bg-slate-900 text-white rounded-sm grid grid-cols-4 gap-4 shadow-sm">
            <ValueBadge 
              label="Overall Pressure Ratio" 
              value={`${animOpr.toFixed(1)} : 1`} 
              status={opr > 27 ? 'WARNING' : 'NOMINAL'} 
            />
            <ValueBadge 
              label="Turbine Inlet Temp (T4)" 
              value={`${Math.round(animT4)} °C`} 
              status={t4C > 1500 ? 'CRITICAL' : t4C > 1400 ? 'WARNING' : 'NOMINAL'} 
            />
            <ValueBadge 
              label="Specific Fuel Consumption" 
              value={`${animSfc.toFixed(2)} kg/(daN·h)`} 
              status="NOMINAL" 
            />
            <ValueBadge 
              label="Isentropic Thrust" 
              value={`${animThrust.toFixed(1)} kN`} 
              status={thrust < 30 ? 'WARNING' : 'NOMINAL'} 
            />
          </div>

          {/* ── Dynamic Stage Matrix ────────────────────────────────────────── */}
          <div className="grid grid-cols-2 gap-3">
            {stages.map((stg) => {
              const isCrit = stg.status === 'CRITICAL';
              const isWarn = stg.status === 'WARNING';
              return (
                <div 
                  key={stg.ref} 
                  onClick={() => setSelectedStageRef(stg.ref)}
                  className={`p-3 rounded-sm border shadow-sm space-y-2 cursor-pointer transition-all hover:shadow-md ${
                    isCrit 
                      ? 'bg-red-950/80 border-red-800 ring-1 ring-red-700' 
                      : isWarn 
                      ? 'bg-amber-950/80 border-amber-800' 
                      : 'bg-slate-950/80 border-slate-800 hover:border-sky-500'
                  }`}
                >
                  <div className="flex justify-between items-center border-b border-slate-800 pb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sky-300 text-sm uppercase">{stg.name}</span>
                      <span className="text-[10px] text-slate-400 uppercase">({stg.ref})</span>
                    </div>
                    <span className={`px-2 py-0.5 rounded-xs font-bold text-[10px] uppercase ${
                      isCrit ? 'bg-red-600 text-white animate-pulse' : isWarn ? 'bg-amber-500 text-white' : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    }`}>
                      {stg.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-4 gap-2 text-[11px] pt-1">
                    <div className="bg-slate-900 p-1.5 rounded-xs border border-slate-800">
                      <div className="text-[9px] text-slate-400 font-bold flex items-center gap-1">
                        <Activity className="w-2.5 h-2.5 text-sky-400" /> HEALTH
                      </div>
                      <div className={`font-bold text-xs mt-0.5 ${stg.health < 75 ? 'text-red-400' : stg.health < 88 ? 'text-amber-400' : 'text-white'}`}>
                        {stg.health.toFixed(0)}%
                      </div>
                    </div>

                    <div className="bg-slate-900 p-1.5 rounded-xs border border-slate-800">
                      <div className="text-[9px] text-slate-400 font-bold flex items-center gap-1">
                        <Thermometer className="w-2.5 h-2.5 text-amber-400" /> TEMP
                      </div>
                      <div className={`font-bold text-xs mt-0.5 ${stg.temp > 1400 ? 'text-red-400' : 'text-white'}`}>
                        {stg.temp.toLocaleString()} °C
                      </div>
                    </div>

                    <div className="bg-slate-900 p-1.5 rounded-xs border border-slate-800">
                      <div className="text-[9px] text-slate-400 font-bold flex items-center gap-1">
                        <Gauge className="w-2.5 h-2.5 text-emerald-400" /> PRESS
                      </div>
                      <div className="font-bold text-xs mt-0.5 text-white">
                        {stg.pressure} Bar
                      </div>
                    </div>

                    <div className="bg-slate-900 p-1.5 rounded-xs border border-slate-800">
                      <div className="text-[9px] text-slate-400 font-bold flex items-center gap-1">
                        <Activity className="w-2.5 h-2.5 text-purple-400" /> VIB
                      </div>
                      <div className={`font-bold text-xs mt-0.5 ${stg.vibration > 1.8 ? 'text-red-400 font-black' : 'text-white'}`}>
                        {stg.vibration} G
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </Panel>
    </div>
  );
});
EngineAnalysisView.displayName = 'EngineAnalysisView';
