import React from 'react';
import { useUiStore, WorkstationViewId } from '@/stores';
import {
  LayoutDashboard,
  Plane,
  FileText,
  Box,
  Layers,
  Activity,
  Cpu,
  BrainCircuit,
  HelpCircle,
  Atom,
  Search,
  Wrench,
  FileSpreadsheet,
  RotateCcw,
  TrendingUp,
  Bell,
  Clock,
  Users,
  Settings,
} from 'lucide-react';

interface NavItem {
  id: WorkstationViewId;
  label: string;
  icon: React.ElementType;
  badge?: string;
}

interface NavGroup {
  label?: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: 'Operations',
    items: [
      { id: 'overview', label: 'Mission Overview', icon: LayoutDashboard },
      { id: 'fleet', label: 'Fleet Operations', icon: Plane, badge: '10 A/C' },
      { id: 'details', label: 'Aircraft Logbook', icon: FileText },
    ],
  },
  {
    label: 'Digital Twin',
    items: [
      { id: 'twin', label: '3D Digital Twin', icon: Box, badge: 'CAD' },
      { id: 'telemetry', label: 'Live Telemetry', icon: Activity, badge: '1Hz' },
      { id: 'engine', label: 'Thermodynamics', icon: Cpu },
      { id: 'physics', label: 'Physics Models', icon: Atom },
    ],
  },


  {
    label: 'Intelligence',
    items: [
      { id: 'ai', label: 'AI Diagnostics', icon: BrainCircuit, badge: 'v4' },
      { id: 'explain', label: 'XAI Explainability', icon: HelpCircle },
      { id: 'investigation', label: 'Root Cause Analysis', icon: Search },
    ],
  },
  {
    label: 'Maintenance & Logs',
    items: [
      { id: 'maintenance', label: 'Work Orders', icon: Wrench, badge: '4 WO' },
      { id: 'reports', label: 'Airworthiness Certs', icon: FileSpreadsheet },
      { id: 'replay', label: 'Mission Replay', icon: RotateCcw },
      { id: 'historical', label: 'Historical Trends', icon: TrendingUp },
      { id: 'eventtimeline', label: 'Event Timeline', icon: Clock },
    ],
  },
  {
    label: 'System',
    items: [
      { id: 'alerts', label: 'Active Alerts', icon: Bell, badge: '3' },
      { id: 'users', label: 'Clearance Roles', icon: Users },
      { id: 'settings', label: 'HUD Settings', icon: Settings },
    ],
  },
];

export const WorkstationSidebar: React.FC = React.memo(() => {
  const { currentView, setView } = useUiStore();

  return (
    <aside className="w-52 bg-[#0B132B] text-slate-200 flex flex-col border-r border-slate-800 select-none z-20 shrink-0">
      <div className="flex-1 overflow-y-auto py-3 space-y-3">
        {NAV_GROUPS.map((group, idx) => (
          <div key={idx} className="space-y-0.5">
            {group.label && (
              <div className="px-4 pt-1 pb-1 font-rajdhani text-[10px] font-bold tracking-widest text-sky-400">
                {group.label}
              </div>
            )}
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive = currentView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setView(item.id)}
                  className={`flex items-center justify-between gap-2 px-3 py-2 mx-2 rounded-md text-left w-[calc(100%-16px)] font-rajdhani font-bold text-[13px] tracking-wide transition-all cursor-pointer ${
                    isActive
                      ? 'bg-[#003366] text-sky-300 border border-[#00A86B]/60 shadow-sm'
                      : 'text-slate-300 hover:bg-slate-800/80 hover:text-white border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
                    <span className="truncate">{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-xs shrink-0 ${
                        isActive ? 'bg-[#00A86B] text-slate-950' : 'bg-slate-800 text-slate-400 border border-slate-700'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </div>
      <div className="p-3 border-t border-slate-800 bg-slate-900/90 font-mono text-[9px] text-slate-400 flex flex-col gap-1">
        <div className="flex justify-between items-center text-slate-200 font-bold">
          <span>System Status</span>
          <span className="text-emerald-400">Nominal • 60 FPS</span>
        </div>
        <div className="text-slate-500">HAL Aerothon Platform v2026.2</div>
      </div>
    </aside>
  );
});
WorkstationSidebar.displayName = 'WorkstationSidebar';
