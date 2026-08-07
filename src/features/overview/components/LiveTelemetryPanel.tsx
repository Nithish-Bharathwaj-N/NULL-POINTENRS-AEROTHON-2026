import React, { useEffect, useState } from 'react';
import { Panel, StatusBadge } from '@/components';
import { Activity } from 'lucide-react';
import { telemetryService } from '@/services';
import { TransducerChannel } from '@/types';
import { useMissionStore } from '@/stores/useMissionStore';

interface LiveTelemetryPanelProps {
  onSelectStage: (stageRef: string) => void;
}

export const LiveTelemetryPanel: React.FC<LiveTelemetryPanelProps> = React.memo(({ onSelectStage }) => {
  const [channels, setChannels] = useState<TransducerChannel[]>([]);
  const telemetry = useMissionStore((state) => state.telemetry);

  useEffect(() => {
    let mounted = true;
    telemetryService.getTransducerChannels('TJ04-SER-88219').then((data) => {
      if (mounted) setChannels(data);
    });
    return () => {
      mounted = false;
    };
  }, [telemetry]);

  return (
    <Panel title="Live Telemetry & Physics Residuals (1Hz Stream)" icon={Activity} className="h-full" noPad>
      <div className="overflow-x-auto font-mono text-xs">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-800 text-sky-400 font-bold uppercase tracking-wider text-[10px] border-b border-slate-700">
              <th className="p-2">Transducer Channel</th>
              <th className="p-2">Subsystem Stage</th>
              <th className="p-2">ARINC Word</th>
              <th className="p-2 text-right">Current Value</th>
              <th className="p-2 text-right">Expected Value</th>
              <th className="p-2 text-right">Residual (Δ)</th>
              <th className="p-2 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {channels.map((ch) => (
              <tr
                key={ch.id}
                onClick={() => onSelectStage(ch.sensorRef)}
                className="hover:bg-slate-800/80 transition-colors cursor-pointer group"
              >
                <td className="p-2 font-bold text-white group-hover:text-sky-300">{ch.name}</td>
                <td className="p-2 text-slate-300 uppercase font-medium">{ch.sensorRef}</td>
                <td className="p-2 text-slate-400 text-[10px]">{ch.arinc429Word}</td>
                <td className="p-2 text-right font-bold text-white">{ch.current} <span className="text-[10px] font-normal text-sky-400">{ch.unit}</span></td>
                <td className="p-2 text-right text-slate-300 font-medium">{ch.expected} <span className="text-[10px] font-normal text-slate-400">{ch.unit}</span></td>
                <td className={`p-2 text-right font-bold ${ch.delta > 20 ? 'text-red-400' : ch.delta > 5 ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {ch.delta > 0 ? `+${ch.delta.toFixed(2)}` : ch.delta.toFixed(2)} {ch.unit}
                </td>
                <td className="p-2 text-center"><StatusBadge status={ch.status} size="sm" /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
});
LiveTelemetryPanel.displayName = 'LiveTelemetryPanel';
