// HAL Mission Control - Legacy Simulation Wrapper
// Delegates all start/stop requests to the centralized Mission Playback Engine (RAF loop).

import { missionPlaybackEngine } from './missionPlaybackEngine';

class MissionEngine {
  public start(): void {
    console.info('[MissionEngine] Delegating start to centralized MissionPlaybackEngine...');
    missionPlaybackEngine.start();
  }

  public stop(): void {
    console.info('[MissionEngine] Delegating stop to centralized MissionPlaybackEngine...');
    missionPlaybackEngine.stop();
  }
}

export const missionEngine = new MissionEngine();
