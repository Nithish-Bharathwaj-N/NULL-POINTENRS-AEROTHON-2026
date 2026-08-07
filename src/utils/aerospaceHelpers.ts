// HAL Mission Control - Pure Aerospace Helper Utilities

export const statusColor = (status: string): string => {
  const s = status.toUpperCase();
  if (s.includes('CRITICAL') || s.includes('AOG') || s.includes('GROUNDED') || s.includes('FAIL')) {
    return 'bg-red-500 text-white border-red-600';
  }
  if (s.includes('WARNING') || s.includes('CAUTION') || s.includes('STANDBY') || s.includes('QRA') || s.includes('URGENT') || s.includes('INSPECTION')) {
    return 'bg-amber-500 text-white border-amber-600';
  }
  if (s.includes('NOMINAL') || s.includes('COMBAT') || s.includes('READY') || s.includes('AIRBORNE') || s.includes('ROUTINE') || s.includes('COMPLETED') || s.includes('SUPERSONIC') || s.includes('PATROL')) {
    return 'bg-emerald-600 text-white border-emerald-700';
  }
  return 'bg-sky-600 text-white border-sky-700';
};

export const healthColor = (health: number): string => {
  if (health >= 90) return '#00A86B'; // HAL Emerald Green
  if (health >= 75) return '#D4AF37'; // HAL Gold / Amber Warning
  return '#EF4444'; // Critical Red
};

export const healthLabel = (health: number): string => {
  if (health >= 90) return 'NOMINAL';
  if (health >= 75) return 'WARNING';
  return 'CRITICAL';
};

export const getStageFromRef = (refOrId: string): string => {
  const r = refOrId.toLowerCase();
  if (r.includes('combustor') || r.includes('t4') || r.includes('t3')) return 'combustor';
  if (r.includes('hpc') || r.includes('p3')) return 'hpc';
  if (r.includes('lpc') || r.includes('p2')) return 'lpc';
  if (r.includes('fan') || r.includes('t1') || r.includes('p1')) return 'fan';
  if (r.includes('hpt') || r.includes('n2') || r.includes('oil')) return 'hpt';
  if (r.includes('lpt') || r.includes('n1') || r.includes('arinc') || r.includes('vib')) return 'lpt';
  if (r.includes('afterburner') || r.includes('reheat')) return 'afterburner';
  if (r.includes('nozzle') || r.includes('area')) return 'nozzle';
  return 'combustor'; // default fallback for demonstration binding
};

export const formatTime = (sec: number): string => {
  const hrs = Math.floor(sec / 3600);
  const mins = Math.floor((sec % 3600) / 60);
  const secs = Math.floor(sec % 60);
  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export const formatNumber = (num: number, decimals = 1): string => {
  return num.toLocaleString('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};
