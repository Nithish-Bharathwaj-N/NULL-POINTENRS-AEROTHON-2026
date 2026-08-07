import React, { Suspense } from 'react';
import { useUiStore } from '@/stores';
import { Skeleton } from '@/components';
import {
  OverviewView,
  FleetView,
  DetailsView,
  TwinView,
  OuterTwinView,
  TelemetryView,
  EngineAnalysisView,
  AiDiagnosticsView,
  ExplainabilityView,
  PhysicsView,
  InvestigationView,
  MaintenanceView,
  ReportsView,
  ReplayView,
  HistoricalView,
  AlertsView,
  EventTimelineView,
  UsersView,
  SettingsView,
} from '@/features';

export const WorkstationPage: React.FC = React.memo(() => {
  const { currentView } = useUiStore();

  const renderActiveView = () => {
    switch (currentView) {
      case 'overview':
        return <OverviewView />;
      case 'fleet':
        return <FleetView />;
      case 'details':
        return <DetailsView />;
      case 'outer_twin':
        return <OuterTwinView />;
      case 'twin':
        return <TwinView />;

      case 'telemetry':
        return <TelemetryView />;
      case 'engine':
        return <EngineAnalysisView />;
      case 'ai':
        return <AiDiagnosticsView />;
      case 'explain':
        return <ExplainabilityView />;
      case 'physics':
        return <PhysicsView />;
      case 'investigation':
        return <InvestigationView />;
      case 'maintenance':
        return <MaintenanceView />;
      case 'reports':
        return <ReportsView />;
      case 'replay':
        return <ReplayView />;
      case 'historical':
        return <HistoricalView />;
      case 'alerts':
        return <AlertsView />;
      case 'eventtimeline':
        return <EventTimelineView />;
      case 'users':
        return <UsersView />;
      case 'settings':
        return <SettingsView />;
      default:
        return <OverviewView />;
    }
  };

  return (
    <Suspense
      fallback={
        <div className="p-4 h-full flex flex-col gap-3">
          <Skeleton className="h-16 w-full" />
          <div className="grid grid-cols-12 gap-3 flex-1">
            <Skeleton className="col-span-3 h-full" />
            <Skeleton className="col-span-6 h-full" />
            <Skeleton className="col-span-3 h-full" />
          </div>
        </div>
      }
    >
      {renderActiveView()}
    </Suspense>
  );
});
WorkstationPage.displayName = 'WorkstationPage';
