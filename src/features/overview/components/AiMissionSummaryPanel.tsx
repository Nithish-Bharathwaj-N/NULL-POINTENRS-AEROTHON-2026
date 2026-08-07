import React, { useMemo } from 'react';
import { Panel, HealthRing } from '@/components';
import { BrainCircuit, Cpu, AlertTriangle, ShieldCheck } from 'lucide-react';
import { useMissionStore } from '@/stores';

export const AiMissionSummaryPanel: React.FC = React.memo(() => {
  const inf = useMissionStore((state) => state.aiInference);
  const alerts = useMissionStore((state) => state.alerts);
  const telemetry = useMissionStore((state) => state.telemetry);

  // Calculate Weibull confidence band width as percentage of 1000 hours
  const lowerPct = Math.min(100, Math.max(0, (inf.weibull.confidenceLowerHrs / 1000) * 100));
  const meanPct = Math.min(100, Math.max(0, (inf.weibull.meanRulHours / 1000) * 100));
  const upperPct = Math.min(100, Math.max(0, (inf.weibull.confidenceUpperHrs / 1000) * 100));
  const bandWidth = Math.max(2, upperPct - lowerPct);

  const isCrit = inf.weibull.meanRulHours < 150 || alerts.some((a) => a.severity === 'CRITICAL');
  const isWarn = !isCrit && (inf.weibull.meanRulHours < 350 || alerts.length > 0);

  // Dynamic SHAP factor adjustments based on live telemetry stress
  const dynamicShap = useMemo(() => {
    const t4Stress = Math.max(0, Math.round((telemetry.t4Kelvin - 1623.15) * 0.15));
    const vibStress = Math.max(0, Math.round((telemetry.vibrationG - 1.2) * 20));

    return inf.shapleyFactors.map((fac) => {
      let val = fac.shapleyValuePct;
      if (fac.parameter.includes('T4') || fac.parameter.includes('Temp')) val += t4Stress;
      if (fac.parameter.includes('Vibration')) val += vibStress;
      return { ...fac, shapleyValuePct: val };
    });
  }, [inf.shapleyFactors, telemetry.t4Kelvin, telemetry.vibrationG]);

  return (
    <Panel title="AeroNet-v4 Propulsion AI Diagnostics" icon={BrainCircuit} className="h-full" highContrastHeader={isCrit}>
      <div className="space-y-3 font-mono text-xs">
        {/* Top RUL and Health Ring Header */}
        <div className={`p-3 rounded-sm border shadow-sm flex items-center justify-between gap-4 transition-colors ${
          isCrit ? 'bg-red-950/90 border-red-800 ring-1 ring-red-700' : isWarn ? 'bg-amber-950/90 border-amber-800' : 'bg-sky-950/80 border-sky-800'
        }`}>
          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-1.5 text-[10px] font-bold text-sky-300 uppercase tracking-widest">
              <span>WEIBULL PROPORTIONAL RUL MODEL</span>
              {isCrit && <span className="bg-red-600 text-white px-1 py-0.5 rounded-xs animate-pulse">WEAR-OUT ANOMALY</span>}
            </div>
            <div className="text-xl font-bold text-white tracking-tight">
              {inf.weibull.meanRulHours.toLocaleString()} <span className="text-xs font-normal text-slate-300">Hours Remaining</span>
            </div>
            <div className="text-[10px] text-sky-400 font-semibold">
              95% Confidence Interval: [{inf.weibull.confidenceLowerHrs} – {inf.weibull.confidenceUpperHrs} Hrs]
            </div>

            {/* Weibull Probability Density & Confidence Band Bar */}
            <div className="pt-2">
              <div className="text-[9px] text-slate-400 flex justify-between mb-0.5">
                <span>0h (FAIL)</span>
                <span>RUL CONFIDENCE BAND</span>
                <span>1,000h (TBO)</span>
              </div>
              <div className="w-full bg-slate-800 h-3 rounded-full relative overflow-hidden flex items-center">
                <div
                  className={`h-full opacity-40 transition-all duration-300 ${isCrit ? 'bg-red-500' : isWarn ? 'bg-amber-500' : 'bg-sky-500'}`}
                  style={{ left: `${lowerPct}%`, width: `${bandWidth}%`, position: 'absolute' }}
                />
                <div
                  className={`h-full w-1 rounded-full shadow-md transition-all duration-300 ${isCrit ? 'bg-red-500 animate-ping' : isWarn ? 'bg-amber-400' : 'bg-sky-400'}`}
                  style={{ left: `${meanPct}%`, position: 'absolute' }}
                />
              </div>
            </div>
          </div>

          <div className="shrink-0 flex flex-col items-center justify-center pl-2 border-l border-sky-800/60">
            <HealthRing
              health={inf.healthIndex}
              size={68}
              stroke={7}
              label={`${Math.round(inf.healthIndex)}%`}
            />
          </div>
        </div>

        {/* Live Shapley Causal Factor Waterfall Breakdown */}
        <div className="space-y-1.5 bg-slate-950/80 border border-slate-800 rounded-sm p-2.5 shadow-inner">
          <div className="text-[10px] font-bold text-sky-400 border-b border-slate-800 pb-1 mb-1.5 uppercase tracking-wider flex items-center justify-between">
            <span>SHAPLEY CAUSAL FACTOR WATERFALL</span>
            <span className="text-slate-400">MODEL: {inf.weibull.modelType}</span>
          </div>

          {dynamicShap.map((fac, idx) => {
            const isDegrading = fac.direction === 'DEGRADING';
            const barPct = Math.min(100, Math.max(5, fac.shapleyValuePct * 2.2));
            return (
              <div key={idx} className="space-y-1 py-1 border-b border-slate-800/60 last:border-0">
                <div className="flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-white">{fac.parameter}</span>
                    <span className="text-[9px] text-slate-400 ml-1.5">({fac.arincWord})</span>
                  </div>
                  <span className={`px-1.5 py-0.5 rounded-xs font-bold text-[10px] ${isDegrading ? 'bg-red-950 text-red-300 border border-red-800' : 'bg-emerald-950 text-emerald-300 border border-emerald-800'}`}>
                    {isDegrading ? `-${fac.shapleyValuePct}% Impact` : `+${fac.shapleyValuePct}% Margin`}
                  </span>
                </div>
                {/* Horizontal Waterfall Impact Bar */}
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden flex">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${isDegrading ? 'bg-red-500' : 'bg-emerald-500'}`}
                    style={{ width: `${barPct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* Recent AI Diagnostic Triage Decision Log */}
        <div className="p-2 bg-slate-900 text-slate-300 rounded-sm border border-slate-800 text-[10px] space-y-1">
          <div className="flex items-center justify-between text-sky-400 font-bold border-b border-slate-800 pb-1">
            <span className="flex items-center gap-1"><Cpu className="w-3 h-3" /> RECENT AI TRIAGE DECISION LOG</span>
            <span className="text-slate-500 font-normal">β = 1.84 (Wear-out phase)</span>
          </div>
          {alerts.length > 0 ? (
            <div className="flex items-center gap-2 text-red-400 font-bold animate-pulse">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-red-500" />
              <span className="truncate">T-0s: {alerts[0].title} → RECOMMENDED: {alerts[0].recommendedAction}</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-emerald-400">
              <ShieldCheck className="w-3.5 h-3.5 shrink-0 text-emerald-500" />
              <span>T-0s: Thermodynamic residuals nominal. Continuous 1Hz Weibull sampling active.</span>
            </div>
          )}
        </div>
      </div>
    </Panel>
  );
});
AiMissionSummaryPanel.displayName = 'AiMissionSummaryPanel';
