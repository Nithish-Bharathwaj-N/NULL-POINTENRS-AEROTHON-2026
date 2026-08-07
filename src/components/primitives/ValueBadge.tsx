import React from 'react';
import { StatusBadge } from './StatusBadge';

export interface ValueBadgeProps {
  label: string;
  value: string | number;
  unit?: string;
  status?: string;
}

export const ValueBadge: React.FC<ValueBadgeProps> = React.memo(({ label, value, unit = '', status }) => (
  <div className="flex flex-col bg-slate-950/80 border border-slate-800 rounded-sm px-2.5 py-1.5 shadow-sm font-mono">
    <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">{label}</span>
    <div className="flex items-baseline justify-between gap-1 mt-0.5">
      <div className="text-xs font-bold text-white">
        {value} <span className="text-[10px] font-normal text-sky-400">{unit}</span>
      </div>
      {status && <StatusBadge status={status} size="sm" />}
    </div>
  </div>
));
ValueBadge.displayName = 'ValueBadge';
