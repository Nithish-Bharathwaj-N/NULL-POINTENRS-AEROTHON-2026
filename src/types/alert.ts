// HAL Mission Control - Alert & Anomaly Domain Contracts
import { z } from 'zod';

export type AlertSeverity = 'CRITICAL' | 'WARNING' | 'INFO';
export type AlertCategory = 'PROPULSION' | 'AVIONICS' | 'HYDRAULICS' | 'STRUCTURE' | 'THERMAL';

export interface MitigationAction {
  id: string;
  title: string;
  actionCode: string;
  tlaReductionPct?: number;
  scheduleInspection?: boolean;
  requiresCommanderApproval: boolean;
}

export const AlertSchema = z.object({
  id: z.string(),
  engineId: z.string(),
  severity: z.custom<AlertSeverity>(),
  category: z.custom<AlertCategory>(),
  subsystemRef: z.string(),
  title: z.string(),
  description: z.string(),
  timestamp: z.string(),
  recommendedAction: z.string(),
  aiConfidencePct: z.number().min(0).max(100),
  acknowledged: z.boolean(),
});

export type Alert = z.infer<typeof AlertSchema>;
