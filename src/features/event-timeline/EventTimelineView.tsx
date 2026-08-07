import React, { useState, useRef, useEffect } from 'react';
import { Panel } from '@/components';
import { Clock, Filter, Radio } from 'lucide-react';
import { useMissionStore } from '@/stores/useMissionStore';
import { useUiStore } from '@/stores';
import { TimelineEvent } from '@/types';
import { missionPlaybackEngine } from '@/services/missionPlaybackEngine';

type CatFilter = 'ALL' | 'PROPULSION' | 'AVIONICS' | 'THERMAL' | 'ELECTRICAL' | 'FLIGHT_CONTROL';

export const EventTimelineView: React.FC = React.memo(() => {
  const timelineEvents = useMissionStore((s) => s.timelineEvents);
  const missionTimeSec = useMissionStore((s) => s.missionTimeSec);
  const missionPhase = useMissionStore((s) => s.missionPhase);
  const [filter, setFilter] = useState<CatFilter>('ALL');
  const [autoScroll, setAutoScroll] = useState(true);
  const listRef = useRef<HTMLDivElement>(null);
  const { setSelectedStageRef } = useUiStore();

  // Auto-scroll to top (newest events) when new events arrive
  useEffect(() => {
    if (autoScroll && listRef.current) {
      listRef.current.scrollTop = 0;
    }
  }, [timelineEvents.length, autoScroll]);

  const filtered = timelineEvents.filter((e) => filter === 'ALL' || e.category === filter);

  const cats: CatFilter[] = ['ALL', 'PROPULSION', 'AVIONICS', 'THERMAL', 'ELECTRICAL', 'FLIGHT_CONTROL'];

  const critCount = timelineEvents.filter((e) => e.severity === 'CRITICAL').length;
  const warnCount = timelineEvents.filter((e) => e.severity === 'WARNING').length;

  return (
    <div className="p-3 h-full overflow-y-auto space-y-3 bg-[#0B132B]">

      {/* ── Live Mission Status ───────────────────────────────────────────────── */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Mission Elapsed', val: (() => { const h = Math.floor(missionTimeSec/3600); const m = Math.floor((missionTimeSec%3600)/60); const s = Math.floor(missionTimeSec%60); return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`; })(), sub: 'T+ elapsed time', color: 'text-sky-300' },
          { label: 'Active Phase', val: missionPhase.split(' ')[0], sub: missionPhase, color: 'text-amber-400' },
          { label: 'Critical Events', val: String(critCount), sub: `${warnCount} Warnings Active`, color: 'text-red-400' },
          { label: 'Total Events', val: String(timelineEvents.length), sub: 'Recorded this sortie', color: 'text-white' },
        ].map((m, i) => (
          <div key={i} className="p-3 bg-slate-950/80 border border-slate-800 rounded-sm shadow-sm font-mono">
            <div className="text-[9px] font-bold uppercase tracking-wider text-slate-400">{m.label}</div>
            <div className={`text-lg font-bold mt-0.5 ${m.color}`}>{m.val}</div>
            <div className="text-[9px] text-slate-400 truncate">{m.sub}</div>
          </div>
        ))}
      </div>

      {/* ── Category Filter & Auto-Scroll ─────────────────────────────────────── */}
      <div className="flex items-center gap-2 font-mono text-xs">
        <Filter className="w-3.5 h-3.5 text-slate-400 shrink-0" />
        {cats.map((cat) => (
          <button key={cat} onClick={() => setFilter(cat)}
            className={`px-2 py-0.5 rounded-xs font-bold uppercase text-[10px] tracking-wider border transition-all cursor-pointer ${
              filter === cat ? 'bg-sky-600 text-white border-sky-500' : 'bg-slate-950 text-slate-300 border-slate-800 hover:bg-slate-900'
            }`}>{cat}</button>
        ))}
        <div className="ml-auto flex items-center gap-2">
          <label className="flex items-center gap-1.5 cursor-pointer text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            <input type="checkbox" checked={autoScroll} onChange={(e) => setAutoScroll(e.target.checked)}
              className="accent-sky-500 w-3 h-3" />
            AUTO-SCROLL
          </label>
          <span className="text-slate-400 text-[10px]">{filtered.length} events</span>
        </div>
      </div>

      {/* ── Live Event Feed ────────────────────────────────────────────────────── */}
      <Panel title={`Live Mission Event Log — ${filtered.length} Events (Auto-updating)`} icon={Radio}
        right={
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[9px] font-mono font-bold text-emerald-400 uppercase">LIVE FEED</span>
          </div>
        }
      >
        <div ref={listRef} className="space-y-1.5 max-h-[500px] overflow-y-auto pr-1 font-mono text-xs">
          {filtered.map((ev: TimelineEvent) => {
            const isCrit = ev.severity === 'CRITICAL';
            const isWarn = ev.severity === 'WARNING';
            const h = Math.floor(ev.timeSec / 3600);
            const m = Math.floor((ev.timeSec % 3600) / 60);
            const s = Math.floor(ev.timeSec % 60);
            const tStr = `T+${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
            return (
              <div
                key={ev.id}
                className={`flex items-start gap-2.5 p-2 rounded-xs border transition-colors cursor-pointer group ${
                  isCrit ? 'bg-red-950/80 border-red-800 hover:border-red-600' :
                  isWarn ? 'bg-amber-950/80 border-amber-800 hover:border-amber-600' :
                  'bg-slate-950/80 border-slate-800 hover:border-sky-500'
                }`}
                onClick={() => {
                  if (ev.subsystemRef) setSelectedStageRef(ev.subsystemRef);
                  missionPlaybackEngine.seek(ev.timeSec);
                }}
              >
                {/* Severity LED */}
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 mt-1.5 ${isCrit ? 'bg-red-500 animate-pulse' : isWarn ? 'bg-amber-500' : 'bg-emerald-500'}`} />

                {/* Time & Category */}
                <div className="shrink-0 w-24">
                  <div className="text-[9px] text-slate-400 font-bold">{tStr}</div>
                  <div className="text-[9px] font-bold text-sky-400 uppercase tracking-wider">{ev.category}</div>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className={`font-bold text-[11px] ${isCrit ? 'text-red-300' : isWarn ? 'text-amber-300' : 'text-white'}`}>{ev.title}</div>
                  <div className="text-[10px] text-slate-400 truncate">{ev.description}</div>
                </div>

                {/* Status badge */}
                <span className={`shrink-0 px-1.5 py-0.5 rounded-xs text-[9px] font-bold uppercase self-start ${
                  isCrit ? 'bg-red-600 text-white' : isWarn ? 'bg-amber-500 text-white' : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                }`}>{ev.severity}</span>
              </div>
            );
          })}
          {filtered.length === 0 && (
            <div className="text-center py-6 text-slate-400 text-[11px]">No events for selected category.</div>
          )}
        </div>
      </Panel>

      {/* ── Timeline Activity Chart ─────────────────────────────────────────── */}
      <Panel title="Event Distribution by Category" icon={Clock}>
        <div className="grid grid-cols-2 gap-4 font-mono text-xs">
          {(['PROPULSION','AVIONICS','THERMAL','ELECTRICAL','FLIGHT_CONTROL','SATCOM','ENVIRONMENTAL','WEAPONS'] as const).map((cat) => {
            const count = timelineEvents.filter((e) => e.category === cat).length;
            const pct = timelineEvents.length > 0 ? Math.round((count / timelineEvents.length) * 100) : 0;
            const critCat = timelineEvents.filter((e) => e.category === cat && e.severity === 'CRITICAL').length;
            return (
              <div key={cat} className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-[10px] font-bold text-slate-300 uppercase">{cat}</span>
                  <span className="text-[10px] font-bold text-white">{count} events {critCat > 0 ? <span className="text-red-400">({critCat} CRIT)</span> : null}</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${critCat > 0 ? 'bg-red-500' : count > 0 ? 'bg-sky-500' : 'bg-slate-700'}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </Panel>
    </div>
  );
});
EventTimelineView.displayName = 'EventTimelineView';
