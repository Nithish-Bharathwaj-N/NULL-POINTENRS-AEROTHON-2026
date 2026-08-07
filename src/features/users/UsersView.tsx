import React from 'react';
import { Panel, StatusBadge } from '@/components';
import { Users, Shield } from 'lucide-react';
import { useAuthStore, SecurityClearanceLevel } from '@/stores';

export const UsersView: React.FC = React.memo(() => {
  const { user, setClearanceRole } = useAuthStore();

  const roles: { role: SecurityClearanceLevel; name: string; desc: string }[] = [
    { role: 'COMMANDER', name: 'IAF Squadron Commander', desc: 'Full authority over sortie launch, AOG override, and Link-17 SATCOM keys.' },
    { role: 'ENGINEER', name: 'HAL Chief Propulsion Lead', desc: 'Read/write authority on borescope sign-offs, TLA trim, and overhaul work orders.' },
    { role: 'ANALYST', name: 'Aerospace Diagnostics Analyst', desc: 'Read-only telemetry streaming, AeroNet-v4 RUL evaluation, and XAI explainability.' },
  ];

  return (
    <div className="p-3 h-full overflow-y-auto space-y-3 bg-[#0B132B]">
      <Panel title="Security Clearance & Operator Role Management" icon={Users}>
        <div className="space-y-4 font-mono text-xs">
          <div className="p-4 bg-slate-900 text-white rounded-sm border border-slate-800 flex items-center justify-between">
            <div>
              <div className="text-sky-400 font-bold uppercase text-[10px]">CURRENT OPERATOR SESSION CLEARANCE</div>
              <div className="text-lg font-bold font-rajdhani uppercase mt-0.5">{user?.name}</div>
              <div className="text-slate-300 text-[10px] mt-0.5">CALLSIGN: {user?.callsign} • SQUADRON: {user?.squadron}</div>
            </div>
            <StatusBadge status={user?.role || 'ANALYST'} size="md" />
          </div>

          <div className="space-y-2">
            <div className="font-bold text-sky-400 text-xs uppercase border-b border-slate-800 pb-1">
              SWITCH SECURITY CLEARANCE ROLE FOR DEMONSTRATION
            </div>
            <div className="grid grid-cols-3 gap-3">
              {roles.map((r) => {
                const isActive = user?.role === r.role;
                return (
                  <div
                    key={r.role}
                    onClick={() => setClearanceRole(r.role)}
                    className={`p-3 rounded-sm border transition-all cursor-pointer flex flex-col justify-between shadow-sm ${
                      isActive
                        ? 'bg-sky-950 text-white border-sky-400 shadow-md font-bold'
                        : 'bg-slate-950/80 border-slate-800 text-white hover:border-sky-500 hover:bg-slate-900'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="font-rajdhani font-bold text-sm uppercase">{r.name}</span>
                        <Shield className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
                      </div>
                      <div className={`text-[10px] mt-1 font-normal leading-normal ${isActive ? 'text-sky-200' : 'text-slate-400'}`}>
                        {r.desc}
                      </div>
                    </div>
                    <div className="mt-3 pt-2 border-t border-slate-800 flex justify-between items-center text-[10px]">
                      <span className="text-slate-400">CLEARANCE LEVEL:</span>
                      <span className="font-bold underline text-sky-300">{r.role}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </Panel>
    </div>
  );
});
UsersView.displayName = 'UsersView';
