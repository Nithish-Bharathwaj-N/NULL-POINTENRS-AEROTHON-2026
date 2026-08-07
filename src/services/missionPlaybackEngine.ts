// HAL Mission Control — Mission Playback Engine
// Single requestAnimationFrame loop driving the entire platform.
// Replaces all scattered setInterval timers with one master clock.

import { MISSION_DATASET, MISSION_TOTAL_DURATION_SEC, MissionState } from '@/constants/missionDataset';
import { useMissionStore } from '@/stores/useMissionStore';
import { useTelemetryStore } from '@/stores/useTelemetryStore';
import { useAircraftStore } from '@/stores/useAircraftStore';
import { missionEventBus } from './missionEventBus';
import { Alert, TimelineEvent } from '@/types';

// ── Interpolation helpers ─────────────────────────────────────────────────────

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function lerpState(from: MissionState, to: MissionState, t: number): MissionState {
  const n = (a: number, b: number) => Number(lerp(a, b, t).toFixed(4));
  return {
    ...to,
    timeSec: n(from.timeSec, to.timeSec),
    mach: n(from.mach, to.mach),
    altitudeFt: n(from.altitudeFt, to.altitudeFt),
    tasKts: n(from.tasKts, to.tasKts),
    throttlePct: n(from.throttlePct, to.throttlePct),
    gLoad: n(from.gLoad, to.gLoad),
    aoaDeg: n(from.aoaDeg, to.aoaDeg),
    fuelFlowKgH: n(from.fuelFlowKgH, to.fuelFlowKgH),
    isentropicEffPct: n(from.isentropicEffPct, to.isentropicEffPct),
    fuelKg: n(from.fuelKg, to.fuelKg),
    n1Rpm: n(from.n1Rpm, to.n1Rpm),
    n2Rpm: n(from.n2Rpm, to.n2Rpm),
    egtKelvin: n(from.egtKelvin, to.egtKelvin),
    t3Kelvin: n(from.t3Kelvin, to.t3Kelvin),
    t4Kelvin: n(from.t4Kelvin, to.t4Kelvin),
    p2Bar: n(from.p2Bar, to.p2Bar),
    p3Bar: n(from.p3Bar, to.p3Bar),
    vibrationG: n(from.vibrationG, to.vibrationG),
    oilPressurePsi: n(from.oilPressurePsi, to.oilPressurePsi),
    fuelFlowSensor: n(from.fuelFlowSensor, to.fuelFlowSensor),
    oilTempCelsius: n(from.oilTempCelsius, to.oilTempCelsius),
    hydraulicPsi: n(from.hydraulicPsi, to.hydraulicPsi),
    engineHealth: n(from.engineHealth, to.engineHealth),
    pressureRatio: n(from.pressureRatio, to.pressureRatio),
    thrustKN: n(from.thrustKN, to.thrustKN),
    sfcKgDaNH: n(from.sfcKgDaNH, to.sfcKgDaNH),
    phase: t < 0.5 ? from.phase : to.phase,
    phaseCode: t < 0.5 ? from.phaseCode : to.phaseCode,
    anomaly: t >= 0.5 ? to.anomaly : from.anomaly,
    anomalySubsystem: t >= 0.5 ? to.anomalySubsystem : from.anomalySubsystem,
  };
}

// ── Noise for analog sensor feel ────────────────────────────────────────────

function noise(amplitude: number): number {
  return (Math.random() - 0.5) * 2 * amplitude;
}

// ── Track which anomalies have already been published ───────────────────────

const publishedAnomalies = new Set<string>();
const publishedPhases = new Set<string>();

// ── Main Engine Class ────────────────────────────────────────────────────────

class MissionPlaybackEngine {
  private rafId: number | null = null;
  private isRunning = false;
  private isPaused = false;

  // Mission time in seconds (dataset units)
  private missionTimeSec = MISSION_DATASET[4].timeSec; // Start at patrol (T+14:00)
  private speed = 1.0; // 1x Real-time speed for smooth, calm, readable telemetry
  private lastRealTimeMs = 0;
  private lastStoreUpdateMs = 0;
  private loopMode: 'loop' | 'stop' = 'loop';

  // Packet tracking for live indicators
  public packetCount = 0;

  public start(): void {
    if (this.isRunning) return;
    this.isRunning = true;
    this.isPaused = false;
    this.lastRealTimeMs = performance.now();
    publishedAnomalies.clear();
    publishedPhases.clear();
    console.info('[MissionPlaybackEngine] Single RAF loop started at', this.speed + 'x speed');
    this.loop();
  }

