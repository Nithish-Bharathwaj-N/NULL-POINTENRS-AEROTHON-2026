import React from 'react';
import { StatusBadge } from '@/components';

interface MetricItem {
  label: string;
  val: string;
  sub: string;
  status: string;
}

interface FleetSummaryRibbonProps {
  metrics: MetricItem[];
}

export const FleetSummaryRibbon: React.FC<FleetSummaryRibbonProps> = React.memo(({ metrics }) => (
  <div className="grid grid-cols-6 gap-2 bg-slate-900/90 text-slate-100 p-2 rounded-sm border border-slate-800 shadow-md font-mono select-none shrink-0">
    {metrics.map((m, idx) => (
      <div
        key={idx}
        className="flex flex-col justify-between bg-slate-950/80 border border-slate-800 rounded-xs p-2.5 hover:border-sky-500/60 hover:bg-slate-900 transition-all shadow-sm relative overflow-hidden group"
      >
        <div className="flex items-center justify-between gap-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-none truncate group-hover:text-sky-300 transition-colors">
            {m.label}
          </span>
          <StatusBadge status={m.status} size="sm" />
        </div>
        <div className="mt-1.5">
          <div className="text-base font-bold text-white tracking-tight leading-none">
            {m.val}
          </div>
          <div className="text-[10px] text-sky-400 font-bold truncate mt-1 leading-none">
            {m.sub}
          </div>
        </div>
      </div>
    ))}
  </div>
));
FleetSummaryRibbon.displayName = 'FleetSummaryRibbon';
