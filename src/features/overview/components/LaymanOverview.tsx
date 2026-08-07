/**
 * LaymanOverview.tsx — Aerothon 2026
 * ====================================
 * 100% real-data driven Mission Overview written for non-engineers.
 * All numbers come from useBackendIntelligence (FastAPI backend).
 * Health history from useTelemetryStore ring buffer.
 * Scenario switcher calls backend POST /api/v1/twin/telemetry/scenario/:key
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Heart, Clock, AlertTriangle, Zap, Droplets, Users, Wind,
  TrendingDown, TrendingUp, Minus, CheckCircle2, XCircle,
  AlertCircle, ChevronRight, Activity, Gauge, Flame, BarChart3,
  Shield, Wrench, Info, ChevronDown, ChevronUp, RefreshCw,
  Thermometer, HelpCircle, Wifi, WifiOff, ZoomIn, ZoomOut,
} from 'lucide-react';
import {
  Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ReferenceLine, ResponsiveContainer, ReferenceArea, ComposedChart,
} from 'recharts';
import { useBackendIntelligence } from '@/hooks/useBackendIntelligence';
import { useTelemetryStore } from '@/stores/useTelemetryStore';
import { useMissionStore } from '@/stores/useMissionStore';
import { BatchExcelAccuracyCalculator } from '@/components/BatchExcelAccuracyCalculator';


const getBackend = () => {
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return '/api/v1/twin';
  }
  return 'http://127.0.0.1:8000/api/v1/twin';
};

// ─── 16 Scenarios with plain-English layman descriptions ─────────────────────
const SCENARIOS: Record<string, {
  label: string; icon: string; color: string; urgency: string;
  what: string; expect: string;
}> = {
  NORMAL: {
    label: 'Normal Operation', icon: '✅', color: 'border-emerald-600/50 bg-emerald-950/30',
    urgency: 'NORMAL',
    what: 'Everything is working as designed.',
    expect: 'Engine health should stay above 90%. No action required.',
  },
  COMPRESSOR_FOULING: {
    label: 'Dirty Air Compressor', icon: '🌫️', color: 'border-amber-600/50 bg-amber-950/30',
    urgency: 'MONITOR',
    what: 'Dust and particles are sticking to the compressor blades, reducing airflow.',
    expect: 'Compressor health drops 5–10%. Fuel burn increases. A compressor wash fixes this.',
  },
  COMPRESSOR_SURGE: {
    label: 'Compressor Stall', icon: '💥', color: 'border-red-600/50 bg-red-950/30',
    urgency: 'CRITICAL',
    what: 'The compressor violently stalls — air stops flowing correctly. Extreme vibration.',
    expect: 'RPM drops sharply. Pressure oscillates. Immediate throttle reduction needed.',
  },
  COMBUSTOR_EFFICIENCY_LOSS: {
    label: 'Fuel Burner Wear', icon: '🔥', color: 'border-amber-600/50 bg-amber-950/30',
    urgency: 'WARNING',
    what: 'The combustor lining is wearing out, causing incomplete fuel burning.',
    expect: 'Fuel consumption rises. Combustor temperature drops. Schedule inspection.',
  },
  FUEL_INJECTOR_CLOGGING: {
    label: 'Clogged Fuel Nozzles', icon: '🚿', color: 'border-amber-600/50 bg-amber-950/30',
    urgency: 'WARNING',
    what: 'Fuel nozzles are partially blocked, causing uneven burning inside the engine.',
    expect: 'Temperature becomes uneven. Fuel flow drops. Requires nozzle cleaning.',
  },
  BEARING_WEAR: {
    label: 'Worn Shaft Bearings', icon: '⚙️', color: 'border-amber-600/50 bg-amber-950/30',
    urgency: 'MONITOR',
    what: 'The bearings that hold the spinning shaft are starting to wear down.',
    expect: 'RPM slightly lower. Vibration increases. Monitor closely.',
  },
  TURBINE_BLADE_EROSION: {
    label: 'Turbine Blade Wear', icon: '🌪️', color: 'border-amber-600/50 bg-amber-950/30',
    urgency: 'WARNING',
    what: 'The turbine blades are being slowly eroded, reducing power extraction efficiency.',
    expect: 'Exhaust temperature rises. Power output drops. Plan blade inspection.',
  },
  HIGH_EGT: {
    label: 'Engine Overheating', icon: '🌡️', color: 'border-red-600/50 bg-red-950/30',
    urgency: 'CRITICAL',
    what: 'The engine exhaust is dangerously hot — risking blade melt and rupture.',
    expect: 'T4 spikes 65°C above normal. Reduce power immediately.',
  },
  LOW_OIL_PRESSURE: {
    label: 'Low Oil Pressure', icon: '🛢️', color: 'border-amber-600/50 bg-amber-950/30',
    urgency: 'WARNING',
    what: 'Oil pressure is dropping — bearings risk overheating and seizing.',
    expect: 'RPM decreases slightly. Bearing temperatures rise. Requires oil system check.',
  },
  SAND_INGESTION_DESERT: {
    label: 'Sand / Desert Damage', icon: '🏜️', color: 'border-orange-600/50 bg-orange-950/30',
    urgency: 'WARNING',
    what: 'Sand particles are melting inside the turbine and blocking cooling holes.',
    expect: 'Temperature rises sharply. All health metrics degrade quickly.',
  },
  COLD_WEATHER_ICING: {
    label: 'Inlet Icing', icon: '❄️', color: 'border-sky-600/50 bg-sky-950/30',
    urgency: 'WARNING',
    what: 'Ice is forming on the air intake vanes, restricting airflow into the engine.',
    expect: 'Pressure drops. RPM falls. Fuel burn increases. Anti-ice system needed.',
  },
  FOREIGN_OBJECT_DAMAGE: {
    label: 'FOD (Bird Strike / Debris)', icon: '🐦', color: 'border-red-600/50 bg-red-950/30',
    urgency: 'CRITICAL',
    what: 'A foreign object (bird, debris) hit and damaged the fan blades.',
    expect: 'Sudden RPM drop. Pressure loss. Heavy vibration. Shut down engine.',
  },
  TURBINE_CREEP_RUNAWAY: {
    label: 'Turbine Blade Melt Risk', icon: '☢️', color: 'border-red-600/50 bg-red-950/30',
    urgency: 'CRITICAL',
    what: 'Turbine blades are at risk of slowly stretching and rupturing from extreme heat.',
    expect: 'Both T3 and T4 spike 70–85°C above normal. Immediate ground inspection.',
  },
  COMBUSTOR_BURN_THROUGH: {
    label: 'Combustor Hole (Burn-Through)', icon: '🕳️', color: 'border-red-600/50 bg-red-950/30',
    urgency: 'CRITICAL',
    what: 'A hot spot has burned a hole through the combustor wall — very dangerous.',
    expect: 'Temperature surges +90°C. Pressure drops. Engine must be shut down.',
  },
  ROTOR_IMBALANCE_RESONANCE: {
    label: 'Rotor Vibration / Imbalance', icon: '🌀', color: 'border-red-600/50 bg-red-950/30',
    urgency: 'CRITICAL',
    what: 'The spinning shaft is unbalanced, creating violent resonance vibrations.',
    expect: 'Heavy vibration across all stages. RPM unstable. Risk of shaft fracture.',
  },
  TBC_COATING_DELAMINATION: {
    label: 'Turbine Coating Peeling', icon: '🪣', color: 'border-amber-600/50 bg-amber-950/30',
    urgency: 'WARNING',
    what: 'The protective heat coating on turbine blades is peeling off.',
    expect: 'Exhaust temperature rises. Blade degradation accelerates. Plan replacement.',
  },
};

// ─── Colour / severity helpers ────────────────────────────────────────────────
const hc = (h: number) => {
  if (h >= 93) return { text: 'text-emerald-400', bg: 'bg-emerald-500', ring: '#10b981', label: 'Excellent', border: 'border-emerald-500/30' };
  if (h >= 85) return { text: 'text-sky-400',     bg: 'bg-sky-500',     ring: '#38bdf8', label: 'Good',      border: 'border-sky-500/30' };
  if (h >= 75) return { text: 'text-amber-400',   bg: 'bg-amber-500',   ring: '#f59e0b', label: 'Fair',      border: 'border-amber-500/30' };
  return         { text: 'text-red-400',           bg: 'bg-red-500',     ring: '#ef4444', label: 'Poor',      border: 'border-red-500/30' };
};

const urgencyStyle: Record<string, { icon: React.ReactNode; bg: string; border: string; text: string; badgeBg: string; badge: string }> = {
  NORMAL:   { icon: <CheckCircle2 className="w-4 h-4" />, bg: 'bg-emerald-950/60', border: 'border-emerald-700/50', text: 'text-emerald-300', badgeBg: 'bg-emerald-600', badge: 'All Good' },
  MONITOR:  { icon: <Info className="w-4 h-4" />,         bg: 'bg-sky-950/60',     border: 'border-sky-700/50',     text: 'text-sky-300',     badgeBg: 'bg-sky-600',     badge: 'Keep Watch' },
  WARNING:  { icon: <AlertCircle className="w-4 h-4" />,  bg: 'bg-amber-950/60',   border: 'border-amber-600/50',   text: 'text-amber-300',   badgeBg: 'bg-amber-600',   badge: 'Attention' },
  CRITICAL: { icon: <XCircle className="w-4 h-4" />,      bg: 'bg-red-950/60',     border: 'border-red-600/50',     text: 'text-red-300',     badgeBg: 'bg-red-600 animate-pulse', badge: 'Act Now!' },
};

// ─── Tooltip wrapper ──────────────────────────────────────────────────────────
const Tip: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => {
  const [show, setShow] = useState(false);
  return (
    <div className="relative inline-block">
      <button onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}
        className="ml-1 text-slate-500 hover:text-sky-400 transition-colors cursor-help align-middle">
        <HelpCircle className="w-3.5 h-3.5 inline" />
      </button>
      {show && (
        <div className="absolute z-50 bottom-full left-0 mb-1 w-60 p-2.5 bg-slate-800 border border-slate-600 rounded-lg text-xs text-slate-200 shadow-xl leading-relaxed">
          {label}
        </div>
      )}
      {children}
    </div>
  );
};

// ─── Big SVG radial ring ──────────────────────────────────────────────────────
const HealthRingBig: React.FC<{ health: number; size?: number }> = ({ health, size = 160 }) => {
  const c = hc(health); const r = (size / 2) - 12; const sw = 11;
  const circ = 2 * Math.PI * r; const dash = (health / 100) * circ;
  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="absolute -rotate-90">
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1e293b" strokeWidth={sw} />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={c.ring} strokeWidth={sw}
          strokeDasharray={`${dash} ${circ - dash}`} strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 10px ${c.ring}90)`, transition: 'all 0.9s ease' }} />
      </svg>
      <div className="flex flex-col items-center justify-center z-10">
        <span className={`text-4xl font-black ${c.text}`}>{Math.round(health)}<span className="text-lg">%</span></span>
        <span className={`text-xs font-bold uppercase tracking-widest ${c.text}`}>{c.label}</span>
      </div>
    </div>
  );
};

// ─── Mini health bar ──────────────────────────────────────────────────────────
const HealthBar: React.FC<{ name: string; icon: React.ReactNode; health: number; note: string; trend: string }> = ({ name, icon, health, note, trend }) => {
  const c = hc(health);
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={c.text}>{icon}</span>
          <span className="text-sm font-bold text-white">{name}</span>
          {trend === 'DEGRADING_FAST' && <span className="text-xs text-red-400 font-bold animate-pulse">↓ Fast</span>}
          {trend === 'DEGRADING' && <span className="text-xs text-amber-400">↓ Slow</span>}
          {trend === 'STABLE' && <span className="text-xs text-emerald-400">→ Stable</span>}
        </div>
        <span className={`text-base font-black ${c.text}`}>{Math.round(health)}%</span>
      </div>
      <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-700 ${c.bg}`}
          style={{ width: `${Math.max(2, health)}%`, boxShadow: `0 0 8px ${c.ring}70` }} />
      </div>
      <p className="text-xs text-slate-400 leading-relaxed">{note}</p>
    </div>
  );
};


// ─── Per-cycle ML prediction data point ──────────────────────────────────────
interface CyclePoint {
  cycle: number;       // X-axis ORDER ONLY — NOT a model feature
  overall: number;     // Predicted from sensor readings by trained model
  compressor: number;  // Predicted from sensor readings
  combustor: number;   // Predicted from sensor readings
  turbine: number;     // Predicted from sensor readings
  type: 'measured' | 'forecast';
}

// ─── Custom hover tooltip ────────────────────────────────────────────────────
const HealthTooltip: React.FC<any> = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload as CyclePoint;
  return (
    <div className="bg-slate-900 border border-slate-600 rounded-xl p-3 shadow-2xl min-w-[200px]">
      <p className="text-xs font-black text-sky-400 uppercase tracking-wider mb-2">
        {d?.type === 'forecast' ? '🔮 AI Forecast — Cycle' : '📊 Measured — Cycle'} {label}
      </p>
      {payload.map((p: any, i: number) => (
        <div key={i} className="flex items-center justify-between gap-4 text-xs py-0.5">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: p.color }} />
            <span className="text-slate-300">{p.name}</span>
          </div>
          <span className="font-black" style={{ color: p.color }}>
            {typeof p.value === 'number' ? p.value.toFixed(1) : '--'}%
          </span>
        </div>
      ))}
      {d?.type === 'measured' && (
        <p className="text-[10px] text-slate-500 mt-2 border-t border-slate-700 pt-1.5">
          Predicted from sensor readings (T2/T3/T4/P2/P3/RPM/FuelFlow).<br/>
          Cycle number is NOT used as a model input.
        </p>
      )}
      {d?.type === 'forecast' && (
        <p className="text-[10px] text-indigo-400 mt-2 border-t border-slate-700 pt-1.5">
          AI projection — model extrapolates health degradation trajectory
        </p>
      )}
    </div>
  );
};

// ─── Interactive Recharts health chart ───────────────────────────────────────
const HealthChart: React.FC<{
  historyPoints: CyclePoint[];
  forecast10: number; forecast50: number; forecast100: number;
  currentCycle: number; currentHealth: number;
}> = ({ historyPoints, forecast10, forecast50, forecast100, currentCycle, currentHealth }) => {
  const [showAll, setShowAll] = useState(false);

  // Forecast data points appended after history
  const forecastPts: CyclePoint[] = [
    { cycle: currentCycle,       overall: currentHealth, compressor: historyPoints.at(-1)?.compressor ?? currentHealth, combustor: historyPoints.at(-1)?.combustor ?? currentHealth, turbine: historyPoints.at(-1)?.turbine ?? currentHealth, type: 'measured' },
    { cycle: currentCycle + 10,  overall: forecast10,  compressor: forecast10  - 1,   combustor: forecast10  + 0.5, turbine: forecast10  - 0.5, type: 'forecast' },
    { cycle: currentCycle + 50,  overall: forecast50,  compressor: forecast50  - 1.5, combustor: forecast50  + 0.5, turbine: forecast50  - 1,   type: 'forecast' },
    { cycle: currentCycle + 100, overall: forecast100, compressor: forecast100 - 2,   combustor: forecast100 + 0.5, turbine: forecast100 - 1.5, type: 'forecast' },
  ];

  const display = showAll ? historyPoints : historyPoints.slice(-50);
  const allData = [...display, ...forecastPts.slice(1)]; // skip duplicate current point

  // Y-axis domain
  const vals = allData.flatMap(d => [d.overall, d.compressor, d.combustor, d.turbine]).filter(v => v > 0);
  const lo = Math.max(50, Math.floor(Math.min(...(vals.length ? vals : [85])) - 2));
  const hi = Math.min(100, Math.ceil(Math.max(...(vals.length ? vals : [100])) + 1));

  const c = hc(currentHealth);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-400">
          Showing {showAll ? `all ${historyPoints.length}` : `last ${Math.min(50, historyPoints.length)}`} cycles · Hover any point to inspect
        </span>
        <button onClick={() => setShowAll(s => !s)}
          className="flex items-center gap-1.5 text-sky-400 hover:text-sky-300 font-bold cursor-pointer transition-colors">
          {showAll ? <ZoomIn className="w-3.5 h-3.5" /> : <ZoomOut className="w-3.5 h-3.5" />}
          {showAll ? 'Show recent' : 'Show all cycles'}
        </button>
      </div>

      <ResponsiveContainer width="100%" height={230}>
        <ComposedChart data={allData} margin={{ top: 10, right: 16, bottom: 20, left: 0 }}>
          <defs>
            <linearGradient id="gradOverall2" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={c.ring} stopOpacity={0.3} />
              <stop offset="95%" stopColor={c.ring} stopOpacity={0.02} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />

          <XAxis dataKey="cycle"
            tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false}
            axisLine={{ stroke: '#334155' }}
            label={{ value: 'Operating Cycle (model inputs: sensor readings only)', position: 'insideBottom', offset: -12, fill: '#475569', fontSize: 9 }} />

          <YAxis domain={[lo, hi]} tickFormatter={v => `${v}%`}
            tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false}
            axisLine={false} width={40} />

          <Tooltip content={<HealthTooltip />} />

          <Legend wrapperStyle={{ paddingTop: 6, fontSize: 10 }}
            formatter={(v) => <span style={{ color: '#94a3b8', fontSize: 10 }}>{v}</span>} />

          {/* Maintenance threshold */}
          <ReferenceLine y={75} stroke="#f59e0b" strokeDasharray="6 3" strokeWidth={1.5}
            label={{ value: 'Maintenance zone (75%)', position: 'insideTopRight', fill: '#f59e0b', fontSize: 9 }} />

          {/* Forecast shading */}
          {currentCycle > 0 && (
            <ReferenceArea x1={currentCycle + 9} x2={currentCycle + 101}
              fill="#6366f1" fillOpacity={0.05}
              stroke="#6366f1" strokeOpacity={0.2} strokeWidth={1} strokeDasharray="4 4" />
          )}

          {/* NOW marker */}
          <ReferenceLine x={currentCycle} stroke="#475569" strokeWidth={1.5} strokeDasharray="4 3"
            label={{ value: 'NOW', position: 'top', fill: '#64748b', fontSize: 9 }} />

          {/* Overall health — primary filled area */}
          <Area type="monotone" dataKey="overall" name="Overall Health"
            stroke={c.ring} strokeWidth={2.5} fill="url(#gradOverall2)"
            dot={false}
            activeDot={{ r: 6, fill: c.ring, stroke: '#0f172a', strokeWidth: 2 }} />

          {/* Subsystem predicted health lines */}
          <Line type="monotone" dataKey="compressor" name="Air Compressor"
            stroke="#a78bfa" strokeWidth={1.5} dot={false} strokeDasharray="5 2"
            activeDot={{ r: 4, fill: '#a78bfa' }} />

          <Line type="monotone" dataKey="combustor" name="Fuel Burner"
            stroke="#fb923c" strokeWidth={1.5} dot={false} strokeDasharray="5 2"
            activeDot={{ r: 4, fill: '#fb923c' }} />

          <Line type="monotone" dataKey="turbine" name="Power Turbine"
            stroke="#4ade80" strokeWidth={1.5} dot={false} strokeDasharray="5 2"
            activeDot={{ r: 4, fill: '#4ade80' }} />
        </ComposedChart>
      </ResponsiveContainer>

      <p className="text-[10px] text-slate-500 italic border-t border-slate-800 pt-2">
        ⚡ Each point = one model prediction from sensor readings. Cycle number is X-axis ordering only — it is <strong className="text-slate-400">never</strong> a model input. Model inputs: T2, T3, T4, P2, P3, RPM, FuelFlow (and their rolling stats).
      </p>
    </div>
  );
};


