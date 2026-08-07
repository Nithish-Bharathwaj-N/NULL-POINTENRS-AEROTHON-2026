// HAL Mission Control - Telemetry Domain Contracts
import { z } from 'zod';

export const TelemetrySensorSchema = z.object({
  n1Rpm: z.number().min(0).max(15000),
  n2Rpm: z.number().min(0).max(25000),
  egtKelvin: z.number().min(273.15).max(1600),
  oilPressurePsi: z.number().min(0).max(120),
  vibrationG: z.number().min(0).max(20),
  fuelFlowKgH: z.number().min(0).max(5000),
  t3Kelvin: z.number().min(273.15).max(1200),
  t4Kelvin: z.number().min(273.15).max(2000),
  p2Bar: z.number().min(0).max(5),
  p3Bar: z.number().min(0).max(35),
});

export type TelemetrySensor = z.infer<typeof TelemetrySensorSchema>;

export interface TelemetryPacket {
  timestamp: string;
  engineId: string;
  sensors: TelemetrySensor;
  sequenceNumber: number;
}

export interface TransducerChannel {
  id: string;
  name: string;
  sensorRef: string;
  channel: string;
  unit: string;
  current: number;
  expected: number;
  delta: number;
  minVal: number;
  maxVal: number;
  status: 'NOMINAL' | 'WARNING' | 'CRITICAL';
  arinc429Word: string;
}
