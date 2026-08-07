import React from 'react';

export interface InspectorRowProps {
  label: string;
  val: string | number;
  unit?: string;
  active?: boolean;
  onClick?: () => void;
  className?: string;
  statusColor?: string;
}

export const InspectorRow: React.FC<InspectorRowProps> = React.memo(({ label, val, unit = '', active = false, onClick, className = '', statusColor }) => (
  <div
    onClick={onClick}
    className={`flex items-center justify-between py-1.5 px-2.5 rounded-sm font-mono text-xs transition-all ${onClick ? 'cursor-pointer' : ''} ${
      active
        ? 'bg-sky-950/80 border-l-2 border-sky-400 font-bold text-white shadow-sm'
        : 'hover:bg-slate-800/80 text-slate-300'
    } ${className}`}
  >
    <span className={active ? 'text-white font-bold' : 'text-slate-300 font-medium'}>{label}</span>
    <div className="flex items-center gap-1.5">
      <span className={active ? 'text-sky-300 font-bold text-sm' : 'text-white font-bold'}>
        {val} <span className="text-[10px] font-normal text-sky-400">{unit}</span>
      </span>
      {statusColor && <span className={`w-2 h-2 rounded-full ${statusColor}`} />}
    </div>
  </div>
));
InspectorRow.displayName = 'InspectorRow';