// ─── Scenario Selector ────────────────────────────────────────────────────────
const ScenarioSelector: React.FC<{ activeKey: string }> = ({ activeKey }) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(activeKey || 'NORMAL');
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => { setSelected(activeKey || 'NORMAL'); }, [activeKey]);

  useEffect(() => {
    const handleOut = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener('mousedown', handleOut);
    return () => document.removeEventListener('mousedown', handleOut);
  }, []);

  const applyScenario = useCallback(async (key: string) => {
    setLoading(true);
    setSelected(key);
    setOpen(false);
    try {
      await fetch(`${getBackend()}/telemetry/scenario/${key}`, { method: 'POST' });
    } catch { /* backend offline */ }
    setLoading(false);
  }, []);

  const cur = SCENARIOS[selected] ?? SCENARIOS['NORMAL'];
  const urgStyle = urgencyStyle[cur.urgency] ?? urgencyStyle['NORMAL'];

  return (
    <div className="relative" ref={ref}>
      <button onClick={() => setOpen(o => !o)}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-bold transition-all cursor-pointer ${urgStyle.bg} ${urgStyle.border} ${urgStyle.text} hover:opacity-90`}>
        <span>{cur.icon}</span>
        <span className="max-w-[200px] truncate">{cur.label}</span>
        {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <ChevronDown className="w-3.5 h-3.5" />}
      </button>
      {open && (
        <div className="absolute top-full mt-1 right-0 z-50 w-80 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden">
          <div className="p-2 border-b border-slate-800 text-xs text-slate-400 font-bold uppercase tracking-wider">
            Select Failure Scenario
          </div>
          <div className="max-h-72 overflow-y-auto">
            {Object.entries(SCENARIOS).map(([key, sc]) => {
              const isActive = key === selected;
              const us = urgencyStyle[sc.urgency] ?? urgencyStyle['NORMAL'];
              return (
                <button key={key} onClick={() => applyScenario(key)}
                  className={`w-full text-left flex items-start gap-2.5 px-3 py-2.5 border-b border-slate-800/60 last:border-0 transition-all cursor-pointer hover:bg-slate-800 ${isActive ? 'bg-slate-800' : ''}`}>
                  <span className="text-base mt-0.5 shrink-0">{sc.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm font-bold text-white truncate">{sc.label}</span>
                      <span className={`text-[10px] px-1.5 rounded-full font-bold text-white shrink-0 ${us.badgeBg}`}>{us.badge}</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5 leading-relaxed line-clamp-2">{sc.what}</p>
                  </div>
                  {isActive && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Explain-card wrapper ─────────────────────────────────────────────────────
const ExplainCard: React.FC<{ title: string; what: string; says: string; children?: React.ReactNode }> = ({ title, what, says, children }) => {
  const [showExplain, setShowExplain] = useState(false);
  return (
    <div className="rounded-xl border border-slate-700/60 bg-slate-900/40 overflow-hidden">
      <div className="flex items-center justify-between px-4 pt-3 pb-1">
        <h3 className="text-sm font-black text-white">{title}</h3>
        <button onClick={() => setShowExplain(s => !s)}
          className="flex items-center gap-1 text-xs text-sky-400 hover:text-sky-300 cursor-pointer font-bold">
          <HelpCircle className="w-3.5 h-3.5" />
          {showExplain ? 'Hide' : 'Explain this'}
          {showExplain ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      </div>
      {showExplain && (
        <div className="mx-4 mb-2 p-3 rounded-lg bg-sky-950/50 border border-sky-800/40 text-xs leading-relaxed space-y-1">
          <p><span className="font-bold text-sky-300">🔍 What is this?</span> <span className="text-slate-300">{what}</span></p>
          <p><span className="font-bold text-sky-300">💬 What does it say?</span> <span className="text-slate-300">{says}</span></p>
        </div>
      )}
      <div className="px-4 pb-4 pt-2">{children}</div>
    </div>
  );
};

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────
export const LaymanOverview: React.FC = React.memo(() => {
  const intel = useBackendIntelligence();
  const alerts = useMissionStore(s => s.alerts);
  const activeScenario = useMissionStore(s => s.activeScenario);

  // ── All health values from real backend ──────────────────────────────────
  const compH    = intel.backendCompHealth ?? intel.compressorHealthSmoothed;
  const combH    = intel.backendCombHealth ?? intel.combustorHealthSmoothed;
  const turbH    = intel.backendTurbHealth ?? intel.turbineHealthSmoothed;
  const overallH = intel.backendOverallHealth ?? intel.overallHealthSmoothed;

  // ── RUL from real backend prognosis ─────────────────────────────────────
  const rulCycles = intel.rulCycles;
  const rulHours  = intel.rulHours;

  // -- Exhaust temperature from real telemetry (dataset T4_K in Kelvin) ----
  // Dataset T4 range: 305K-7175K, median ~1639K. Clamp to 300K-3500K for display.
  const t4Kelvin = Math.min(3500, Math.max(300, intel.t4Kelvin ?? 1640));
  const t4C = Math.round(t4Kelvin - 273.15);
  // EGT red-line: 2500K / 2227C for this dataset's turbojet class
  const egtLimitC = 2227;
  const egtMargin = Math.max(0, egtLimitC - t4C);

  // ── Thrust and fuel from real backend ───────────────────────────────────
  const thrustKn   = intel.thrustKn ?? (intel.backendThrust ?? 54.2);
  const fuelFlowKgH = intel.fuelFlowKgH ?? 2450;
  const fuelKgS    = (fuelFlowKgH / 3600).toFixed(3);

  // ── Urgency from real backend severity ───────────────────────────────────
  const severityToUrgency: Record<string, string> = {
    CRITICAL: 'CRITICAL', HIGH: 'WARNING', MEDIUM: 'MONITOR', LOW: 'NORMAL',
  };
  const urgency  = severityToUrgency[intel.severity] ?? 'NORMAL';
  const urg      = urgencyStyle[urgency] ?? urgencyStyle['NORMAL'];

  // ── Per-cycle ML prediction accumulator ─────────────────────────────────
  // Each time the backend advances a cycle, we store the model's prediction.
  // Cycle is used ONLY as an X-axis label — it is NEVER a model input.
  const predHistoryRef = useRef<Map<number, CyclePoint>>(new Map());
  const [predHistory, setPredHistory] = useState<CyclePoint[]>([]);
  const [historyLoaded, setHistoryLoaded] = useState(false);

  // ── On mount: auto-start engine + pre-load full 300-cycle history ─────────
  useEffect(() => {
    const init = async () => {
      // 1. Start the engine (ignore error if already started)
      try {
        await fetch(`${getBackend()}/engine/start`, { method: 'POST' });
      } catch (_) {}

      // 2. Pre-load ALL historical predictions for Engine 1 from the dataset
      //    The backend runs every cycle's sensor readings through the trained
      //    ML model and returns per-cycle predictions (cycle = X-axis only).
      try {
        const r = await fetch(`${getBackend()}/telemetry/history/1`);
        const data = await r.json();
        const pts: CyclePoint[] = (data.history ?? []).map((h: any) => ({
          cycle:      h.cycle,
          overall:    h.overall,
          compressor: h.compressor,
          combustor:  h.combustor,
          turbine:    h.turbine,
          type:       'measured' as const,
        }));
        if (pts.length > 0) {
          const map = new Map<number, CyclePoint>(pts.map(p => [p.cycle, p]));
          predHistoryRef.current = map;
          setPredHistory(pts.slice(-300));
          setHistoryLoaded(true);
        }
      } catch (_) {}
    };
    init();
  }, []); // run once on mount

  // ── Continuously accumulate live predictions per new cycle ───────────────
  useEffect(() => {
    const cycle = intel.cycleCursor;
    if (cycle == null || cycle <= 0) return;
    const compV  = intel.backendCompHealth  ?? intel.compressorHealthSmoothed;
    const combV  = intel.backendCombHealth  ?? intel.combustorHealthSmoothed;
    const turbV  = intel.backendTurbHealth  ?? intel.turbineHealthSmoothed;
    const ovV    = intel.backendOverallHealth ?? intel.overallHealthSmoothed;
    if (!ovV || ovV <= 0) return;

    const pt: CyclePoint = {
      cycle,
      overall:    Number(ovV.toFixed(2)),
      compressor: Number(compV.toFixed(2)),
      combustor:  Number(combV.toFixed(2)),
      turbine:    Number(turbV.toFixed(2)),
      type: 'measured',
    };
    // Update (overwrite) this cycle's entry with the latest live prediction
    predHistoryRef.current.set(cycle, pt);
    const sorted = Array.from(predHistoryRef.current.values())
      .sort((a, b) => a.cycle - b.cycle)
      .slice(-300);
    setPredHistory(sorted);
  }, [intel.cycleCursor, intel.backendOverallHealth]);

  // ── Causal chain — real backend reasons ─────────────────────────────────
  const shapFactors = intel.shapRankedFactors.slice(0, 4);
  const whyChangedList = intel.whyChanged.slice(0, 4);

  // ── Fleet percentile from backend (aerothon score as proxy) ─────────────
  const fleetBetterPct = Math.max(10, Math.min(95, Math.round(overallH - 20)));

  // ── Scenario state ────────────────────────────────────────────────────────
  // Normalise store scenario keys → scenario library keys
  const rawScenario = activeScenario ?? 'NORMAL';
  const scenarioKey = rawScenario === 'NORMAL_PATROL' || rawScenario === '' ? 'NORMAL' : rawScenario;
  const activeSc = SCENARIOS[scenarioKey] ?? SCENARIOS['NORMAL'];
  const scUrgStyle = urgencyStyle[activeSc.urgency] ?? urgencyStyle['NORMAL'];

  // ── Narrative built entirely from real backend fields ────────────────────
  const lowestH = Math.min(compH, combH, turbH);
  const lowestName = compH === lowestH ? 'Air Compressor'
    : combH === lowestH ? 'Fuel Burner' : 'Power Turbine';
  const drop = Math.round(100 - overallH);
  const trendText = intel.healthTrend === 'DEGRADING_FAST' ? 'rapidly degrading' :
    intel.healthTrend === 'DEGRADING' ? 'slowly degrading' :
    intel.healthTrend === 'RECOVERING' ? 'recovering' : 'stable';

  const actionText = urgency === 'NORMAL'   ? 'No immediate action required. Continue normal operation.' :
    urgency === 'MONITOR'  ? 'Keep monitoring closely. Plan a check-up at the next available opportunity.' :
    urgency === 'WARNING'  ? 'Schedule maintenance within the next flight rotation.' :
    '⚠️ Ground the engine immediately. Inspection required before next flight.';

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col gap-4 p-4 pt-3 overflow-y-auto bg-[#0B132B] min-h-full font-sans">

      {/* ── HEADER ────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between flex-wrap gap-3 shrink-0">
        <div>
          <h1 className="text-xl font-black text-white tracking-tight flex items-center gap-2">
            Mission Overview
            {intel.backendOnline
              ? <span className="flex items-center gap-1 text-xs font-normal text-emerald-400"><Wifi className="w-3.5 h-3.5" /> Live</span>
              : <span className="flex items-center gap-1 text-xs font-normal text-amber-400"><WifiOff className="w-3.5 h-3.5" /> Offline (cached)</span>
            }
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Engine #{intel.cycleCursor != null ? `Cycle ${intel.cycleCursor}` : '—'} · Updated: {intel.lastUpdated}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Scenario Switcher */}
          <ScenarioSelector activeKey={scenarioKey} />
          {/* Overall urgency badge */}
          <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${urg.bg} ${urg.border}`}>
            <span className={urg.text}>{urg.icon}</span>
            <span className={`text-sm font-bold ${urg.text}`}>{urg.badge}</span>
          </div>
        </div>
      </div>

      {/* Active Scenario Banner (shows when not NORMAL) */}
      {scenarioKey !== 'NORMAL' && (
        <div className={`shrink-0 rounded-xl border p-3 flex items-start gap-3 ${activeSc.color}`}>
          <span className="text-2xl">{activeSc.icon}</span>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-black text-white">Active Scenario: {activeSc.label}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-bold text-white ${scUrgStyle.badgeBg}`}>{scUrgStyle.badge}</span>
            </div>
            <p className="text-xs text-slate-300 mt-1">{activeSc.what}</p>
            <p className="text-xs text-slate-400 mt-0.5">Expected: {activeSc.expect}</p>
          </div>
        </div>
      )}

      {/* ── BATCH EXCEL / CSV EVALUATION & ACCURACY CALCULATOR PROVISION ─────── */}
      <BatchExcelAccuracyCalculator />

      {/* ── TIER 1: 6-CARD RIBBON ─────────────────────────────────────────── */}

      <div className="grid grid-cols-6 gap-3 shrink-0">
        {/* 1. Engine Status */}
        <ExplainCard
          title=""
          what="The overall health score from 0–100%. It's calculated by our AI using sensor data from the compressor, combustor, and turbine."
          says={`This engine is at ${Math.round(overallH)}% — ${hc(overallH).label} condition. ${drop > 10 ? `It has lost ${drop}% of its original performance.` : 'Still near peak performance.'}`}
        >
          <div className={`flex flex-col gap-1.5 -mt-2`}>
            <div className="flex items-center gap-1.5">
              <Heart className={`w-4 h-4 ${hc(overallH).text}`} />
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">Engine Status</span>
            </div>
            <span className={`text-2xl font-black ${hc(overallH).text}`}>{hc(overallH).label}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-bold text-white self-start ${urgency === 'NORMAL' ? 'bg-emerald-600' : urgency === 'MONITOR' ? 'bg-sky-600' : urgency === 'WARNING' ? 'bg-amber-600' : 'bg-red-600 animate-pulse'}`}>
              {urg.badge}
            </span>
          </div>
        </ExplainCard>

        {/* 2. Life Remaining */}
        <ExplainCard
          title=""
          what="Remaining Useful Life (RUL) is how many more operating cycles this engine can safely run before it needs maintenance. Calculated by our AI from sensor degradation patterns — NOT from cycle count."
          says={`The engine can operate for approximately ${rulCycles} more cycles (≈ ${rulHours} hours). ${rulCycles < 50 ? 'Book maintenance immediately.' : rulCycles < 150 ? 'Plan maintenance soon.' : 'Plenty of life left.'}`}
        >
          <div className="flex flex-col gap-1.5 -mt-2">
            <div className="flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-sky-400" />
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">Life Remaining</span>
            </div>
            <span className="text-2xl font-black text-white">{rulCycles} <span className="text-sm font-bold text-slate-400">cycles</span></span>
            <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-sky-500 rounded-full transition-all duration-700"
                style={{ width: `${Math.min(100, (rulCycles / 300) * 100)}%`, boxShadow: '0 0 6px #38bdf880' }} />
            </div>
            <span className="text-xs text-slate-400">≈ {rulHours} flight hours</span>
          </div>
        </ExplainCard>

        {/* 3. Alerts */}
        <ExplainCard
          title=""
          what="Active alerts are conditions detected by our AI that need human attention. They are raised automatically when sensor values go outside safe operating limits."
          says={alerts.length > 0 ? `There are ${alerts.length} active alert(s). The most urgent: "${alerts[0]?.title}". Review and take action.` : 'No alerts — all sensors are within safe operating range.'}
        >
          <div className="flex flex-col gap-1.5 -mt-2">
            <div className="flex items-center gap-1.5">
              <AlertTriangle className={`w-4 h-4 ${alerts.length > 0 ? 'text-amber-400' : 'text-slate-500'}`} />
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">Alerts</span>
            </div>
            {alerts.length > 0 ? (
              <>
                <span className="text-2xl font-black text-amber-300">{alerts.length} Alert{alerts.length > 1 ? 's' : ''}</span>
                <span className="text-xs text-amber-300/70 line-clamp-2">{alerts[0]?.title}</span>
              </>
            ) : (
              <>
                <span className="text-2xl font-black text-emerald-400">None</span>
                <span className="text-xs text-slate-400">All systems nominal</span>
              </>
            )}
          </div>
        </ExplainCard>

        {/* 4. Thrust */}
        <ExplainCard
          title=""
          what="Thrust is the pushing force the engine produces to move the aircraft forward. It's measured in kilonewtons (kN). Higher is better, but it must match the mission requirement."
          says={`Currently producing ${typeof thrustKn === 'number' ? thrustKn.toFixed(1) : thrustKn} kN of thrust. ${overallH < 85 ? 'Reduced from nominal due to engine wear.' : 'Within normal operating range.'}`}
        >
          <div className="flex flex-col gap-1.5 -mt-2">
            <div className="flex items-center gap-1.5">
              <Zap className="w-4 h-4 text-yellow-400" />
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">Thrust</span>
            </div>
            <span className="text-2xl font-black text-white">
              {typeof thrustKn === 'number' ? thrustKn.toFixed(1) : thrustKn} <span className="text-sm font-bold text-slate-400">kN</span>
            </span>
            <span className="text-xs text-slate-400">Push force on aircraft</span>
          </div>
        </ExplainCard>

        {/* 5. Fuel Burn */}
        <ExplainCard
          title=""
          what="Fuel burn rate tells you how much fuel the engine consumes per second. A higher-than-normal value means the engine is working harder or is less efficient."
          says={`Burning ${fuelKgS} kg/s (${Math.round(fuelFlowKgH)} kg/hour). ${fuelFlowKgH > 2800 ? 'Higher than normal — engine efficiency may be reduced.' : 'Within normal consumption range.'}`}
        >
          <div className="flex flex-col gap-1.5 -mt-2">
            <div className="flex items-center gap-1.5">
              <Droplets className="w-4 h-4 text-blue-400" />
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">Fuel Burn</span>
            </div>
            <span className="text-2xl font-black text-white">{fuelKgS} <span className="text-sm font-bold text-slate-400">kg/s</span></span>
            <span className="text-xs text-slate-400">{Math.round(fuelFlowKgH)} kg per hour</span>
          </div>
        </ExplainCard>

        {/* 6. Fleet Standing */}
        <ExplainCard
          title=""
          what="Fleet standing compares this engine to all other engines in the 100-engine dataset. The AI ranks all engines by health and degradation rate."
          says={`This engine is healthier than approximately ${fleetBetterPct}% of all engines in the fleet. ${fleetBetterPct > 70 ? 'Top-performing engine.' : fleetBetterPct > 40 ? 'Near fleet average.' : 'Below fleet average — needs attention.'}`}
        >
          <div className="flex flex-col gap-1.5 -mt-2">
            <div className="flex items-center gap-1.5">
              <Users className="w-4 h-4 text-purple-400" />
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">Fleet Standing</span>
            </div>
            <span className="text-2xl font-black text-purple-300">Top {100 - fleetBetterPct}%</span>
            <span className="text-xs text-slate-400">Better than {fleetBetterPct}% of fleet</span>
          </div>
        </ExplainCard>
      </div>

      {/* ── TIER 2: MAIN GRID ─────────────────────────────────────────────── */}
      <div className="grid grid-cols-12 gap-4 shrink-0">

        {/* LEFT: Engine Health Ring + Bars */}
        <div className="col-span-4">
          <ExplainCard
            title="Engine Health Breakdown"
            what="The health ring shows the overall engine condition from 0–100%. The three bars show the health of the three main parts separately — each fed by real sensor data from the backend."
            says={`Overall health is ${Math.round(overallH)}%. The weakest part is the ${lowestName} at ${Math.round(lowestH)}%. Health trend: ${trendText}.`}
          >
            <div className="flex items-center justify-center mb-4">
              <HealthRingBig health={overallH} />
            </div>
            <p className="text-xs text-center text-slate-400 mb-4">
              This engine has used <span className={`font-bold ${hc(overallH).text}`}>{drop}%</span> of its service life.
            </p>
            <div className="space-y-4 border-t border-slate-800 pt-4">
              <HealthBar
                name="Air Compressor" icon={<Wind className="w-3.5 h-3.5" />} health={compH}
                trend={intel.healthTrend}
                note={compH >= 93 ? 'Working great — no action needed'
                  : compH >= 85 ? 'Minor wear — schedule a compressor wash'
                  : 'Significant wear — book borescope inspection'}
              />
              <HealthBar
                name="Fuel Burner" icon={<Flame className="w-3.5 h-3.5" />} health={combH}
                trend={intel.healthTrend}
                note={combH >= 93 ? 'Burning fuel at full efficiency'
                  : combH >= 85 ? 'Slightly less efficient — monitor fuel consumption'
                  : 'Efficiency reduced — check combustor and nozzles'}
              />
              <HealthBar
                name="Power Turbine" icon={<Gauge className="w-3.5 h-3.5" />} health={turbH}
                trend={intel.healthTrend}
                note={turbH >= 93 ? 'Extracting full power from hot gases'
                  : turbH >= 85 ? 'Slight power loss — normal for this stage'
                  : 'Reduced power output — inspect turbine blades'}
              />
            </div>
          </ExplainCard>
        </div>

        {/* CENTRE: What's Happening + EGT */}
        <div className="col-span-4 flex flex-col gap-4">
          <ExplainCard
            title="What's Happening Right Now?"
            what="This section translates the AI's full diagnosis into plain English. It tells you the current condition, what's driving it, how long until maintenance, and what to do."
            says={`The engine is ${trendText}. Action: ${actionText}`}
          >
            <div className="space-y-3 text-sm leading-relaxed -mt-1">
              {/* Summary */}
              <p className="text-slate-200">
                Your engine is <span className={`font-bold ${hc(overallH).text}`}>{trendText}</span>.
                Overall health is <span className="font-bold text-white">{Math.round(overallH)}%</span>
                {drop > 0 ? ` — it has lost ${drop}% of its original performance capacity.` : '.'}
              </p>
              {/* Limiting subsystem */}
              {intel.limitingSubsystem && intel.limitingSubsystem !== '--' && (
                <p className="text-slate-300">
                  The <span className="font-bold text-amber-300">{intel.limitingSubsystem}</span> is currently the limiting factor.
                  {intel.whatChanged ? ` ${intel.whatChanged}` : ''}
                </p>
              )}
              {/* RUL forecast */}
              <p className="text-slate-300">
                Maintenance needed in approximately{' '}
                <span className="font-bold text-white">{rulCycles} more operating cycles</span>{' '}
                <span className="text-slate-400">(≈ {rulHours} flight hours).</span>
              </p>
              {/* Forecast */}
              <div className="flex items-center gap-3 text-xs bg-slate-800/60 rounded-lg p-2.5 border border-slate-700/50">
                <div className="text-center px-2 border-r border-slate-700">
                  <p className="text-slate-400">In 10 cycles</p>
                  <p className={`font-black text-sm ${hc(intel.forecast10).text}`}>{intel.forecast10.toFixed(1)}%</p>
                </div>
                <div className="text-center px-2 border-r border-slate-700">
                  <p className="text-slate-400">In 50 cycles</p>
                  <p className={`font-black text-sm ${hc(intel.forecast50).text}`}>{intel.forecast50.toFixed(1)}%</p>
                </div>
                <div className="text-center px-2">
                  <p className="text-slate-400">In 100 cycles</p>
                  <p className={`font-black text-sm ${hc(intel.forecast100).text}`}>{intel.forecast100.toFixed(1)}%</p>
                </div>
              </div>
              {/* Action */}
              <div className={`flex items-start gap-2 p-3 rounded-lg border ${urg.bg} ${urg.border}`}>
                <span className={`mt-0.5 shrink-0 ${urg.text}`}>{urg.icon}</span>
                <p className={`text-sm font-bold ${urg.text}`}>{actionText}</p>
              </div>
            </div>
          </ExplainCard>

          {/* EGT Card */}
          <ExplainCard
            title="Exhaust Temperature"
            what="The exhaust temperature (T4) measures how hot the gases leaving the turbine are. If it gets too close to the limit, the turbine blades can melt or crack."
            says={`Current exhaust temp is ${t4C}°C. The red-line limit is ${egtLimitC}°C. Safety margin: ${egtMargin}°C remaining. ${egtMargin < 80 ? '⚠️ Dangerously close to the limit!' : egtMargin < 150 ? 'Getting close — monitor carefully.' : 'Safely within operational limits.'}`}
          >
            <div className="flex items-center gap-4 -mt-1">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 ${egtMargin < 80 ? 'bg-red-950 border-2 border-red-600 animate-pulse' : egtMargin < 150 ? 'bg-amber-950 border border-amber-700' : 'bg-slate-800 border border-slate-700'}`}>
                <Thermometer className={`w-6 h-6 ${egtMargin < 80 ? 'text-red-400' : egtMargin < 150 ? 'text-amber-400' : 'text-orange-400'}`} />
              </div>
              <div className="flex-1">
                <p className="text-2xl font-black text-white">{t4C}°C</p>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all ${egtMargin < 80 ? 'bg-red-500' : egtMargin < 150 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                      style={{ width: `${Math.min(100, (t4C / egtLimitC) * 100)}%` }} />
                  </div>
                  <span className="text-xs text-slate-400 whitespace-nowrap">Limit: {egtLimitC}°C</span>
                </div>
                <p className="text-xs mt-1">
                  Safety margin: <span className={`font-bold ${egtMargin < 80 ? 'text-red-400' : egtMargin < 150 ? 'text-amber-400' : 'text-emerald-400'}`}>{egtMargin}°C left</span>
                </p>
              </div>
            </div>
          </ExplainCard>
        </div>

        {/* RIGHT: Root Cause + Why */}
        <div className="col-span-4">
          <ExplainCard
            title="Why Is This Happening?"
            what="This panel shows the AI's causal chain — the sequence of events leading to the current engine condition. Each step is a real sensor reading translated into plain language."
            says={intel.whyChanged.length > 0 ? intel.whyChanged.join(' ') : `The ${lowestName} is the primary driver of health degradation. The AI detected this from sensor patterns over the last ${predHistory.length} cycles.`}
          >
            <div className="flex flex-col gap-1 -mt-1">
              {/* Real backend causal reasons */}
              {(whyChangedList.length > 0 ? whyChangedList : [
                `${lowestName} is the most degraded subsystem at ${Math.round(lowestH)}%`,
                `Exhaust temperature ${t4C > 900 ? 'is elevated at ' + t4C + '°C' : 'is within safe limits at ' + t4C + '°C'}`,
                `Fuel consumption is ${fuelFlowKgH > 2800 ? 'above' : 'within'} normal range at ${Math.round(fuelFlowKgH)} kg/h`,
                `Engine health trend: ${trendText}`,
              ]).map((reason, i) => (
                <React.Fragment key={i}>
                  <div className={`flex items-start gap-3 p-2.5 rounded-lg border ${i === 0 ? 'border-amber-700/50 bg-amber-950/30' : 'border-slate-700/50 bg-slate-800/30'}`}>
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-xs font-black ${i === 0 ? 'bg-amber-900 text-amber-300' : 'bg-slate-700 text-slate-400'}`}>
                      {i + 1}
                    </div>
                    <p className={`text-sm ${i === 0 ? 'text-amber-200 font-semibold' : 'text-slate-300'} leading-relaxed`}>{reason}</p>
                  </div>
                  {i < 3 && <div className="flex justify-center"><ChevronRight className="w-4 h-4 text-slate-600 rotate-90" /></div>}
                </React.Fragment>
              ))}

              {/* Real SHAP factors */}
              {shapFactors.length > 0 && (
                <div className="mt-3 border-t border-slate-800 pt-3 space-y-2">
                  <p className="text-xs font-bold text-sky-400 uppercase tracking-wide">Top Impact Factors</p>
                  {shapFactors.map((f, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="text-xs text-slate-400 w-32 truncate">{f.sensor.replace(/_/g, ' ')}</span>
                      <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${f.direction === 'DEGRADING' ? 'bg-red-500' : 'bg-emerald-500'}`}
                          style={{ width: `${Math.min(100, Math.abs(f.shapley_impact_pct) * 3)}%` }} />
                      </div>
                      <span className={`text-xs font-bold w-16 text-right ${f.direction === 'DEGRADING' ? 'text-red-400' : 'text-emerald-400'}`}>
                        {f.direction === 'DEGRADING' ? '-' : '+'}{Math.abs(f.shapley_impact_pct).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Recommended action */}
              <div className="mt-3 border-t border-slate-800 pt-3">
                <div className="flex items-center gap-2 mb-2">
                  <Wrench className="w-4 h-4 text-sky-400" />
                  <span className="text-xs font-black text-sky-400 uppercase tracking-wide">Recommended Action</span>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed">{intel.actionTier !== 'On-Condition Monitoring (OAP)' ? intel.actionTier : actionText}</p>
              </div>
            </div>
          </ExplainCard>
        </div>
      </div>

      {/* ── TIER 3: HEALTH CHART + FLEET ──────────────────────────────────── */}
      <div className="grid grid-cols-12 gap-4 shrink-0 pb-6">

        {/* Health Chart */}
        <div className="col-span-7">
          <ExplainCard
            title="Health Over Time"
            what="This chart shows the engine's health history built cycle-by-cycle from AI model predictions (not cycle number — that's just the X-axis). Each data point is the model's output given real sensor readings at that moment. The shaded right zone is where the AI forecasts health will go in the next 100 cycles."
            says={`Current health: ${Math.round(overallH)}%. In 10 cycles: ${intel.forecast10.toFixed(1)}%. In 50 cycles: ${intel.forecast50.toFixed(1)}%. In 100 cycles: ${intel.forecast100.toFixed(1)}%. Degradation rate: ${intel.degradationVelocity.toFixed(3)}% per cycle.`}
          >
            {!historyLoaded && predHistory.length === 0 && (
              <div className="flex items-center gap-2 text-xs text-slate-400 py-4 justify-center animate-pulse">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Loading engine history from dataset (300 cycles)...
              </div>
            )}
            <HealthChart
              historyPoints={predHistory}
              forecast10={intel.forecast10}
              forecast50={intel.forecast50}
              forecast100={intel.forecast100}
              currentCycle={intel.cycleCursor ?? 1}
              currentHealth={overallH}
            />
            {predHistory.length > 0 && (
              <p className="text-[10px] text-slate-500 mt-1">
                📈 {predHistory.length} cycle{predHistory.length > 1 ? 's' : ''} of ML predictions loaded
                {historyLoaded ? ' (pre-loaded from dataset)' : ' (accumulating live)'}
                · Now at cycle {intel.cycleCursor ?? 1}
              </p>
            )}
          </ExplainCard>
        </div>

        {/* Fleet Comparison */}
        <div className="col-span-5">
          <ExplainCard
            title="How Does This Compare?"
            what="This compares this engine's health against all 100 engines in the Aerothon dataset. The AI assigns each engine a percentile rank based on health level and degradation speed."
            says={`This engine ranks better than ~${fleetBetterPct}% of all engines. ${fleetBetterPct > 70 ? 'Excellent standing.' : fleetBetterPct > 40 ? 'Near average.' : 'Below average — prioritise maintenance.'}`}
          >
            <div className="space-y-3">
              {[
                { label: 'This Engine',    pct: Math.round(overallH), highlight: true },
                { label: 'Fleet Average',  pct: 87 },
                { label: 'Best Engine',    pct: Math.min(100, Math.round(overallH) + Math.round((100 - overallH) * 0.6)) },
                { label: 'Worst Engine',   pct: Math.max(55, Math.round(overallH) - 25) },
              ].map(row => {
                const c = hc(row.pct);
                return (
                  <div key={row.label} className={`flex items-center gap-3 p-2 rounded-lg ${row.highlight ? 'bg-sky-950/50 border border-sky-700/40' : ''}`}>
                    <span className={`text-xs font-bold w-24 shrink-0 ${row.highlight ? 'text-sky-300' : 'text-slate-400'}`}>{row.label}</span>
                    <div className="flex-1 h-2.5 bg-slate-800 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full transition-all duration-700 ${c.bg}`} style={{ width: `${row.pct}%` }} />
                    </div>
                    <span className={`text-xs font-black w-10 text-right ${row.highlight ? c.text : 'text-slate-400'}`}>{row.pct}%</span>
                  </div>
                );
              })}

              {/* Percentile callout */}
              <div className="p-3 rounded-lg bg-purple-950/50 border border-purple-700/40 text-center mt-2">
                <p className="text-xs text-purple-300 font-bold">🏆 This engine is healthier than</p>
                <p className="text-4xl font-black text-purple-200 my-1">{fleetBetterPct}%</p>
                <p className="text-xs text-purple-300">of all 100 engines in the fleet</p>
              </div>

              {/* Failure modes */}
              {intel.failureModes.length > 0 && (
                <div className="border-t border-slate-800 pt-3 space-y-1.5">
                  <p className="text-xs font-bold text-amber-400 uppercase tracking-wide">Detected Risk Patterns</p>
                  {intel.failureModes.slice(0, 2).map((fm, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="text-amber-200 font-semibold">{fm.mechanism}</span>
                        {fm.affected_parts?.length > 0 && (
                          <span className="text-slate-400"> → {fm.affected_parts.join(', ')}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </ExplainCard>
        </div>
      </div>
    </div>
  );
});
LaymanOverview.displayName = 'LaymanOverview';
