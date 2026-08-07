import React, { useMemo } from 'react';
import { Panel } from '@/components';
import { TrendingUp, TrendingDown, Minus, BarChart2, Activity } from 'lucide-react';
import { useTelemetryStore } from '@/stores';
import { useAircraftStore } from '@/stores';
import { useMissionStore } from '@/stores/useMissionStore';
import { MISSION_DATASET } from '@/constants/missionDataset';
import { formatTimeSec } from '@/services/missionPlaybackEngine';

export const HistoricalView: React.FC = React.memo(() => {
  const { historyBuffer } = useTelemetryStore();
  const { fleet, selectedTail } = useAircraftStore();
  const stages = useMissionStore((s) => s.subsystemStages);
  const aiInference = useMissionStore((s) => s.aiInference);

  // Compute sparkline from history buffer (last 30 readings)
  const last30 = useMemo(() => historyBuffer.slice(-30), [historyBuffer]);
  const egtHistory = useMemo(() => last30.map((p) => Math.round(p.sensors.egtKelvin - 273.15)), [last30]);
  const vibHistory = useMemo(() => last30.map((p) => Number(p.sensors.vibrationG.toFixed(2))), [last30]);
  const n1History = useMemo(() => last30.map((p) => p.sensors.n1Rpm), [last30]);

  const trendIcon = (arr: number[]) => {
    if (arr.length < 2) return <Minus className="w-3 h-3 text-slate-400" />;
    const diff = arr[arr.length - 1] - arr[arr.length - 2];
    if (diff > 0) return <TrendingUp className="w-3 h-3 text-red-500" />;
    if (diff < 0) return <TrendingDown className="w-3 h-3 text-emerald-500" />;
    return <Minus className="w-3 h-3 text-slate-400" />;
  };

  // Fleet ranked by health
  const fleetRanked = useMemo(() => [...fleet].sort((a, b) => b.health - a.health), [fleet]);

  // Mission dataset EGT profile for RUL projection
  const rulProjection = useMemo(() =>
    MISSION_DATASET.map((row) => ({
      t: formatTimeSec(row.timeSec),
      rul: Math.max(0, Math.round(row.engineHealth * 7.2)),
      health: row.engineHealth,
      anomaly: row.anomaly,
    })), []);

  return (
    <div className="p-3 h-full overflow-y-auto space-y-3 bg-[#0B132B]">

      {/* ── Rolling Parameter History ──────────────────────────────────────────── */}
      <Panel title="ARINC-429 Parameter Rolling History — Last 30 Readings" icon={Activity}>
        <div className="space-y-3 font-mono text-xs">
          {[
            { label: 'EGT (°C)', data: egtHistory, max: 1200, critLimit: 1000, warnLimit: 850, unit: '°C' },
            { label: 'N1 Spool RPM', data: n1History, max: 12000, critLimit: 11500, warnLimit: 10800, unit: 'RPM' },
            { label: 'Vibration (G)', data: vibHistory, max: 3.0, critLimit: 2.0, warnLimit: 1.6, unit: 'G' },
          ].map((metric) => {
            const current = metric.data[metric.data.length - 1] ?? 0;
            const isCrit = current > metric.critLimit;
            const isWarn = !isCrit && current > metric.warnLimit;
            return (
              <div key={metric.label} className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-300 text-[10px] uppercase">{metric.label}</span>
                  <div className="flex items-center gap-1.5">
                    {trendIcon(metric.data)}
                    <span className={`text-sm font-bold font-mono ${isCrit ? 'text-red-400' : isWarn ? 'text-amber-400' : 'text-white'}`}>
                      {typeof current === 'number' && !isNaN(current) ? (Number.isInteger(current) ? current.toLocaleString() : current.toFixed(2)) : '—'}
                      <span className="text-[10px] font-normal text-sky-400 ml-1">{metric.unit}</span>
                    </span>
                    {isCrit && <span className="text-[8px] font-bold text-red-300 bg-red-950 px-1 py-0.5 rounded-xs border border-red-800 uppercase">CRITICAL</span>}
                    {isWarn && <span className="text-[8px] font-bold text-amber-300 bg-amber-950 px-1 py-0.5 rounded-xs border border-amber-800 uppercase">WARNING</span>}
                  </div>
                </div>
                {/* Sparkline */}
                <div className="flex items-end gap-px h-10 bg-slate-950 border border-slate-800 rounded-sm px-1 pt-1">
                  {metric.data.map((val, i) => {
                    const barH = Math.max(2, Math.min(100, (val / metric.max) * 100));
                    const col = val > metric.critLimit ? 'bg-red-500' : val > metric.warnLimit ? 'bg-amber-500' : 'bg-emerald-500';
                    return (
                      <div key={i} className={`flex-1 rounded-t-xs ${col} transition-all duration-100`}
                        style={{ height: `${barH}%` }} />
                    );
                  })}
                </div>
                <div className="flex justify-between text-[8px] text-slate-400">
                  <span>T-{last30.length}s ago</span>
                  <span className="text-red-400">LIMIT: {metric.critLimit.toLocaleString()}{metric.unit}</span>
                  <span>NOW</span>
                </div>
              </div>
            );
          })}
        </div>
      </Panel>

      {/* ── RUL Degradation Projection ──────────────────────────────────────── */}
      <Panel title="Weibull Proportional RUL Projection — Full Mission Profile" icon={BarChart2}>
        <div className="space-y-2 font-mono text-xs">
          <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
            <span className="text-slate-400">Current RUL: <span className="font-bold text-white">{aiInference.weibull.meanRulHours}h</span></span>
            <span className="text-slate-400">Confidence: <span className="font-bold text-white">{aiInference.weibull.confidenceLowerHrs}h – {aiInference.weibull.confidenceUpperHrs}h</span></span>
          </div>
          <div className="space-y-1">
            {rulProjection.map((pt, i) => {
              const barPct = Math.min(100, (pt.rul / 990) * 100);
              const isCrit = pt.anomaly !== null;
              const isLow = pt.rul < 300;
              return (
                <div key={i} className="flex items-center gap-2">
                  <span className="w-20 text-[9px] text-slate-400 shrink-0">{pt.t}</span>
                  <div className="flex-1 bg-slate-800 rounded-full h-2 relative overflow-hidden">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${isCrit ? 'bg-red-500' : isLow ? 'bg-amber-500' : 'bg-emerald-500'}`}
                      style={{ width: `${barPct}%` }}
                    />
                  </div>
                  <span className={`w-14 text-right text-[9px] font-bold shrink-0 ${isCrit ? 'text-red-400' : isLow ? 'text-amber-400' : 'text-slate-200'}`}>
                    {pt.rul}h
                  </span>
                  {isCrit && <span className="text-[8px] text-red-400 font-bold uppercase shrink-0">⚠ ANOMALY</span>}
                </div>
              );
            })}
          </div>
        </div>
      </Panel>

      {/* ── Fleet Health Ranking ──────────────────────────────────────────────── */}
      <Panel title="Fleet Health Ranking — All Aircraft (Live)" icon={BarChart2} noPad>
        <div className="overflow-x-auto">
          <table className="w-full font-mono text-xs text-left border-collapse">
            <thead>
              <tr className="bg-slate-800 uppercase text-[10px] tracking-wider font-bold text-sky-400 border-b border-slate-700">
                <th className="p-2">Rank</th>
                <th className="p-2">Tail</th>
                <th className="p-2">Squadron</th>
                <th className="p-2">Status</th>
                <th className="p-2">Health</th>
                <th className="p-2">Engine</th>
                <th className="p-2">RUL (hrs)</th>
                <th className="p-2">Warning</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {fleetRanked.map((ac, i) => {
                const healthColor = ac.health >= 90 ? 'text-emerald-400' : ac.health >= 75 ? 'text-amber-400' : 'text-red-400';
                const isSelected = ac.tail === selectedTail;
                return (
                  <tr key={ac.tail} className={`transition-colors ${isSelected ? 'bg-sky-950/70' : 'hover:bg-slate-800/80'}`}>
                    <td className="p-2 font-bold text-slate-400 text-[10px]">#{i + 1}</td>
                    <td className="p-2">
                      <span className={`font-bold text-[11px] ${isSelected ? 'text-sky-300' : 'text-white'}`}>{ac.tail}</span>
                      {isSelected && <span className="ml-1 text-[8px] text-sky-400 font-bold uppercase">ACTIVE</span>}
                    </td>
                    <td className="p-2 text-[10px] text-slate-400 truncate max-w-[120px]">{ac.squadron}</td>
                    <td className="p-2 text-[10px] font-bold text-slate-200">{ac.status}</td>
                    <td className="p-2">
                      <div className="flex items-center gap-1.5">
                        <div className="w-16 bg-slate-800 rounded-full h-1.5">
                          <div className={`h-1.5 rounded-full ${ac.health >= 90 ? 'bg-emerald-500' : ac.health >= 75 ? 'bg-amber-500' : 'bg-red-500'}`} style={{ width: `${ac.health}%` }} />
                        </div>
                        <span className={`font-bold text-[10px] ${healthColor}`}>{ac.health}%</span>
                      </div>
                    </td>
                    <td className="p-2 text-[10px] text-slate-200 font-medium">{ac.engineHealth}%</td>
                    <td className={`p-2 font-bold text-[10px] ${ac.tboRulHrs < 200 ? 'text-red-400' : ac.tboRulHrs < 400 ? 'text-amber-400' : 'text-slate-200'}`}>{ac.tboRulHrs}h</td>
                    <td className="p-2 text-[10px] text-amber-400 truncate max-w-[120px]">{ac.warning ?? '—'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>

      {/* ── Engine Stage Health History ───────────────────────────────────────── */}
      <Panel title="Subsystem Stage Health Index — Live Ranking" icon={Activity}>
        <div className="grid grid-cols-4 gap-2 font-mono text-xs">
          {[...stages].sort((a, b) => a.health - b.health).map((stg, i) => {
            const isBottom = i < 2;
            return (
              <div key={stg.ref} className={`p-2 rounded-sm border shadow-sm ${stg.status === 'CRITICAL' ? 'bg-red-950/80 border-red-800' : stg.status === 'WARNING' ? 'bg-amber-950/80 border-amber-800' : 'bg-slate-950/80 border-slate-800'}`}>
                <div className="flex items-center justify-between mb-1">
                  <span className={`font-bold text-[10px] uppercase ${stg.status === 'CRITICAL' ? 'text-red-400' : 'text-sky-300'}`}>{stg.ref}</span>
                  {isBottom && <span className="text-[8px] bg-amber-950 text-amber-300 font-bold px-1 py-0.5 rounded-xs border border-amber-800">LOWEST</span>}
                </div>
                <div className={`text-lg font-bold font-mono ${stg.health < 70 ? 'text-red-400' : stg.health < 85 ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {stg.health.toFixed(0)}%
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5 mt-1">
                  <div className={`h-1.5 rounded-full transition-all duration-500 ${stg.health < 70 ? 'bg-red-500' : stg.health < 85 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                    style={{ width: `${stg.health}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </Panel>
    </div>
  );
});
HistoricalView.displayName = 'HistoricalView';
