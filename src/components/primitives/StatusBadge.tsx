import React from 'react';
import { statusColor } from '@/utils';

export interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = React.memo(({ status, size = 'sm', className = '' }) => {
  const cols = statusColor(status);
  const padding = size === 'sm' ? 'px-1.5 py-0.5 text-[9px]' : 'px-2 py-0.5 text-[10px]';
  return (
    <span className={`inline-flex items-center justify-center font-bold font-mono uppercase tracking-wider rounded-xs border shadow-2xs ${padding} ${cols} ${className}`}>
      {status}
    </span>
  );
});
StatusBadge.displayName = 'StatusBadge';
