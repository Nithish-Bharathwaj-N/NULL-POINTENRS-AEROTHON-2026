// HAL Mission Control - Aerospace Design Tokens (C Palette)
export const C = {
  navy: '#003366', // Primary Brand / Header / Active Borders
  green: '#00A86B', // Nominal / Healthy / Mission Ready
  gold: '#D4AF37', // Warning / QRA Alert / Caution
  blue: '#1E90FF', // Accent / Telemetry / Airborne
  bg: '#F4F6F8', // Engineering Workstation Background
  panel: '#FFFFFF', // Card and Dock Surface
} as const;

export const THEME_CONFIG = {
  hudFont: 'JetBrains Mono, monospace',
  uiFont: 'Rajdhani, sans-serif',
  refreshRateHz: 1,
  chartAnimationMs: 300,
} as const;
