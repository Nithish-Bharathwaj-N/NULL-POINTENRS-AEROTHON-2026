import React from 'react';
import { useFleetData } from './hooks';
import { FleetSummaryRibbon } from './components/FleetSummaryRibbon';
import { FleetFilterBar } from './components/FleetFilterBar';
import { FleetMatrixPanel } from './components/FleetMatrixPanel';
import { FleetListPanel } from './components/FleetListPanel';
import { FleetSelectionPanel } from './components/FleetSelectionPanel';
import { FleetHealthChart } from './components/FleetHealthChart';
import { FleetMissionBoard } from './components/FleetMissionBoard';
import { FleetMaintenanceQueue } from './components/FleetMaintenanceQueue';
import { FleetOperationalFeed } from './components/FleetOperationalFeed';

export const FleetView: React.FC = React.memo(() => {
  const {
    fleet,
    filteredFleet,
    selectedTail,
    setSelectedTail,
    selectedAircraft,
    searchQuery,
    setSearchQuery,
    squadronFilter,
    setSquadronFilter,
    statusFilter,
    setStatusFilter,
    activeTab,
    setActiveTab,
    fleetMetrics,
  } = useFleetData();

  return (
    <div className="flex flex-col h-full gap-3 p-3 overflow-y-auto bg-[#0B132B]">
      {/* TIER 1: FLEET SUMMARY RIBBON & OPERATIONAL FILTERS */}
      <FleetSummaryRibbon metrics={fleetMetrics} />
      <FleetFilterBar
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        squadronFilter={squadronFilter}
        setSquadronFilter={setSquadronFilter}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        totalCount={fleet.length}
      />

      {/* TIER 2: MAIN FLEET MATRIX OR LIST DOCK (75% Center, 25% Right Inspector) */}
      <div className="grid grid-cols-12 gap-3 min-h-[500px] shrink-0">
        <div className="col-span-9 h-full">
          {activeTab === 'matrix' ? (
            <FleetMatrixPanel fleet={filteredFleet} selectedTail={selectedTail} onSelectTail={setSelectedTail} />
          ) : (
            <FleetListPanel fleet={filteredFleet} selectedTail={selectedTail} onSelectTail={setSelectedTail} />
          )}
        </div>

        <div className="col-span-3 flex flex-col gap-3">
          <div className="flex-1 min-h-[260px]">
            <FleetSelectionPanel ac={selectedAircraft} />
          </div>
          <div className="flex-1 min-h-[220px]">
            <FleetHealthChart ac={selectedAircraft} />
          </div>
        </div>
      </div>

      {/* TIER 3: BOTTOM OPERATIONAL QUEUES */}
      <div className="grid grid-cols-12 gap-3 min-h-[260px] shrink-0 pb-6">
        <div className="col-span-5 h-full">
          <FleetMissionBoard fleet={fleet} onSelectTail={setSelectedTail} />
        </div>
        <div className="col-span-4 h-full">
          <FleetMaintenanceQueue />
        </div>
        <div className="col-span-3 h-full">
          <FleetOperationalFeed />
        </div>
      </div>
    </div>
  );
});
FleetView.displayName = 'FleetView';
