// HAL Mission Control - Live Overview Feature Hooks
import { useMemo } from 'react';
import { useAircraftStore, useUiStore } from '@/stores';
import { useMissionStore } from '@/stores/useMissionStore';
import { getStageFromRef } from '@/utils';

export const useOverviewData = () => {
  const { selectedAircraft } = useAircraftStore();
  const { selectedStageRef, setSelectedStageRef, selectedAlert, setSelectedAlert } = useUiStore();
  const { telemetry, missionPhase, flightEnvelope } = useMissionStore();

  const summaryMetrics = useMemo(() => {
    const egtDelta = Math.round(telemetry.egtKelvin - 1103.15);
    const isEgtHigh = telemetry.egtKelvin > 1200;
    const isVibHigh = telemetry.vibrationG > 1.8;

    return [
      { label: 'Active Combat Sortie', val: missionPhase.split(' ')[0] || 'OP SINDHUR', sub: `Mach ${flightEnvelope.mach.toFixed(2)} • ${flightEnvelope.altitudeFt.toLocaleString()} Ft`, status: 'ACTIVE' },
      { label: 'Propulsion Health', val: `${selectedAircraft.engineHealth}%`, sub: 'GE F404-IN20 #88219', status: selectedAircraft.engineHealth >= 90 ? 'NOMINAL' : 'WARNING' },
      { label: 'Time To Overhaul (RUL)', val: `${selectedAircraft.tboRulHrs} Hrs`, sub: 'Next: Borescope Stage 1', status: selectedAircraft.tboRulHrs > 300 ? 'NOMINAL' : 'WARNING' },
      { label: 'EGT Thermal Margin', val: `${egtDelta > 0 ? '+' : ''}${egtDelta}°C Δ`, sub: `Peak T4: ${Math.round(telemetry.t4Kelvin - 273.15)}°C`, status: isEgtHigh ? 'CRITICAL' : 'WARNING' },
      { label: 'Vibration RMS', val: `${telemetry.vibrationG.toFixed(2)} G`, sub: 'N2 Spool Harmonic', status: isVibHigh ? 'CRITICAL' : 'NOMINAL' },
      { label: 'Link-17 SATCOM', val: 'LOCKED', sub: `Downlink: ${Math.round(100 * (flightEnvelope.isentropicEffPct / 92.4))} Hz`, status: 'ACTIVE' },
    ];
  }, [selectedAircraft, telemetry, missionPhase, flightEnvelope]);

  const handleStageSelect = (refOrId: string | null) => {
    if (!refOrId) {
      setSelectedStageRef(null);
      return;
    }
    const target = getStageFromRef(refOrId);
    setSelectedStageRef(target === selectedStageRef ? null : target);
  };

  return {
    ac: selectedAircraft,
    selectedStageRef,
    selectedAlert,
    setSelectedAlert,
    summaryMetrics,
    handleStageSelect,
  };
};
