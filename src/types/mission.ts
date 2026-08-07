// HAL Mission Control - Mission & Sortie Domain Contracts
export interface FlightEnvelope {
  mach: number;
  altitudeFt: number;
  tasKts: number;
  tlaPct: number;
  loadFactorG: number;
  alphaDeg: number;
  fuelBurnRateKgH: number;
}

export interface Sortie {
  id: string;
  callsign: string;
  missionCode: string;
  aircraftTail: string;
  pilotName: string;
  takeoffUtc: string;
  etaUtc: string;
  status: 'AIRBORNE' | 'INGRESS' | 'EGRESS' | 'RTB' | 'LANDED';
  targetArea: string;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  timeSec: number;
  category: 'PROPULSION' | 'AVIONICS' | 'FLIGHT_CONTROL' | 'WEAPONS' | 'SATCOM' | 'ENVIRONMENTAL' | 'ELECTRICAL' | 'THERMAL';
  subsystemRef: string;
  title: string;
  description: string;
  severity: 'NOMINAL' | 'WARNING' | 'CRITICAL';
  telemetrySnapshot?: Record<string, number>;
}
