import React from 'react';
import { healthColor } from '@/utils';

export interface RingProps {
  pct: number;
  color?: string;
  size?: number;
  stroke?: number;
  label?: string;
}

export const Ring: React.FC<RingProps> = React.memo(({ pct, color = '#00A86B', size = 44, stroke = 4, label }) => {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (pct / 100) * c;
  return (
    <div className="relative inline-flex items-center justify-center font-mono select-none shrink-0" style={{ width: size, height: size }}>
      <svg className="w-full h-full -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="#1E293B" strokeWidth={stroke} fill="none" />
        <circle cx={size / 2} cy={size / 2} r={r} stroke={color} strokeWidth={stroke} strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round" fill="none" />
      </svg>
      <span className="absolute text-[10px] font-extrabold text-white tracking-tighter drop-shadow-md leading-none">
        {label || `${Math.round(pct)}%`}
      </span>
    </div>
  );
});
Ring.displayName = 'Ring';

export interface HealthRingProps {
  health: number;
  size?: number;
  stroke?: number;
  label?: string;
}

export const HealthRing: React.FC<HealthRingProps> = React.memo(({ health, size = 44, stroke = 4, label }) => {
  const col = healthColor(health);
  return <Ring pct={health} color={col} size={size} stroke={stroke} label={label} />;
});
HealthRing.displayName = 'HealthRing';
