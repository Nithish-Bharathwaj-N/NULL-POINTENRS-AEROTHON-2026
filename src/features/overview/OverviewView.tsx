import React, { useState } from 'react';
import { useOverviewData } from './hooks';
import { AerothonAccuracyPanel } from '@/components/AerothonAccuracyPanel';
import { MissionSummaryRibbon } from './components/MissionSummaryRibbon';
import { MissionOperationsPanel } from './components/MissionOperationsPanel';
import { FlightEnvelopePanel } from './components/FlightEnvelopePanel';
import { DigitalTwinInspector } from './components/DigitalTwinInspector';
import { EngineHealthSummaryPanel } from './components/EngineHealthSummaryPanel';
import { AiMissionSummaryPanel } from './components/AiMissionSummaryPanel';
import { LiveTelemetryPanel } from './components/LiveTelemetryPanel';
import { AlertsPanel } from './components/AlertsPanel';
import { MissionTimelinePanel } from './components/MissionTimelinePanel';
import { LaymanOverview } from './components/LaymanOverview';
import { Eye, Terminal } from 'lucide-react';

export const OverviewView: React.FC = React.memo(() => {
  const { ac, selectedStageRef, summaryMetrics, handleStageSelect } = useOverviewData();
  const [activeTab, setActiveTab] = useState<'layman' | 'technical'>('layman');

  return (
    <div className="flex flex-col h-full bg-[#0B132B] overflow-hidden">

      {/* ── TAB BAR ──────────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-1 px-4 pt-3 pb-0 shrink-0 border-b border-slate-800">
        <button
          id="tab-mission-overview"
          onClick={() => setActiveTab('layman')}
          className={`flex items-center gap-2 px-4 py-2 rounded-t-lg text-sm font-bold transition-all cursor-pointer ${
            activeTab === 'layman'
              ? 'bg-slate-800 text-white border-t border-l border-r border-slate-700 -mb-px'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
          }`}
        >
          <Eye className="w-4 h-4" />
          Mission Overview
          <span className="ml-1 px-1.5 py-0.5 bg-sky-600 text-white text-[10px] font-black rounded-full">NEW</span>
        </button>
        <button
          id="tab-technical-view"
          onClick={() => setActiveTab('technical')}
          className={`flex items-center gap-2 px-4 py-2 rounded-t-lg text-sm font-bold transition-all cursor-pointer ${
            activeTab === 'technical'
              ? 'bg-slate-800 text-white border-t border-l border-r border-slate-700 -mb-px'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
          }`}
        >
          <Terminal className="w-4 h-4" />
          Technical Workstation
        </button>
      </div>

      {/* ── TAB CONTENT ───────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto">

        {/* ═══ MISSION OVERVIEW (Layman-Friendly) ═══════════════════════════════ */}
        {activeTab === 'layman' && <LaymanOverview />}

        {/* ═══ TECHNICAL WORKSTATION (Original) ════════════════════════════════ */}
        {activeTab === 'technical' && (
          <div className="flex flex-col gap-3 p-4 pt-4">
            {/* TIER 0: AEROTHON ACCURACY & MODEL JUDGING MATRIX */}
            <div className="shrink-0 mb-1">
              <AerothonAccuracyPanel />
            </div>

            {/* TIER 1: MISSION SUMMARY RIBBON */}
            <MissionSummaryRibbon metrics={summaryMetrics} />

            {/* TIER 2: MAIN WORKSTATION DOCK */}
            <div className="grid grid-cols-12 gap-3 shrink-0">
              <div className="col-span-6 flex flex-col gap-3">
                <MissionOperationsPanel ac={ac} />
                <FlightEnvelopePanel ac={ac} />
              </div>
              <div className="col-span-6 flex flex-col gap-3">
                <DigitalTwinInspector selectedStageRef={selectedStageRef} onSelectStage={handleStageSelect} />
                <EngineHealthSummaryPanel selectedStageRef={selectedStageRef} onSelectStage={handleStageSelect} />
                <AiMissionSummaryPanel />
              </div>
            </div>

            {/* TIER 3: BOTTOM ANALYTICS DOCK */}
            <div className="grid grid-cols-12 gap-3 min-h-[260px] shrink-0 pb-8">
              <div className="col-span-6 h-full">
                <LiveTelemetryPanel onSelectStage={handleStageSelect} />
              </div>
              <div className="col-span-6 flex flex-col gap-3">
                <div className="flex-1 min-h-[125px]">
                  <AlertsPanel onSelectStage={handleStageSelect} />
                </div>
                <div className="flex-1 min-h-[125px]">
                  <MissionTimelinePanel onSelectStage={handleStageSelect} />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
});
OverviewView.displayName = 'OverviewView';
