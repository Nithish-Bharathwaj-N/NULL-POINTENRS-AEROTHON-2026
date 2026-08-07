import * as React from 'react';
import { cn } from '@/lib/utils';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'outline' | 'secondary' | 'destructive' | 'nominal' | 'warning' | 'critical';
}

export function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  const baseStyles = 'inline-flex items-center rounded-xs border px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider font-mono transition-colors';
  const variants = {
    default: 'border-transparent bg-slate-900 text-white hover:bg-slate-800',
    outline: 'text-slate-700 border-slate-300',
    secondary: 'border-transparent bg-slate-100 text-slate-900 hover:bg-slate-200',
    destructive: 'border-transparent bg-red-600 text-white hover:bg-red-700',
    nominal: 'border-emerald-700 bg-emerald-600 text-white shadow-2xs',
    warning: 'border-amber-600 bg-amber-500 text-white shadow-2xs',
    critical: 'border-red-600 bg-red-500 text-white shadow-2xs animate-pulse',
  };
  return <div className={cn(baseStyles, variants[variant], className)} {...props} />;
}
