// HAL Mission Control - Aircraft Domain Contracts
import { z } from 'zod';

export type MissionStatus = 'Combat Patrol' | 'Standby / QRA' | 'Supersonic Test' | 'CAP Patrol' | 'QRA Intercept' | 'Escort' | 'SATCOM Calib' | 'Envelope Open';
export type PriorityLevel = 'Alpha' | 'Bravo' | 'Charlie';

export const FleetMemberSchema = z.object({
  id: z.string(),
  tail: z.string(),
  squadron: z.string(),
  base: z.string(),
  status: z.string(),
  health: z.number().min(0).max(100),
  engineHealth: z.number().min(0).max(100),
  airframeHealth: z.number().min(0).max(100),
  fuelPct: z.number().min(0).max(100),
  fuelKg: z.number(),
  sortieHours: z.number(),
  tboRulHrs: z.number(),
  missionType: z.string(),
  pilot: z.string(),
  crew: z.string(),
  location: z.string(),
  warning: z.string().nullable(),
});

export type FleetMember = z.infer<typeof FleetMemberSchema>;

export interface Squadron {
  id: string;
  name: string;
  callsign: string;
  base: string;
  aircraftCount: number;
}

export interface AirBase {
  id: string;
  name: string;
  code: string;
  location: string;
  shelters: number;
}
