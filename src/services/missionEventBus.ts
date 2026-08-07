// HAL Mission Control - Global Mission Event Bus
import { TelemetrySensor, Alert, MaintenanceTask, TimelineEvent } from '@/types';

export type MissionEventType =
  | 'TelemetryUpdated'
  | 'SubsystemWarning'
  | 'SubsystemRecovered'
  | 'EngineStageSelected'
  | 'MissionPhaseChanged'
  | 'AircraftSelected'
  | 'FuelLow'
  | 'RULUpdated'
  | 'AlertRaised'
  | 'AlertAcknowledged'
  | 'MaintenanceCreated'
  | 'TimelineEventAdded'
  | 'ReplayBookmarkAdded'
  | 'DigitalTwinSelectionChanged'
  | 'ScenarioTriggered';

export interface MissionEventPayloads {
  TelemetryUpdated: { timeSec: number; sensors: TelemetrySensor };
  SubsystemWarning: { stageRef: string; temp: number; pressure: number; warning: string };
  SubsystemRecovered: { stageRef: string };
  EngineStageSelected: { stageRef: string | null };
  MissionPhaseChanged: { phase: string };
  AircraftSelected: { tail: string };
  FuelLow: { fuelPct: number; fuelKg: number };
  RULUpdated: { rulHours: number; confidencePct: number };
  AlertRaised: Alert;
  AlertAcknowledged: { alertId: string };
  MaintenanceCreated: MaintenanceTask;
  TimelineEventAdded: TimelineEvent;
  ReplayBookmarkAdded: { timeSec: number; label: string };
  DigitalTwinSelectionChanged: { stageRef: string | null };
  ScenarioTriggered: { scenarioId: string; name: string; description: string };
}

type EventCallback<T extends MissionEventType> = (payload: MissionEventPayloads[T]) => void;

class MissionEventBus {
  private listeners: { [K in MissionEventType]?: Array<EventCallback<K>> } = {};

  public subscribe<T extends MissionEventType>(type: T, callback: EventCallback<T>): () => void {
    if (!this.listeners[type]) {
      this.listeners[type] = [];
    }
    this.listeners[type]!.push(callback);

    // Return unsubscribe function
    return () => {
      const idx = this.listeners[type]?.indexOf(callback) ?? -1;
      if (idx > -1) {
        this.listeners[type]!.splice(idx, 1);
      }
    };
  }

  public publish<T extends MissionEventType>(type: T, payload: MissionEventPayloads[T]): void {
    const callbacks = this.listeners[type];
    if (callbacks && callbacks.length > 0) {
      // Execute asynchronously or safely in current loop
      callbacks.forEach((cb) => {
        try {
          cb(payload);
        } catch (err) {
          console.error(`[MissionEventBus] Error executing subscriber for ${type}:`, err);
        }
      });
    }
  }

  public clear(): void {
    this.listeners = {};
  }
}

export const missionEventBus = new MissionEventBus();
