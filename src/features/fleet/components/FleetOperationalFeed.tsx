import React from 'react';
import { Panel } from '@/components';
import { Bell } from 'lucide-react';
import { useMissionStore } from '@/stores';

export const FleetOperationalFeed: React.FC = React.memo(() => {
  const alerts = useMissionStore((s) => s.alerts);
  return (
    <Panel title="Real-Time Squadron Operational Feed" icon={Bell} className="h-full" noPad>
      <div className="divide-y divide-slate-200 font-mono text-xs">
        {alerts.map((alt) => (
          <div key={alt.id} className="p-2.5 hover:bg-slate-50 transition-colors flex items-start gap-2.5">
            <span className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${alt.severity === 'CRITICAL' ? 'bg-red-500 animate-ping' : 'bg-amber-500'}`} />
            <div className="space-y-0.5 flex-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900">{alt.title}</span>
                <span className="text-[10px] text-slate-400 font-bold">{alt.timestamp}</span>
              </div>
              <p className="text-slate-600 text-[11px]">{alt.description}</p>
              <div className="text-[10px] font-bold text-[#003366] pt-0.5">ENGINE: {alt.engineId} • TRIAGE REQUIRED</div>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
});
FleetOperationalFeed.displayName = 'FleetOperationalFeed';