  public stop(): void {
    this.isRunning = false;
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    console.info('[MissionPlaybackEngine] Stopped.');
  }

  public pause(): void {
    this.isPaused = true;
    useMissionStore.getState().setSimulationSettings({ simulationSpeed: 0 });
  }

  public resume(): void {
    this.isPaused = false;
    this.lastRealTimeMs = performance.now();
    useMissionStore.getState().setSimulationSettings({ simulationSpeed: this.speed });
  }

  public seek(timeSec: number): void {
    this.missionTimeSec = Math.max(0, Math.min(MISSION_TOTAL_DURATION_SEC, timeSec));
    this.lastRealTimeMs = performance.now();
    this.lastStoreUpdateMs = 0;
  }

  public setSpeed(multiplier: number): void {
    this.speed = multiplier;
    this.lastStoreUpdateMs = 0;
    useMissionStore.getState().setSimulationSettings({ simulationSpeed: multiplier });
  }

  public getTimeSec(): number {
    return this.missionTimeSec;
  }

  public getIsRunning(): boolean {
    return this.isRunning && !this.isPaused;
  }

  // ── Core RAF Loop ─────────────────────────────────────────────────────────

  private loop = (): void => {
    if (!this.isRunning) return;

    const nowMs = performance.now();
    const deltaMs = nowMs - this.lastRealTimeMs;
    this.lastRealTimeMs = nowMs;

    if (!this.isPaused) {
      // Advance mission clock
      this.missionTimeSec += (deltaMs / 1000) * this.speed;

      // Loop handling
      if (this.missionTimeSec > MISSION_TOTAL_DURATION_SEC) {
        if (this.loopMode === 'loop') {
          this.missionTimeSec = 0;
          publishedAnomalies.clear();
          publishedPhases.clear();
        } else {
          this.missionTimeSec = MISSION_TOTAL_DURATION_SEC;
          this.pause();
        }
      }

      // Compute interpolated state
      const state = this.interpolate(this.missionTimeSec);

      // Apply subtle analog sensor noise (calm, steady, realistic transducer feel)
      const noisyState: MissionState = {
        ...state,
        n1Rpm: Math.round(state.n1Rpm + noise(2)),
        n2Rpm: Math.round(state.n2Rpm + noise(3)),
        egtKelvin: Number((state.egtKelvin + noise(0.2)).toFixed(1)),
        t3Kelvin: Number((state.t3Kelvin + noise(0.1)).toFixed(1)),
        t4Kelvin: Number((state.t4Kelvin + noise(0.2)).toFixed(1)),
        p2Bar: Number((state.p2Bar + noise(0.002)).toFixed(3)),
        p3Bar: Number((state.p3Bar + noise(0.01)).toFixed(2)),
        vibrationG: Number((state.vibrationG + noise(0.005)).toFixed(2)),
        oilPressurePsi: Number((state.oilPressurePsi + noise(0.05)).toFixed(1)),
      };

      // Throttle store updates to a steady 1Hz (1,000ms) interval for clean, readable numbers
      if (nowMs - this.lastStoreUpdateMs >= 1000) {
        this.lastStoreUpdateMs = nowMs;
        this.applyToStores(noisyState);
        this.checkEventTriggers(state);
        this.packetCount++;
      }
    }

    this.rafId = requestAnimationFrame(this.loop);
  };

  // ── Interpolation ─────────────────────────────────────────────────────────

  private interpolate(timeSec: number): MissionState {
    const data = MISSION_DATASET;

    // Past end
    if (timeSec >= data[data.length - 1].timeSec) return data[data.length - 1];
    // Before start
    if (timeSec <= data[0].timeSec) return data[0];

    // Find surrounding rows
    let fromIdx = 0;
    for (let i = 0; i < data.length - 1; i++) {
      if (data[i].timeSec <= timeSec && data[i + 1].timeSec > timeSec) {
        fromIdx = i;
        break;
      }
    }
    const from = data[fromIdx];
    const to = data[fromIdx + 1];
    const t = (timeSec - from.timeSec) / (to.timeSec - from.timeSec);
    return lerpState(from, to, Math.max(0, Math.min(1, t)));
  }

  // ── Apply state to all Zustand stores ────────────────────────────────────

