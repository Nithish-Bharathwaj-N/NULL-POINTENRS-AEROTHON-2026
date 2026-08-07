"""
engine_state.py
===============
Centralized Single Source of Truth Engine State Manager for AEROTWIN Digital Twin.
Supported states: OFF, STARTING, IDLE, RUNNING, SHUTDOWN, FAULT

Enforces strict backend state transition safety (HTTP 409 on invalid jumps),
maintains persistent telemetry session cycle cursor, records timestamped mission logs,
and locks throttle / failure scenarios while OFF or STARTING.
"""

import time
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

class MissionLogger:
    """Internal timestamped backend mission event log."""
    def __init__(self):
        self._logs: List[Dict[str, str]] = []
        self._lock = threading.Lock()

    def log(self, event: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = {"timestamp": timestamp, "event": event}
        with self._lock:
            self._logs.append(entry)
            # Keep last 200 logs
            if len(self._logs) > 200:
                self._logs.pop(0)

    def get_logs(self) -> List[Dict[str, str]]:
        with self._lock:
            return list(self._logs)

class EngineStateManager:
    """Centralized Single Source of Truth Engine State Machine."""

    # Allowed state transition map
    VALID_TRANSITIONS = {
        "OFF": ["STARTING"],
        "STARTING": ["IDLE"],
        "IDLE": ["RUNNING", "SHUTDOWN", "FAULT"],
        "RUNNING": ["IDLE", "SHUTDOWN", "FAULT"],
        "FAULT": ["RUNNING", "IDLE", "SHUTDOWN"],
        "SHUTDOWN": ["OFF"]
    }

    def __init__(self):
        self.current_state: str = "OFF"
        self.logger = MissionLogger()
        self.cycle_cursor: int = 0
        self.throttle_pct: float = 0.0
        self.active_scenario: str = "NORMAL"
        self.startup_step: str = "STARTER MOTOR ENGAGED"
        self.startup_progress_pct: float = 0.0
        self.shutdown_progress_pct: float = 0.0
        self._lock = threading.Lock()

        # Record initial status log
        self.logger.log("System Initialized - Engine OFF")

    def get_state(self) -> str:
        with self._lock:
            return self.current_state

    def set_state(self, new_state: str, force: bool = False):
        with self._lock:
            curr = self.current_state
            if not force and new_state not in self.VALID_TRANSITIONS.get(curr, []):
                msg = f"Invalid state transition from '{curr}' to '{new_state}'. Allowed transitions from '{curr}': {self.VALID_TRANSITIONS.get(curr, [])}"
                self.logger.log(f"REJECTED TRANSITION: {curr} -> {new_state}")
                raise HTTPException(status_code=409, detail=msg)
            
            self.current_state = new_state
            self.logger.log(f"Engine State Changed: {curr} -> {new_state}")

    def request_start(self):
        with self._lock:
            if self.current_state != "OFF":
                raise HTTPException(
                    status_code=409,
                    detail=f"Cannot start engine when current state is '{self.current_state}'. Engine must be 'OFF'."
                )
            self.current_state = "STARTING"
            self.startup_progress_pct = 0.0
            self.logger.log("Engine Start Requested - Transitioning to STARTING")

        # Launch realistic 10-second startup sequence in background thread
        threading.Thread(target=self._run_startup_sequence, daemon=True).start()

    def _run_startup_sequence(self):
        steps = [
            (2.0, "STARTER MOTOR ENGAGED", 20.0),
            (2.0, "IGNITER SPARKING", 40.0),
            (2.0, "FUEL INTRODUCED", 65.0),
            (2.0, "COMBUSTION STABILIZATION", 85.0),
            (2.0, "IDLE LOCK ATTAINED", 100.0)
        ]

        for duration, step_name, progress in steps:
            time.sleep(duration)
            with self._lock:
                if self.current_state != "STARTING":
                    return # Interrupted by emergency stop
                self.startup_step = step_name
                self.startup_progress_pct = progress
                self.logger.log(f"Startup Progress ({int(progress)}%): {step_name}")

        with self._lock:
            if self.current_state == "STARTING":
                self.current_state = "IDLE"
                self.throttle_pct = 0.15 # 15% Idle throttle
                self.logger.log("Idle Stabilized - Engine Ready in IDLE State")

    def request_stop(self):
        with self._lock:
            if self.current_state in ["OFF", "SHUTDOWN"]:
                raise HTTPException(
                    status_code=409,
                    detail=f"Cannot stop engine when current state is '{self.current_state}'."
                )
            self.current_state = "SHUTDOWN"
            self.shutdown_progress_pct = 0.0
            self.logger.log("Engine Stop Requested - Transitioning to SHUTDOWN")

        # Launch 8-second realistic coast-down sequence in background thread
        threading.Thread(target=self._run_shutdown_sequence, daemon=True).start()

    def _run_shutdown_sequence(self):
        steps = [
            (2.0, "FUEL CUTOFF", 25.0),
            (2.0, "ROTOR DEACCELERATION", 60.0),
            (2.0, "THERMAL DISSIPATION", 90.0),
            (2.0, "ROTOR STOPPED", 100.0)
        ]

        for duration, step_name, progress in steps:
            time.sleep(duration)
            with self._lock:
                if self.current_state != "SHUTDOWN":
                    return
                self.shutdown_progress_pct = progress
                self.logger.log(f"Shutdown Progress ({int(progress)}%): {step_name}")

        with self._lock:
            if self.current_state == "SHUTDOWN":
                self.current_state = "OFF"
                self.throttle_pct = 0.0
                self.active_scenario = "NORMAL"
                self.logger.log("Engine Off - All Subsystems Static")

    def set_throttle(self, pct: float) -> float:
        with self._lock:
            if self.current_state in ["OFF", "STARTING"]:
                raise HTTPException(
                    status_code=409,
                    detail=f"Throttle is LOCKED while engine is in '{self.current_state}' state."
                )
            
            clamp_pct = max(0.0, min(1.0, pct))
            self.throttle_pct = clamp_pct
            
            if clamp_pct > 0.18 and self.current_state == "IDLE":
                self.current_state = "RUNNING"
                self.logger.log(f"Throttle Advanced to {int(clamp_pct*100)}% - State: RUNNING")
            elif clamp_pct <= 0.18 and self.current_state == "RUNNING":
                self.current_state = "IDLE"
                self.logger.log("Throttle Reduced to Idle - State: IDLE")
            else:
                self.logger.log(f"Throttle Adjusted to {int(clamp_pct*100)}%")

            return self.throttle_pct

    def set_scenario(self, scenario_key: str):
        with self._lock:
            if self.current_state in ["OFF", "STARTING"]:
                raise HTTPException(
                    status_code=409,
                    detail=f"Failure injection is DISABLED while engine is in '{self.current_state}' state."
                )
            
            old_scen = self.active_scenario
            self.active_scenario = scenario_key.upper()
            if scenario_key.upper() != "NORMAL":
                self.current_state = "FAULT"
                self.logger.log(f"FAULT INJECTED: {scenario_key.upper()}")
            else:
                self.current_state = "RUNNING" if self.throttle_pct > 0.18 else "IDLE"
                self.logger.log("Fault Cleared - Returned to Normal Operation")

# Global Singleton Instance
state_manager = EngineStateManager()
