// HAL Mission Control - Live Mission Operating System State Store
import { create } from 'zustand';
import { TelemetrySensor, SubsystemStage, Alert, TimelineEvent, AIInference } from '@/types';
import { OPERATIONAL_TELEMETRY, OPERATIONAL_SUBSYSTEM_STAGES, OPERATIONAL_ALERTS, OPERATIONAL_TIMELINE_EVENTS, OPERATIONAL_AI_INFERENCE } from '@/constants';
import { missionEventBus } from '@/services/missionEventBus';

export interface FlightEnvelopeState {
  mach: number;
  altitudeFt: number;
  tasKts: number;
  throttlePct: number;
  gLoad: number;
  aoaDeg: number;
  fuelFlowKgH: number;
  isentropicEffPct: number;
}

export interface AircraftSystemsState {
  hydraulicPressPsi: number;
  electricalBusA: 'ONLINE' | 'DEGRADED' | 'OFFLINE';
  electricalBusB: 'ONLINE' | 'DEGRADED' | 'OFFLINE';
  weaponLoad: string;
  landingGear: 'UP & LOCKED' | 'IN TRANSIT' | 'DOWN';
  oilPressurePsi: number;
  vibrationG: number;
  oatCelsius: number;
}

export interface WeatherState {
  condition: string;
  tempCelsius: number;
  windSpeedKts: number;
  windDirectionDeg: number;
  visibilityKm: number;
}

export interface SimulationSettings {
  refreshRateHz: number;
  simulationSpeed: number; // 1x, 4x, 10x
  solverPrecision: 'HIGH' | 'MEDIUM' | 'FAST';
  aiConfidenceThreshold: number;
  autoTriage: boolean;
}

export interface MissionStoreState {
  missionTimeSec: number;
  missionPhase: string;
  activeScenario: string;
  weather: WeatherState;
  flightEnvelope: FlightEnvelopeState;
  sysStates: AircraftSystemsState;
  telemetry: TelemetrySensor;
  subsystemStages: SubsystemStage[];
  aiInference: AIInference;
  alerts: Alert[];
  timelineEvents: TimelineEvent[];
  simulationSettings: SimulationSettings;

  // Actions
  updateTelemetry: (reading: TelemetrySensor, envelope: Partial<FlightEnvelopeState>, sys: Partial<AircraftSystemsState>) => void;
  updateSubsystems: (stages: SubsystemStage[]) => void;
  updateAiInference: (inf: AIInference) => void;
  addAlert: (alert: Alert) => void;
  acknowledgeAlert: (alertId: string) => void;
  removeAlert: (alertId: string) => void;
  addTimelineEvent: (event: TimelineEvent) => void;
  setMissionPhase: (phase: string) => void;
  setWeather: (weather: Partial<WeatherState>) => void;
  setSimulationSettings: (settings: Partial<SimulationSettings>) => void;
  triggerScenario: (scenarioId: string, overrides: Partial<MissionStoreState>) => void;
  tickTime: (deltaSec: number) => void;
}

export const useMissionStore = create<MissionStoreState>((set) => ({
  missionTimeSec: 3600, // T+01:00:00 default
  missionPhase: 'COMBAT PATROL (MACH 0.88)',
  activeScenario: 'NORMAL_PATROL',
  weather: {
    condition: 'CLEAR HIGH ALTITUDE',
    tempCelsius: -42.5,
    windSpeedKts: 45,
    windDirectionDeg: 270,
    visibilityKm: 50,
  },
  flightEnvelope: {
    mach: 0.88,
    altitudeFt: 28450,
    tasKts: 512,
    throttlePct: 74.0,
    gLoad: 1.42,
    aoaDeg: 4.8,
    fuelFlowKgH: 2450.0,
    isentropicEffPct: 92.4,
  },
  sysStates: {
    hydraulicPressPsi: 3050,
    electricalBusA: 'ONLINE',
    electricalBusB: 'ONLINE',
    weaponLoad: '2x R-73E • 2x Astra Mk1 • Drop Tank',
    landingGear: 'UP & LOCKED',
    oilPressurePsi: 68.4,
    vibrationG: 1.42,
    oatCelsius: -42.5,
  },
  telemetry: { ...OPERATIONAL_TELEMETRY },
  subsystemStages: OPERATIONAL_SUBSYSTEM_STAGES.map((s) => ({ ...s })),
  aiInference: JSON.parse(JSON.stringify(OPERATIONAL_AI_INFERENCE)),
  alerts: OPERATIONAL_ALERTS.map((a) => ({ ...a })),
  timelineEvents: OPERATIONAL_TIMELINE_EVENTS.map((e) => ({ ...e })),
  simulationSettings: {
    refreshRateHz: 1,
    simulationSpeed: 1,
    solverPrecision: 'HIGH',
    aiConfidenceThreshold: 85,
    autoTriage: true,
  },

  updateTelemetry: (reading, envelope, sys) =>
    set((state) => ({
      telemetry: { ...state.telemetry, ...reading },
      flightEnvelope: { ...state.flightEnvelope, ...envelope },
      sysStates: { ...state.sysStates, ...sys },
    })),

  updateSubsystems: (stages) => set({ subsystemStages: stages }),

  updateAiInference: (inf) => set({ aiInference: inf }),

  addAlert: (alert) =>
    set((state) => {
      if (state.alerts.some((a) => a.id === alert.id || (a.subsystemRef === alert.subsystemRef && a.title === alert.title))) {
        return state; // Prevent duplicate active alerts
      }
      missionEventBus.publish('AlertRaised', alert);
      return { alerts: [alert, ...state.alerts] };
    }),

  acknowledgeAlert: (alertId) =>
    set((state) => {
      missionEventBus.publish('AlertAcknowledged', { alertId });
      return {
        alerts: state.alerts.map((a) => (a.id === alertId ? { ...a, acknowledged: true } : a)),
      };
    }),

  removeAlert: (alertId) =>
    set((state) => ({
      alerts: state.alerts.filter((a) => a.id !== alertId),
    })),

  addTimelineEvent: (event) =>
    set((state) => {
      missionEventBus.publish('TimelineEventAdded', event);
      return { timelineEvents: [event, ...state.timelineEvents].slice(0, 50) };
    }),

  setMissionPhase: (phase) =>
    set(() => {
      missionEventBus.publish('MissionPhaseChanged', { phase });
      return { missionPhase: phase };
    }),

  setWeather: (weather) =>
    set((state) => ({
      weather: { ...state.weather, ...weather },
    })),

  setSimulationSettings: (settings) =>
    set((state) => ({
      simulationSettings: { ...state.simulationSettings, ...settings },
    })),

  triggerScenario: (scenarioId, overrides) =>
    set(() => {
      missionEventBus.publish('ScenarioTriggered', {
        scenarioId,
        name: overrides.missionPhase || scenarioId,
        description: `Triggered live engineering scenario: ${scenarioId}`,
      });
      return {
        activeScenario: scenarioId,
        ...overrides,
      };
    }),

  tickTime: (deltaSec) =>
    set((state) => {
      const nextTime = state.missionTimeSec + deltaSec * state.simulationSettings.simulationSpeed;
      return { missionTimeSec: nextTime };
    }),
}));
