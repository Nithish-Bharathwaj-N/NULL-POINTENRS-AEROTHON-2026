import React, { useState } from 'react';
import { Panel, HealthRing } from '@/components';
import { Cpu, ChevronDown, ChevronUp, Activity } from 'lucide-react';
import { useMissionStore } from '@/stores';
import { statusColor } from '@/utils';

interface EngineHealthSummaryPanelProps {
  selectedStageRef: string | null;
  onSelectStage: (stageRef: string | null) => void;
}

export const EngineHealthSummaryPanel: React.FC<EngineHealthSummaryPanelProps> = React.memo(({ selectedStageRef, onSelectStage }) => {
  const subsystemStages = useMissionStore((s) => s.subsystemStages);
  const [isExpanded, setIsExpanded] = useState(false);

  // Compute 4 core health indicators
  const compStages = subsystemStages.filter((s) => s.ref.includes('lpc') || s.ref.includes('hpc') || s.ref.includes('fan'));
  const combStages = subsystemStages.filter((s) => s.ref.includes('combustor'));
  const turbStages = subsystemStages.filter((s) => s.ref.includes('hpt') || s.ref.includes('lpt'));

  const compHealth = Math.round(compStages.reduce((acc, s) => acc + s.health, 0) / (compStages.length || 1));
  const combHealth = Math.round(combStages.reduce((acc, s) => acc + s.health, 0) / (combStages.length || 1));
  const turbHealth = Math.round(turbStages.reduce((acc, s) => acc + s.health, 0) / (turbStages.length || 1));
  const overallHealth = Number(((compHealth + combHealth + turbHealth) / 3).toFixed(1));

  return (
    <Panel
      title="Propulsion & Subsystem Health"
      icon={Cpu}
      className="shrink-0 transition-all duration-300"
      noPad
      headerRight={
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-[10px] font-mono font-bold text-sky-400 hover:text-white px-2 py-0.5 bg-slate-800/80 hover:bg-slate-700 border border-slate-700 rounded transition-colors cursor-pointer"
        >
          <span>{isExpanded ? 'Collapse' : 'Expand Stages'}</span>
          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      }
    >
      <div className="font-mono text-xs">
        {/* COMPACT SIDE HEALTH METRICS BAR (Always Visible) */}
        <div className="grid grid-cols-4 gap-2 p-2.5 bg-slate-950/90 border-b border-slate-800">
          <div className="flex flex-col items-center justify-center p-1.5 bg-slate-900/80 border border-slate-800 rounded">
            <span className="text-[9px] font-bold text-slate-400 uppercase">Compressor</span>
            <span className={`text-xs font-bold ${compHealth >= 90 ? 'text-emerald-400' : 'text-amber-400'}`}>
              {compHealth}%
            </span>
          </div>

          <div className="flex flex-col items-center justify-center p-1.5 bg-slate-900/80 border border-slate-800 rounded">
            <span className="text-[9px] font-bold text-slate-400 uppercase">Combustor</span>
            <span className={`text-xs font-bold ${combHealth >= 90 ? 'text-emerald-400' : 'text-amber-400'}`}>
              {combHealth}%
            </span>
          </div>

          <div className="flex flex-col items-center justify-center p-1.5 bg-slate-900/80 border border-slate-800 rounded">
            <span className="text-[9px] font-bold text-slate-400 uppercase">Turbine</span>
            <span className={`text-xs font-bold ${turbHealth >= 90 ? 'text-emerald-400' : 'text-amber-400'}`}>
              {turbHealth}%
            </span>
          </div>

          <div className="flex flex-col items-center justify-center p-1.5 bg-sky-950/80 border border-sky-800/60 rounded">
            <span className="text-[9px] font-bold text-sky-400 uppercase">Overall</span>
            <span className="text-xs font-bold text-sky-300">
              {overallHealth}%
            </span>
          </div>
        </div>

        {/* EXPANDABLE DETAILED 6-STAGE RANKING LIST */}
        {isExpanded && (
          <div className="divide-y divide-slate-800 animate-fadeIn">
            {subsystemStages.map((stg) => {
              const isSelected = selectedStageRef === stg.ref;
              const badgeCol = statusColor(stg.status);
              return (
                <div
                  key={stg.ref}
                  onClick={() => onSelectStage(stg.ref)}
                  className={`flex items-center justify-between p-2.5 transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-sky-950/80 border-l-4 border-sky-400 font-bold text-white shadow-sm'
                      : 'hover:bg-slate-800/80 text-slate-300'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <HealthRing health={stg.health} size={28} stroke={3} />
                    <div>
                      <div className={isSelected ? 'text-white font-bold' : 'text-slate-200 font-medium'}>
                        {stg.name}
                      </div>
                      <div className="text-[10px] text-slate-400 font-normal">
                        Temp: {stg.temp}°C • Press: {stg.pressure} Bar
                      </div>
                    </div>
                  </div>
                  <span className={`px-2 py-0.5 rounded-xs font-bold text-[9px] uppercase tracking-wider ${badgeCol}`}>
                    {stg.status}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Panel>
  );
});
EngineHealthSummaryPanel.displayName = 'EngineHealthSummaryPanel';