  private applyToStores(s: MissionState): void {
    const missionStore = useMissionStore.getState();
    const aircraftStore = useAircraftStore.getState();
    const telStore = useTelemetryStore.getState();

    const telemetry = {
      n1Rpm: s.n1Rpm,
      n2Rpm: s.n2Rpm,
      egtKelvin: s.egtKelvin,
      oilPressurePsi: s.oilPressurePsi,
      vibrationG: s.vibrationG,
      fuelFlowKgH: s.fuelFlowSensor,
      t3Kelvin: s.t3Kelvin,
      t4Kelvin: s.t4Kelvin,
      p2Bar: s.p2Bar,
      p3Bar: s.p3Bar,
    };

    const envelope = {
      mach: s.mach,
      altitudeFt: s.altitudeFt,
      tasKts: s.tasKts,
      throttlePct: s.throttlePct,
      gLoad: s.gLoad,
      aoaDeg: s.aoaDeg,
      fuelFlowKgH: s.fuelFlowKgH,
      isentropicEffPct: s.isentropicEffPct,
    };

    const sys = {
      oilPressurePsi: s.oilPressurePsi,
      vibrationG: s.vibrationG,
      oatCelsius: s.oilTempCelsius,
      hydraulicPressPsi: s.hydraulicPsi,
    };

    // Update mission store
    missionStore.updateTelemetry(telemetry, envelope, sys);
    missionStore.tickTime(0); // Reset — mission time comes from playback engine
    useMissionStore.setState({ missionTimeSec: this.missionTimeSec });
    if (s.phase !== missionStore.missionPhase) {
      missionStore.setMissionPhase(s.phase);
    }

    // Update subsystem stages from live state
    const updatedStages = missionStore.subsystemStages.map((stg) => {
      let temp = stg.temp;
      let pressure = stg.pressure;
      let vibration = stg.vibration;
      let status: 'NOMINAL' | 'WARNING' | 'CRITICAL' = 'NOMINAL';
      let health = stg.health;

      switch (stg.ref) {
        case 'fan':
          pressure = Number(s.p2Bar.toFixed(2));
          temp = Math.round(s.t3Kelvin * 0.3 - 273.15 + 25);
          vibration = Number((s.vibrationG * 0.65).toFixed(2));
          break;
        case 'lpc':
          pressure = Number((s.p2Bar * 2.8).toFixed(2));
          temp = Math.round(s.t3Kelvin * 0.55 - 273.15);
          vibration = Number((s.vibrationG * 0.8).toFixed(2));
          break;
        case 'hpc':
          pressure = Number(s.p3Bar.toFixed(1));
          temp = Math.round(s.t3Kelvin - 273.15);
          vibration = Number((s.vibrationG * 1.05).toFixed(2));
          if (s.anomaly === 'COMPRESSOR_SURGE') { status = 'CRITICAL'; health = Math.max(60, stg.health - 0.05); }
          break;
        case 'combustor':
          pressure = Number((s.p3Bar * 0.96).toFixed(1));
          temp = Math.round(s.t4Kelvin - 273.15);
          vibration = Number((s.vibrationG * 1.1).toFixed(2));
          if (s.anomaly === 'EGT_OVERTEMP') { status = 'CRITICAL'; health = Math.max(55, stg.health - 0.08); }
          else if (temp > 1400) status = 'WARNING';
          break;
        case 'hpt':
          temp = Math.round(s.egtKelvin - 273.15 + 50);
          pressure = Number((s.p3Bar * 0.88).toFixed(1));
          vibration = Number((s.vibrationG * 1.15).toFixed(2));
          if (temp > 1350) status = 'WARNING';
          break;
        case 'lpt':
          temp = Math.round(s.egtKelvin - 273.15 - 80);
          pressure = Number((s.p3Bar * 0.45).toFixed(1));
          vibration = Number((s.vibrationG * 0.9).toFixed(2));
          break;
        case 'afterburner':
          temp = Math.round(s.t4Kelvin * 0.85 - 273.15);
          pressure = Number((s.p2Bar * 0.95).toFixed(2));
          vibration = Number((s.vibrationG * 0.75).toFixed(2));
          break;
        case 'nozzle':
          temp = Math.round(s.egtKelvin - 273.15 - 120);
          pressure = Number((s.p2Bar * 0.6).toFixed(2));
          vibration = Number((s.vibrationG * 0.55).toFixed(2));
          break;
        default:
          break;
      }

      if (status === 'NOMINAL') {
        if (vibration > 2.0 || pressure > 29.5) status = 'CRITICAL';
        else if (vibration > 1.6 || pressure > 27.0 || temp > 1450) status = 'WARNING';
      }

      return { ...stg, temp, pressure, vibration, status, health };
    });
    missionStore.updateSubsystems(updatedStages);

    // Update AI Inference (Weibull RUL)
    const avgHealth = updatedStages.reduce((a, s) => a + s.health, 0) / updatedStages.length;
    const healthDrop = 100 - avgHealth;
    const rul = Math.max(45, Math.round(s.engineHealth * 7.2));
    const currentInf = missionStore.aiInference;
    missionStore.updateAiInference({
      ...currentInf,
      healthIndex: Number(s.engineHealth.toFixed(1)),
      weibull: {
        ...currentInf.weibull,
        meanRulHours: rul,
        confidenceLowerHrs: Math.round(rul * 0.92),
        confidenceUpperHrs: Math.round(rul * 1.08),
      },
      failureConfidencePct: Number(Math.min(99, healthDrop * 2.1).toFixed(1)),
    });

    // Update fleet / aircraft fuel & health
    const tail = aircraftStore.selectedTail;
    const fuelKg = Math.round(s.fuelKg);
    const fuelPct = Math.round((s.fuelKg / 2480) * 100);
    useAircraftStore.setState((state) => ({
      fleet: state.fleet.map((a) =>
        a.tail === tail
          ? { ...a, fuelKg, fuelPct, engineHealth: Math.round(s.engineHealth), health: Math.round(s.engineHealth) }
          : a
      ),
      selectedAircraft: {
        ...state.selectedAircraft,
        fuelKg,
        fuelPct,
        engineHealth: Math.round(s.engineHealth),
        health: Math.round(s.engineHealth),
        tboRulHrs: rul,
      },
    }));

    // Push to telemetry ring buffer (throttled to ~1Hz via packetCount)
    if (this.packetCount % 60 === 0) {
      telStore.pushReading(telemetry, this.missionTimeSec);
      missionEventBus.publish('TelemetryUpdated', { timeSec: this.missionTimeSec, sensors: telemetry });
    }
  }

