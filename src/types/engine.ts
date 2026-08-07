// HAL Mission Control - Engine Domain Contracts
import { z } from 'zod';

export type SubsystemStageRef = 'fan' | 'lpc' | 'hpc' | 'combustor' | 'hpt' | 'lpt' | 'afterburner' | 'nozzle';

export const SubsystemStageSchema = z.object({
  ref: z.custom<SubsystemStageRef>(),
  name: z.string(),
  health: z.number().min(0).max(100),
  temp: z.number(),
  pressure: z.number(),
  vibration: z.number(),
  status: z.enum(['NOMINAL', 'WARNING', 'CRITICAL']),
});

export type SubsystemStage = z.infer<typeof SubsystemStageSchema>;

export interface ThermodynamicResidual {
  stage: string;
  parameter: string;
  actual: number;
  expected: number;
  residual: number;
  unit: string;
  status: 'NOMINAL' | 'WARNING' | 'CRITICAL';
}

export interface VibrationProfile {
  spool: 'N1' | 'N2';
  frequencyHz: number;
  amplitudeG: number;
  phaseDeg: number;
  thresholdG: number;
}
