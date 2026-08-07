import React from 'react';

export interface PanelProps {
  title: string;
  icon?: React.ElementType;
  right?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  noPad?: boolean;
  highContrastHeader?: boolean;
}

export const Panel: React.FC<PanelProps> = React.memo(({ title, icon: Icon, right, children, className = '', noPad = false, highContrastHeader = false }) => (
  <div className={`bg-slate-900/90 border border-slate-800 rounded-sm shadow-md text-slate-100 flex flex-col ${className}`}>
    <div className={`px-3 py-2 flex items-center justify-between border-b border-slate-800 select-none ${highContrastHeader ? 'bg-slate-800 text-sky-400' : 'bg-slate-900/95 text-sky-400'}`}>
      <div className="flex items-center gap-1.5 font-rajdhani font-bold text-xs tracking-wider uppercase">
        {Icon && <Icon className="w-3.5 h-3.5 text-sky-400" />}
        <span>{title}</span>
      </div>
      {right && <div className="flex items-center gap-2">{right}</div>}
    </div>
    <div className={`flex-1 overflow-auto ${noPad ? '' : 'p-3'}`}>
      {children}
    </div>
  </div>
));
Panel.displayName = 'Panel';
