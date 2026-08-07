import React, { useState } from 'react';
import { Panel, StatusBadge } from '@/components';
import { Wrench, CheckCircle } from 'lucide-react';
import { OPERATIONAL_MAINTENANCE_TASKS } from '@/constants';
import { MaintenanceTask } from '@/types';

export const MaintenanceView: React.FC = React.memo(() => {
  const [tasks, setTasks] = useState<MaintenanceTask[]>(OPERATIONAL_MAINTENANCE_TASKS);

  const handleStatusChange = (id: string, nextStatus: MaintenanceTask['status']) => {
    setTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, status: nextStatus } : t)),
    );
  };

  return (
    <div className="p-3 h-full overflow-y-auto space-y-3 bg-[#0B132B]">
      <Panel title="HAL Overhaul & Borescope Work Order Scheduling Board" icon={Wrench}>
        <div className="space-y-3 font-mono text-xs">
          <div className="grid grid-cols-2 gap-3">
            {tasks.map((wo) => (
              <div key={wo.id} className="p-3 bg-slate-950/80 border border-slate-800 rounded-sm shadow-sm space-y-2.5">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sky-300 text-sm">{wo.id}</span>
                    <StatusBadge status={wo.priority} size="sm" />
                  </div>
                  <span className="text-[11px] font-bold text-white bg-slate-800 px-2 py-0.5 rounded-xs border border-slate-700">
                    {wo.aircraftTail} • {wo.engineSerial}
                  </span>
                </div>

                <div>
                  <div className="font-bold text-white text-sm">{wo.title}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    ASSIGNED: {wo.assignedCrew} • BAY: {wo.location}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    TASK CODE: <span className="font-bold text-sky-300">{wo.taskCode}</span> • EST: {wo.estimatedHours} Hrs
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400 text-[10px]">CURRENT STATUS:</span>
                    <StatusBadge status={wo.status} size="sm" />
                  </div>
                  <div className="flex gap-1">
                    {wo.status !== 'COMPLETED' ? (
                      <button
                        onClick={() => handleStatusChange(wo.id, 'COMPLETED')}
                        className="flex items-center gap-1 px-2 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xs text-[10px] cursor-pointer"
                      >
                        <CheckCircle className="w-3 h-3" />
                        <span>Sign-Off Complete</span>
                      </button>
                    ) : (
                      <span className="text-emerald-400 font-bold text-[10px] flex items-center gap-1">
                        <CheckCircle className="w-3.5 h-3.5" /> QA VERIFIED
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Panel>
    </div>
  );
});
MaintenanceView.displayName = 'MaintenanceView';
