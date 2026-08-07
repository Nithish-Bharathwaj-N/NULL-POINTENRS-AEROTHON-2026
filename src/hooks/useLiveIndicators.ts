// HAL Mission Control — Live Indicator Hook
// Returns real-time UTC clock, packet counter, signal quality, heartbeat pulse.
// Zero layout impact — purely data.

import { useEffect, useRef, useState } from 'react';
import { missionEventBus } from '@/services/missionEventBus';
import { missionPlaybackEngine } from '@/services/missionPlaybackEngine';

export interface LiveIndicators {
  utcTime: string;       // "05:15:06 UTC"
  istTime: string;       // "10:45:06 IST"
  missionTime: string;   // "T+01:08:42"
  packetCount: number;   // rolling packet counter
  signalQuality: number; // 94–100%
  heartbeat: boolean;    // alternating true/false at 1Hz
  dataRateHz: string;    // "60 FPS"
  linkStatus: 'LOCKED' | 'DEGRADED' | 'OFFLINE';
}

function formatMissionTime(timeSec: number): string {
  const h = Math.floor(timeSec / 3600);
  const m = Math.floor((timeSec % 3600) / 60);
  const s = Math.floor(timeSec % 60);
  return `T+${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function getIstTime(): string {
  try {
    const d = new Date();
    return d.toLocaleTimeString('en-IN', {
      timeZone: 'Asia/Kolkata',
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }) + ' IST';
  } catch (e) {
    const d = new Date();
    return d.toTimeString().substring(0, 8) + ' IST';
  }
}

export function useLiveIndicators(): LiveIndicators {
  const [utcTime, setUtcTime] = useState(() => {
    const d = new Date();
    return d.toISOString().substring(11, 19) + ' UTC';
  });
  const [istTime, setIstTime] = useState(getIstTime);
  const [packetCount, setPacketCount] = useState(0);
  const [signalQuality, setSignalQuality] = useState(98);
  const [heartbeat, setHeartbeat] = useState(false);
  const [missionTime, setMissionTime] = useState('T+00:00:00');
  const localPackets = useRef(0);

  useEffect(() => {
    // 1-second ticker for UTC clock, IST clock, heartbeat, signal quality, mission time
    const ticker = setInterval(() => {
      const d = new Date();
      setUtcTime(d.toISOString().substring(11, 19) + ' UTC');
      setIstTime(getIstTime());
      setHeartbeat((h) => !h);
      // Drift signal quality slightly
      setSignalQuality(Math.max(92, Math.min(100, Math.round(97 + (Math.random() - 0.5) * 4))));
      setMissionTime(formatMissionTime(Math.round(missionPlaybackEngine.getTimeSec())));
    }, 1000);

    // Subscribe to packet events
    const unsub = missionEventBus.subscribe('TelemetryUpdated', () => {
      localPackets.current += 1;
      setPacketCount(localPackets.current);
    });

    return () => {
      clearInterval(ticker);
      unsub();
    };
  }, []);

  return {
    utcTime,
    istTime,
    missionTime,
    packetCount,
    signalQuality,
    heartbeat,
    dataRateHz: '60 FPS',
    linkStatus: 'LOCKED',
  };
}
