import React from 'react';
import { CADViewMode } from '@/types';
import { Box, Layers, Zap, Flame, ShieldAlert, Eye, RefreshCw, ZoomIn, ZoomOut } from 'lucide-react';

interface CADToolbarProps {
  viewMode: CADViewMode;
  setViewMode: (mode: CADViewMode) => void;
  zoom: number;
  setZoom: React.Dispatch<React.SetStateAction<number>>;
  setPan: React.Dispatch<React.SetStateAction<{ x: number; y: number }>>;
}

const MODES: { id: CADViewMode; label: string; icon: React.ElementType }[] = [
  { id: 'NORMAL ASSEMBLY', label: 'NORMAL ASSEMBLY', icon: Box },
  { id: 'X-RAY SPOOLS', label: 'X-RAY SPOOLS', icon: Eye },
  { id: 'EXPLODED CAD', label: 'EXPLODED CAD', icon: Layers },
  { id: 'THERMAL FIELD', label: 'THERMAL FIELD', icon: Flame },
  { id: 'PRESSURE FIELD', label: 'PRESSURE FIELD', icon: Zap },
  { id: 'STRESS LOAD (FEA)', label: 'STRESS LOAD (FEA)', icon: ShieldAlert },
];

export const CADToolbar: React.FC<CADToolbarProps> = React.memo(({ viewMode, setViewMode, zoom, setZoom, setPan }) => (
  <div className="flex items-center justify-between bg-slate-900 text-white px-3 py-1.5 border-b border-slate-800 font-mono text-xs select-none shrink-0">
    <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5">
      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mr-1 shrink-0 whitespace-nowrap">CAD VIEWPORT:</span>
      {MODES.map((m) => {
        const Icon = m.icon;
        const isActive = viewMode === m.id;
        return (
          <button
            key={m.id}
            onClick={() => setViewMode(m.id)}
            className={`flex items-center gap-1.5 px-2.5 py-1 font-rajdhani font-bold text-xs tracking-wider uppercase transition-all whitespace-nowrap shrink-0 cursor-pointer ${
              isActive
                ? 'bg-[#003366] text-white border border-[#00A86B] shadow-2xs'
                : 'bg-slate-800/90 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700'
            }`}
          >
            <Icon className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-[#00A86B]' : 'text-slate-400'}`} />
            <span>{m.label}</span>
          </button>
        );
      })}
    </div>

    <div className="flex items-center gap-1 shrink-0 ml-2 border-l border-slate-700 pl-2">
      <button
        onClick={() => setZoom((z) => Math.min(2.5, z + 0.2))}
        className="p-1 bg-slate-800 hover:bg-slate-700 text-slate-200 cursor-pointer border border-slate-700"
        title="Zoom In"
      >
        <ZoomIn className="w-3.5 h-3.5" />
      </button>
      <button
        onClick={() => setZoom((z) => Math.max(0.6, z - 0.2))}
        className="p-1 bg-slate-800 hover:bg-slate-700 text-slate-200 cursor-pointer border border-slate-700"
        title="Zoom Out"
      >
        <ZoomOut className="w-3.5 h-3.5" />
      </button>
      <button
        onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}
        className="p-1 bg-slate-800 hover:bg-slate-700 text-slate-200 cursor-pointer border border-slate-700"
        title="Reset Camera"
      >
        <RefreshCw className="w-3.5 h-3.5" />
      </button>
      <span className="text-[10px] text-sky-400 font-bold ml-1 min-w-[36px] text-right">{Math.round(zoom * 100)}%</span>
    </div>
  </div>
));
CADToolbar.displayName = 'CADToolbar';
