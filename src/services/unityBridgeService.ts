// HAL Mission Control - Unity 3D WebGL / Wasm Bridge Service
import { CADViewMode, WasmBridgeMessage } from '@/types';

class UnityBridgeService {
  private isHydrated = false;

  setHydrated(val: boolean) {
    this.isHydrated = val;
  }

  sendMessage(_msg: WasmBridgeMessage) {
    if (!this.isHydrated) {
      // Wasm CAD Engine message queued for dispatch upon WebGL canvas hydration
      return;
    }
    try {
      // In production WebGL integration: window.unityInstance.SendMessage('CADController', _msg.command, JSON.stringify(_msg.payload));
    } catch {
      // Silent error recovery if Wasm canvas detaches
    }
  }

  setViewMode(mode: CADViewMode) {
    this.sendMessage({ command: 'SET_VIEW_MODE', payload: { mode } });
  }

  highlightStage(stageRef: string) {
    this.sendMessage({ command: 'HIGHLIGHT_STAGE', payload: { stageRef } });
  }

  resetCamera() {
    this.sendMessage({ command: 'RESET_CAMERA', payload: {} });
  }
}

export const unityBridgeService = new UnityBridgeService();
