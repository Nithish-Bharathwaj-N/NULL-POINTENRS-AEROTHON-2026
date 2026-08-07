import * as React from 'react';
import { cn } from '@/lib/utils';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline' | 'ghost' | 'destructive' | 'secondary' | 'hal-navy' | 'hal-green';
  size?: 'default' | 'sm' | 'lg' | 'icon';
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center rounded-sm text-xs font-semibold transition-colors focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-slate-400 disabled:pointer-events-none disabled:opacity-50 font-rajdhani tracking-wider uppercase';
    const variants = {
      default: 'bg-slate-900 text-white shadow-2xs hover:bg-slate-800/90',
      outline: 'border border-slate-300 bg-white hover:bg-slate-100 hover:text-slate-900 text-slate-700',
      ghost: 'hover:bg-slate-100 hover:text-slate-900 text-slate-600',
      destructive: 'bg-red-600 text-white hover:bg-red-700 shadow-2xs',
      secondary: 'bg-slate-100 text-slate-900 hover:bg-slate-200 shadow-2xs',
      'hal-navy': 'bg-[#003366] text-white hover:bg-[#002244] shadow-md border border-[#003366]',
      'hal-green': 'bg-[#00A86B] text-white hover:bg-[#008F5B] shadow-md border border-[#00A86B]',
    };
    const sizes = {
      default: 'h-8 px-3 py-1.5',
      sm: 'h-6 rounded-xs px-2 text-[10px]',
      lg: 'h-10 rounded-md px-6 text-sm',
      icon: 'h-8 w-8',
    };
    return (
      <button
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = 'Button';
