import React from 'react';
import { Search, Filter, LayoutGrid, List } from 'lucide-react';
import { Input, Select } from '@/components';

interface FleetFilterBarProps {
  searchQuery: string;
  setSearchQuery: (val: string) => void;
  squadronFilter: string;
  setSquadronFilter: (val: string) => void;
  statusFilter: string;
  setStatusFilter: (val: string) => void;
  activeTab: 'matrix' | 'list';
  setActiveTab: (tab: 'matrix' | 'list') => void;
  totalCount: number;
}

export const FleetFilterBar: React.FC<FleetFilterBarProps> = React.memo(({
  searchQuery,
  setSearchQuery,
  squadronFilter,
  setSquadronFilter,
  statusFilter,
  setStatusFilter,
  activeTab,
  setActiveTab,
  totalCount,
}) => (
  <div className="bg-slate-900/90 border border-slate-800 rounded-sm p-2 shadow-md flex items-center justify-between gap-3 font-mono text-xs select-none shrink-0 text-slate-100">
    <div className="flex items-center gap-2 flex-1 max-w-md">
      <div className="relative flex-1">
        <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
        <Input
          type="text"
          placeholder="Search by Tail (e.g. TJ-103), Pilot, or Bay..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-8"
        />
      </div>
    </div>

    <div className="flex items-center gap-2">
      <div className="flex items-center gap-1 text-sky-400">
        <Filter className="w-3.5 h-3.5 text-sky-400" />
        <span className="text-[10px] font-bold uppercase tracking-wider">FILTER:</span>
      </div>

      <Select
        value={squadronFilter}
        onChange={(e) => setSquadronFilter(e.target.value)}
        className="w-48"
      >
        <option value="ALL" className="bg-slate-900 text-white">ALL SQUADRONS (3)</option>
        <option value="No. 45 Sqn" className="bg-slate-900 text-white">No. 45 Sqn (Flying Daggers)</option>
        <option value="No. 18 Sqn" className="bg-slate-900 text-white">No. 18 Sqn (Flying Bullets)</option>
        <option value="HAL Flight Test" className="bg-slate-900 text-white">HAL Flight Test Center</option>
      </Select>

      <Select
        value={statusFilter}
        onChange={(e) => setStatusFilter(e.target.value)}
        className="w-40"
      >
        <option value="ALL" className="bg-slate-900 text-white">ALL STATUSES ({totalCount})</option>
        <option value="AIRBORNE" className="bg-slate-900 text-white">AIRBORNE / COMBAT</option>
        <option value="QRA" className="bg-slate-900 text-white">ARMED STANDBY (QRA)</option>
        <option value="GROUNDED" className="bg-slate-900 text-white">GROUNDED / MAINT</option>
      </Select>
    </div>

    <div className="flex items-center bg-slate-950 p-0.5 rounded-sm border border-slate-800">
      <button
        onClick={() => setActiveTab('matrix')}
        className={`flex items-center gap-1 px-2.5 py-1 rounded-xs font-rajdhani font-bold text-xs uppercase tracking-wider transition-all cursor-pointer ${
          activeTab === 'matrix' ? 'bg-sky-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
        }`}
      >
        <LayoutGrid className="w-3.5 h-3.5" />
        <span>Squadron Matrix</span>
      </button>
      <button
        onClick={() => setActiveTab('list')}
        className={`flex items-center gap-1 px-2.5 py-1 rounded-xs font-rajdhani font-bold text-xs uppercase tracking-wider transition-all cursor-pointer ${
          activeTab === 'list' ? 'bg-sky-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
        }`}
      >
        <List className="w-3.5 h-3.5" />
        <span>List View</span>
      </button>
    </div>
  </div>
));
FleetFilterBar.displayName = 'FleetFilterBar';
