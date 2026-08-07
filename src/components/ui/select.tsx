import * as React from 'react';
import { cn } from '@/lib/utils';

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <select
        className={cn(
          'flex h-8 w-full rounded-sm border border-slate-800 bg-slate-950 px-2 py-1 text-xs text-white focus:border-sky-400 focus:outline-hidden focus:ring-1 focus:ring-sky-400 disabled:cursor-not-allowed disabled:opacity-50 font-mono',
          className,
        )}
        ref={ref}
        {...props}
      >
        {children}
      </select>
    );
  },
);
Select.displayName = 'Select';
