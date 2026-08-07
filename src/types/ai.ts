// HAL Mission Control - AI Diagnostics & XAI Explainability Contracts
export interface WeibullDistribution {
  shapeBeta: number;
  scaleEta: number;
  meanRulHours: number;
  confidenceLowerHrs: number;
  confidenceUpperHrs: number;
  modelType: 'AeroNet-v4' | 'Weibull-Proportional' | 'Kalman-LSTM';
}

export interface ShapleyFactor {
  parameter: string;
  arincWord: string;
  shapleyValuePct: number;
  direction: 'DEGRADING' | 'STABILIZING';
  description: string;
}

export interface AIInference {
  engineId: string;
  timestamp: string;
  healthIndex: number;
  weibull: WeibullDistribution;
  primaryFailureMode: string;
  failureConfidencePct: number;
  shapleyFactors: ShapleyFactor[];
}
