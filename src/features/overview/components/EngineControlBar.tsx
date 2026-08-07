// HAL Mission Control — Engine Control Bar
// Synchronized with useBackendIntelligence and FastAPI /api/v1/twin/engine/* endpoints
import React, { useCallback, useState } from 'react';
import { Power, PowerOff, Gauge, Wifi, WifiOff, AlertTriangle, Loader2 } from 'lucide-react';
import { useBackendIntelligence } from '@/hooks/useBackendIntelligence';

const getBackend = () => {
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return '/api/v1/twin';
  }
  return 'http://127.0.0.1:8000/api/v1/twin';
};

type EngineState = 'OFF' | 'STARTING' | 'IDLE' | 'RUNNING' | 'SHUTDOWN' | 'FAULT';

export const EngineControlBar: React.FC = React.memo(() => {
  const backend = useBackendIntelligence();
  const [throttle, setThrottle] = useState(74);
  const [loading, setLoading] = useState(false);

  const startEngine = useCallback(async () => {
    if (loading) return;
    setLoading(true);
    try {
      await fetch(`${BACKEND}/engine/start`, { method: 'POST' });
    } catch { /* ignore */ }
    setLoading(false);
  }, [loading]);

  const stopEngine = useCallback(async () => {
    if (loading) return;
    setLoading(true);
    try {
      await fetch(`${getBackend()}/engine/stop`, { method: 'POST' });
    } catch { /* ignore */ }
    setLoading(false);
  }, [loading]);

  const applyThrottle = useCallback(async (pct: number) => {
    setThrottle(pct);
    try {
      await fetch(`${getBackend()}/engine/throttle/${(pct / 100).toFixed(2)}`, { method: 'POST' });
    } catch { /* ignore */ }
  }, []);

  const st = (backend.engineState || 'OFF') as EngineState;
  const online = backend.backendOnline;

  const stateColor: Record<EngineState, string> = {
    OFF:      'bg-slate-700 text-slate-300',
    STARTING: 'bg-amber-600 text-white animate-pulse',
    IDLE:     'bg-sky-700 text-sky-100',
    RUNNING:  'bg-emerald-700 text-emerald-100',
    SHUTDOWN: 'bg-orange-700 text-white animate-pulse',
    FAULT:    'bg-red-700 text-white animate-pulse',
  };

  const canStart = st !== 'RUNNING';
  const canStop  = st !== 'OFF';

  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-slate-900/95 border border-slate-700 rounded-sm font-mono text-xs shrink-0 shadow-lg select-none">

      {/* Backend connectivity */}
      <div className="flex items-center gap-1.5 pr-3 border-r border-slate-700">
        {online
          ? <Wifi className="w-3.5 h-3.5 text-emerald-400" />
          : <WifiOff className="w-3.5 h-3.5 text-red-400" />}
        <span className={online ? 'text-emerald-400 font-bold' : 'text-red-400 font-bold'}>
          {online ? 'BACKEND ONLINE' : 'BACKEND OFFLINE'}
        </span>
      </div>

      {/* Engine state badge */}
      <div className="flex items-center gap-2 pr-3 border-r border-slate-700">
        <span className="text-slate-400 uppercase tracking-widest text-[9px]">Engine</span>
        <span className={`px-2 py-0.5 rounded-xs text-[10px] font-bold uppercase tracking-wider ${stateColor[st] || 'bg-slate-700 text-slate-300'}`}>
          {st}
        </span>
        {st === 'FAULT' && (
          <AlertTriangle className="w-3.5 h-3.5 text-red-400 animate-pulse" />
        )}
        {backend.cycleCursor !== null && backend.cycleCursor !== undefined && (
          <span className="text-slate-400 text-[9px] font-bold">Cycle #{backend.cycleCursor}</span>
        )}
      </div>

      {/* Start / Stop buttons */}
      <div className="flex items-center gap-2 pr-3 border-r border-slate-700">
        <button
          onClick={startEngine}
          disabled={!online || loading || st === 'RUNNING'}
          className={`flex items-center gap-1.5 px-3 py-1 rounded-xs text-[10px] font-bold uppercase tracking-wider transition-all border
            ${online && st !== 'RUNNING'
              ? 'bg-emerald-700 hover:bg-emerald-600 text-white border-emerald-500 cursor-pointer shadow-emerald-900/50 shadow-sm'
              : 'bg-slate-800 text-slate-500 border-slate-700 cursor-not-allowed opacity-50'}`}
        >
          {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Power className="w-3 h-3" />}
          Start
        </button>

        <button
          onClick={stopEngine}
          disabled={!online || loading || st === 'OFF'}
          className={`flex items-center gap-1.5 px-3 py-1 rounded-xs text-[10px] font-bold uppercase tracking-wider transition-all border
            ${online && st !== 'OFF'
              ? 'bg-red-800 hover:bg-red-700 text-white border-red-600 cursor-pointer'
              : 'bg-slate-800 text-slate-500 border-slate-700 cursor-not-allowed opacity-50'}`}
        >
          {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <PowerOff className="w-3 h-3" />}
          Stop
        </button>
      </div>

      {/* Throttle */}
      <div className="flex items-center gap-2 flex-1">
        <Gauge className="w-3.5 h-3.5 text-sky-400 shrink-0" />
        <span className="text-slate-400 text-[9px] uppercase tracking-widest shrink-0">Throttle</span>
        <input
          type="range"
          min={15}
          max={100}
          step={1}
          value={throttle}
          onChange={e => applyThrottle(Number(e.target.value))}
          disabled={st === 'OFF' || st === 'STARTING' || st === 'SHUTDOWN' || !online}
          className="flex-1 h-1.5 appearance-none bg-slate-700 rounded-full accent-sky-400 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
        />
        <span className="text-sky-300 font-bold text-xs w-8 text-right">{throttle}%</span>
      </div>

      {/* ML model status */}
      {online && (
        <div className="flex items-center gap-1.5 pl-3 border-l border-slate-700 text-[9px]">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-emerald-400 font-bold">
            6 ML Models Active · {backend.pipelineLatencyMs || backend.backendInferenceMs || '<1'}ms
          </span>
        </div>
      )}
    </div>
  );
});
EngineControlBar.displayName = 'EngineControlBar';
