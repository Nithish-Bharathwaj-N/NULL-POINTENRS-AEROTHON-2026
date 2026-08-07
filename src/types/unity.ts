// HAL Mission Control - Unity 3D & Digital Twin Contracts
export type CADViewMode = 'NORMAL ASSEMBLY' | 'THERMAL FIELD' | 'PRESSURE FIELD' | 'STRESS LOAD (FEA)' | 'EXPLODED CAD' | 'X-RAY SPOOLS' | 'SIMULATED FEA';

export interface DigitalTwinNode {
  id: string;
  name: string;
  partNumber: string;
  stageRef: string;
  coordinates: [number, number, number];
  healthPct: number;
  temperatureCelcius: number;
  stressMpa: number;
}

export interface WasmBridgeMessage {
  command: 'SELECT_PART' | 'SET_VIEW_MODE' | 'ZOOM_TO' | 'HIGHLIGHT_STAGE' | 'RESET_CAMERA';
  payload: Record<string, unknown>;
}
