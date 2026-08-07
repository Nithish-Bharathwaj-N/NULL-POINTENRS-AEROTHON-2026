// HAL Mission Control - Zustand Real-Time Telemetry Ring Buffer Store
import { create } from 'zustand';
import { TelemetrySensor, TransducerChannel } from '@/types';
import { OPERATIONAL_TELEMETRY } from '@/constants';

interface TelemetryHistoryPoint {
  timeSec: number;
  timestamp: string;
  sensors: TelemetrySensor;
}

interface TelemetryStoreState {
  isConnected: boolean;
  isLiveStreaming: boolean;
  bufferRateHz: number;
  latestReadings: TelemetrySensor;
  historyBuffer: TelemetryHistoryPoint[];
  activeChannels: TransducerChannel[];
  setConnected: (val: boolean) => void;
  toggleLiveStreaming: () => void;
  setBufferRateHz: (hz: number) => void;
  pushReading: (reading: TelemetrySensor, timeSec: number) => void;
  setActiveChannels: (channels: TransducerChannel[]) => void;
}

export const useTelemetryStore = create<TelemetryStoreState>((set) => ({
  isConnected: true,
  isLiveStreaming: true,
  bufferRateHz: 1,
  latestReadings: OPERATIONAL_TELEMETRY,
  historyBuffer: [
    { timeSec: 0, timestamp: '11:40:00 UTC', sensors: OPERATIONAL_TELEMETRY },
  ],
  activeChannels: [],
  setConnected: (val) => set({ isConnected: val }),
  toggleLiveStreaming: () => set((state) => ({ isLiveStreaming: !state.isLiveStreaming })),
  setBufferRateHz: (hz) => set({ bufferRateHz: hz }),
  pushReading: (reading, timeSec) =>
    set((state) => {
      const timestamp = new Date().toISOString().substring(11, 19) + ' UTC';
      const newPoint: TelemetryHistoryPoint = { timeSec, timestamp, sensors: reading };
      const nextBuffer = [...state.historyBuffer, newPoint].slice(-600); // 10-minute ring buffer at 1Hz
      return { latestReadings: reading, historyBuffer: nextBuffer };
    }),
  setActiveChannels: (channels) => set({ activeChannels: channels }),
}));
