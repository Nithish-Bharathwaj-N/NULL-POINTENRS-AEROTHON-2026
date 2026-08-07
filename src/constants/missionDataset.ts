import { ENGINE_1_DATASET, TurbojetDataPoint } from './turbojetDataset';

export interface MissionState {
  timeSec: number;               // Mission time in seconds from T+0
  phase: string;                 // Human-readable mission phase name
  phaseCode: string;             // Internal phase identifier
  // Flight Envelope
  mach: number;
  altitudeFt: number;
  tasKts: number;
  throttlePct: number;
  gLoad: number;
  aoaDeg: number;
  fuelFlowKgH: number;
  isentropicEffPct: number;
  fuelKg: number;
  // Engine Telemetry
  n1Rpm: number;
  n2Rpm: number;
  egtKelvin: number;
  t3Kelvin: number;
  t4Kelvin: number;
  p2Bar: number;
  p3Bar: number;
  vibrationG: number;
  oilPressurePsi: number;
  fuelFlowSensor: number;
  // Systems
  oilTempCelsius: number;
  hydraulicPsi: number;
  // Aircraft health
  engineHealth: number;
  // Derived
  pressureRatio: number;
  thrustKN: number;
  sfcKgDaNH: number;
  // Anomaly flag
  anomaly: any;
  anomalySubsystem?: string;
}

export const MISSION_DATASET: MissionState[] = ENGINE_1_DATASET.map((d: TurbojetDataPoint) => ({
  ...d,
  anomaly: d.anomaly as any,
}));

export const MISSION_TOTAL_DURATION_SEC = MISSION_DATASET[MISSION_DATASET.length - 1].timeSec;