  // ── Event Triggers ────────────────────────────────────────────────────────

  private checkEventTriggers(state: MissionState): void {
    const missionStore = useMissionStore.getState();

    // Fuel low warning
    if (state.fuelKg < 800 && state.fuelKg > 0 && !publishedAnomalies.has('FUEL_LOW')) {
      publishedAnomalies.add('FUEL_LOW');
      missionEventBus.publish('FuelLow', { fuelPct: Math.round((state.fuelKg / 2480) * 100), fuelKg: Math.round(state.fuelKg) });
    }

    // Anomaly cascade — fires once per anomaly type
    if (state.anomaly && !publishedAnomalies.has(state.anomaly)) {
      publishedAnomalies.add(state.anomaly);
      this.triggerAnomalyCascade(state, missionStore);
    }

    // Mission phase change events
    const phaseKey = state.phaseCode;
    if (!publishedPhases.has(phaseKey)) {
      publishedPhases.add(phaseKey);
      missionEventBus.publish('MissionPhaseChanged', { phase: state.phase });

      // Add phase start timeline event
      const ev: TimelineEvent = {
        id: `EV-PHASE-${phaseKey}-${Date.now()}`,
        timeSec: this.missionTimeSec,
        timestamp: new Date().toISOString().substring(11, 19) + ' UTC',
        category: 'PROPULSION',
        subsystemRef: 'overall',
        title: `Mission Phase: ${state.phase}`,
        description: `Aircraft entered ${state.phase} at T+${formatTimeSec(this.missionTimeSec)}.`,
        severity: 'NOMINAL',
      };
      missionStore.addTimelineEvent(ev);
    }
  }

