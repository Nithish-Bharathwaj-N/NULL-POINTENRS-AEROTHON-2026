// HAL Mission Control — Mission Demo Hook
// 1-click automated sortie pipeline. Drives missionPlaybackEngine through all phases.

import { useState, useRef, useCallback } from 'react';
import { missionPlaybackEngine } from '@/services/missionPlaybackEngine';
import { MISSION_DATASET } from '@/constants/missionDataset';
import { useUiStore } from '@/stores';

export interface MissionDemoState {
  isDemoRunning: boolean;
  demoPhase: string;
  demoProgress: number; // 0–100
  startDemo: () => void;
  stopDemo: () => void;
}

export function useMissionDemo(): MissionDemoState {
  const [isDemoRunning, setIsDemoRunning] = useState(false);
  const [demoPhase, setDemoPhase] = useState('');
  const [demoProgress, setDemoProgress] = useState(0);
  const rafRef = useRef<number | null>(null);
  const { setView } = useUiStore();

  const stopDemo = useCallback(() => {
    setIsDemoRunning(false);
    setDemoPhase('');
    setDemoProgress(0);
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    // Reset to normal patrol speed
    missionPlaybackEngine.setSpeed(8);
  }, []);

  const startDemo = useCallback(() => {
    setIsDemoRunning(true);
    // Seek to beginning
    missionPlaybackEngine.seek(0);
    missionPlaybackEngine.setSpeed(20); // 20x speed for demo — full mission in ~4.5 min
    missionPlaybackEngine.resume();

    const totalDuration = MISSION_DATASET[MISSION_DATASET.length - 1].timeSec;

    const track = () => {
      const current = missionPlaybackEngine.getTimeSec();
      const progress = Math.min(100, Math.round((current / totalDuration) * 100));
      setDemoProgress(progress);

      // Find current phase label from dataset
      for (let i = MISSION_DATASET.length - 1; i >= 0; i--) {
        if (current >= MISSION_DATASET[i].timeSec) {
          setDemoPhase(MISSION_DATASET[i].phase);
          break;
        }
      }

      // Manual view selection preserved — automatic view switching disabled
      if (progress >= 100) {
        stopDemo();
        return;
      }

      rafRef.current = requestAnimationFrame(track);
    };

    rafRef.current = requestAnimationFrame(track);
  }, [stopDemo, setView]);

  return { isDemoRunning, demoPhase, demoProgress, startDemo, stopDemo };
}
