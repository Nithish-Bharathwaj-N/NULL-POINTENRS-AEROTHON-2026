// HAL Mission Control - Zustand UI Navigation & Stage Selection Store
import { create } from 'zustand';
import { Alert } from '@/types';
import { missionEventBus } from '@/services/missionEventBus';

export type WorkstationViewId =
  | 'overview'
  | 'fleet'
  | 'details'
  | 'outer_twin'
  | 'twin'
  | 'telemetry'
  | 'engine'
  | 'ai'
  | 'explain'
  | 'physics'
  | 'investigation'
  | 'maintenance'
  | 'reports'
  | 'replay'
  | 'historical'
  | 'alerts'
  | 'eventtimeline'
  | 'users'
  | 'settings';


interface UiStoreState {
  currentView: WorkstationViewId;
  selectedStageRef: string | null;
  selectedAlert: Alert | null;
  selectedSensorChannel: string | null;
  timeRangeSec: number;
  themeMode: 'dark' | 'light' | 'hud';
  hudUnits: 'metric' | 'imperial';
  setView: (view: WorkstationViewId) => void;
  setSelectedStageRef: (stageRef: string | null) => void;
  setSelectedAlert: (alert: Alert | null) => void;
  setSelectedSensorChannel: (channel: string | null) => void;
  setTimeRangeSec: (sec: number) => void;
  setThemeMode: (mode: 'dark' | 'light' | 'hud') => void;
  toggleHudUnits: () => void;
}

export const useUiStore = create<UiStoreState>((set, get) => ({
  currentView: 'twin',
  selectedStageRef: 'combustor', // Default selected subsystem for demo binding
  selectedAlert: null,
  selectedSensorChannel: null,
  timeRangeSec: 3600, // 1 hour default window
  themeMode: 'light', // Matches prototype background #F4F6F8
  hudUnits: 'metric',
  setView: (view) => set({ currentView: view }),
  setSelectedStageRef: (stageRef) => {
    set({ selectedStageRef: stageRef });
    missionEventBus.publish('EngineStageSelected', { stageRef });
    missionEventBus.publish('DigitalTwinSelectionChanged', { stageRef });
  },
  setSelectedAlert: (alert) => {
    set({ selectedAlert: alert });
    if (alert) {
      missionEventBus.publish('AlertRaised', alert);
      if (alert.subsystemRef && alert.subsystemRef !== get().selectedStageRef) {
        get().setSelectedStageRef(alert.subsystemRef);
      }
    }
  },
  setSelectedSensorChannel: (channel) => set({ selectedSensorChannel: channel }),
  setTimeRangeSec: (sec) => set({ timeRangeSec: sec }),
  setThemeMode: (mode) => set({ themeMode: mode }),
  toggleHudUnits: () =>
    set((state) => ({ hudUnits: state.hudUnits === 'metric' ? 'imperial' : 'metric' })),
}));
