// HAL Mission Control - Real-Time WebSocket Service (1Hz Streaming via Mission Engine)
import { TelemetrySensor } from '@/types';
import { missionEngine } from './missionEngine';
import { missionEventBus } from './missionEventBus';
import { useMissionStore } from '@/stores/useMissionStore';

type SensorCallback = (data: TelemetrySensor) => void;

class SocketService {
  private listeners: SensorCallback[] = [];
  private isConnected = false;
  private unsubscribeBus: (() => void) | null = null;

  connect(_url = 'ws://telemetry.hal.res.in/v1/fleet/stream') {
    if (this.isConnected) return;
    this.isConnected = true;

    // Start centralized Mission Operating System simulation heartbeat
    missionEngine.start();

    // Subscribe to Mission Event Bus telemetry stream
    this.unsubscribeBus = missionEventBus.subscribe('TelemetryUpdated', (payload) => {
      this.listeners.forEach((cb) => {
        try {
          cb(payload.sensors);
        } catch {
          // Silent recovery if a consumer listener throws during stream processing
        }
      });
    });

    // Push initial snapshot immediately
    const initialTel = useMissionStore.getState().telemetry;
    this.listeners.forEach((cb) => cb(initialTel));
  }

  subscribe(callback: SensorCallback): () => void {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter((cb) => cb !== callback);
    };
  }

  disconnect() {
    this.isConnected = false;
    if (this.unsubscribeBus) {
      this.unsubscribeBus();
      this.unsubscribeBus = null;
    }
    // Note: We keep missionEngine running in background if other services need it, or stop if no listeners
    if (this.listeners.length === 0) {
      missionEngine.stop();
    }
    this.listeners = [];
  }
}

export const socketService = new SocketService();