  private triggerAnomalyCascade(state: MissionState, missionStore: ReturnType<typeof useMissionStore.getState>): void {
    const ts = new Date().toISOString().substring(11, 19) + ' UTC';
    const subsystem = state.anomalySubsystem ?? 'combustor';

    // 1. Raise Alert
    const alert: Alert = {
      id: `ALT-AUTO-${Date.now()}`,
      engineId: 'TJ04-SER-88219',
      severity: 'CRITICAL',
      category: 'PROPULSION',
      subsystemRef: subsystem,
      title: getAnomalyTitle(state.anomaly!),
      description: getAnomalyDescription(state),
      timestamp: ts,
      recommendedAction: getAnomalyAction(state.anomaly!),
      aiConfidencePct: 96.4,
      acknowledged: false,
    };
    missionStore.addAlert(alert);

    // 2. Add Timeline Event
    const ev: TimelineEvent = {
      id: `EV-ANOMALY-${Date.now()}`,
      timeSec: this.missionTimeSec,
      timestamp: ts,
      category: 'THERMAL',
      subsystemRef: subsystem,
      title: `⚠ ANOMALY DETECTED: ${getAnomalyTitle(state.anomaly!)}`,
      description: getAnomalyDescription(state),
      severity: 'CRITICAL',
    };
    missionStore.addTimelineEvent(ev);

    // 3. Select affected stage in UI (Digital Twin highlights)
    missionEventBus.publish('EngineStageSelected', { stageRef: subsystem });
    missionEventBus.publish('DigitalTwinSelectionChanged', { stageRef: subsystem });

    // 4. Publish replay bookmark
    missionEventBus.publish('ReplayBookmarkAdded', {
      timeSec: this.missionTimeSec,
      label: getAnomalyTitle(state.anomaly!),
    });

    // 5. Auto-select the anomaly subsystem (cross-workstation sync)
    // Import avoidance: directly dispatch to useUiStore
    import('@/stores/useUiStore').then(({ useUiStore }) => {
      useUiStore.getState().setSelectedStageRef(subsystem);
    });

    console.warn(`[MissionPlaybackEngine] ⚠ Anomaly cascade fired: ${state.anomaly} on ${subsystem}`);
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatTimeSec(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function getAnomalyTitle(anomaly: string): string {
  const titles: Record<string, string> = {
    COMPRESSOR_SURGE: 'HPC Compressor Surge / Stall',
    EGT_OVERTEMP: 'Combustor EGT Over-Temperature',
    VIBRATION_HIGH: 'Critical Spool Vibration RMS',
    OIL_LOW: 'Bearing Oil Pressure Loss',
    FUEL_LEAK: 'Rapid Fuel Tank Leakage',
    BIRD_STRIKE: 'Foreign Object / Bird Strike Ingestion',
  };
  return titles[anomaly] ?? anomaly;
}

function getAnomalyDescription(state: MissionState): string {
  const t4C = Math.round(state.t4Kelvin - 273.15);
  const p3 = state.p3Bar.toFixed(1);
  const vib = state.vibrationG.toFixed(2);
  if (state.anomaly === 'EGT_OVERTEMP') {
    return `T4 Turbine Inlet Temp: ${t4C}°C (limit 1650°C). EGT: ${Math.round(state.egtKelvin - 273.15)}°C. AI Weibull model predicts accelerated fatigue on HPT blades.`;
  }
  if (state.anomaly === 'COMPRESSOR_SURGE') {
    return `P3 HPC Discharge Pressure: ${p3} Bar oscillating ±4 Bar. Vibration RMS: ${vib}G. Acoustic surge signature detected on ARINC-429 Channel 4.`;
  }
  return `Anomaly detected on ${state.anomalySubsystem?.toUpperCase()}. P3: ${p3} Bar, T4: ${t4C}°C, Vib: ${vib}G.`;
}

function getAnomalyAction(anomaly: string): string {
  const actions: Record<string, string> = {
    COMPRESSOR_SURGE: 'Reduce throttle by 15% (TLA < 72%). Check inlet guide vane schedule. Schedule HPC borescope post-sortie.',
    EGT_OVERTEMP: 'Reduce throttle to 65% TLA. Monitor EGT trend. Initiate RTB if EGT exceeds 1700°C. HPT blade inspection required.',
    VIBRATION_HIGH: 'Reduce N1 RPM by 8%. Monitor spool balance. Fan/LPC blade inspection at next available gate.',
    OIL_LOW: 'Monitor oil pressure trend. Do not exceed 80% throttle. Bearing seizure risk if OIL < 45 PSI.',
    FUEL_LEAK: 'Confirm external drop tank jettison. Activate fuel crossfeed. RTB immediately. Landing weight within limits.',
    BIRD_STRIKE: 'Maintain N1 < 85%. Check for compressor damage. RTB immediately. Full fan/LPC borescope inspection required.',
  };
  return actions[anomaly] ?? 'Investigate and report to HAL Propulsion Engineering team.';
}

// ── Singleton Export ──────────────────────────────────────────────────────────

export const missionPlaybackEngine = new MissionPlaybackEngine();
export { formatTimeSec };
