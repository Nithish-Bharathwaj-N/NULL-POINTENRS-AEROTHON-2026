"""
engine_history.py
=================
Dual-layer Engine History Store for Aerothon 2026 Digital Twin.

Architecture:
  RAM layer  — last N cycles per engine (fast inference, O(1) lookup)
  SQLite layer — complete history (persistence across server restarts)

The store also maintains a rich "experience profile" per engine:
  - Normal operating profile (mean ± std of all sensors)
  - Worst thermal load cycle
  - Worst pressure ratio cycle
  - Largest single-cycle health degradation jump
  - Longest stable operating region (|ΔHealth| < threshold)
  - Total accumulated cycles
"""

import os
import json
import sqlite3
import threading
from collections import deque
from typing import Optional, Dict, List
import numpy as np
import pandas as pd

# ─── Configuration ─────────────────────────────────────────────────────────────
RAM_BUFFER_CYCLES = 50          # fast-inference window
STABLE_HEALTH_THRESHOLD = 0.001 # |ΔHealth| < this = stable cycle
DB_TABLE = "engine_cycles"

# Default SQLite path
_DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", "..", "hal_mission_control.db"
)


class EngineExperienceProfile:
    """
    Stores rich operational memory for a single engine beyond just raw cycles.
    The Digital Twin 'experiences' these episodes and uses them for prognosis.
    """

    def __init__(self):
        self.total_cycles: int = 0
        self.normal_operating_profile: Dict = {}   # mean ± std per sensor
        self.worst_thermal_load: Optional[Dict] = None       # snapshot
        self.worst_pressure_ratio: Optional[Dict] = None     # snapshot
        self.largest_degradation_jump: Optional[Dict] = None # snapshot
        self.longest_stable_region: Dict = {"length": 0, "start_pos": 0, "end_pos": 0}
        self.current_stable_streak: int = 0
        self._sensor_accum: Dict[str, List[float]] = {}
        self._prev_overall_health: Optional[float] = None

    def update(self, frame: dict, position: int):
        """Update experience profile with a new telemetry frame."""
        self.total_cycles += 1

        # Accumulate sensor values for normal operating profile
        for key, val in frame.items():
            if isinstance(val, (int, float)) and key not in ("EngineID", "Cycle"):
                if key not in self._sensor_accum:
                    self._sensor_accum[key] = []
                self._sensor_accum[key].append(float(val))

        # Worst thermal load (highest T3_K or T4_K)
        t3 = frame.get("T3_K", 0.0)
        t4 = frame.get("T4_K", 0.0)
        current_thermal = max(float(t3), float(t4))
        if self.worst_thermal_load is None or current_thermal > self.worst_thermal_load.get("_thermal_val", 0.0):
            snap = dict(frame)
            snap["_thermal_val"] = current_thermal
            snap["_position"] = position
            self.worst_thermal_load = snap

        # Worst pressure ratio
        p3 = frame.get("P3_Pa", 0.0)
        p2 = frame.get("P2_Pa", 1.0)
        pr = float(p3) / max(float(p2), 1e-9)
        if self.worst_pressure_ratio is None or pr > self.worst_pressure_ratio.get("_pr_val", 0.0):
            snap = dict(frame)
            snap["_pr_val"] = pr
            snap["_position"] = position
            self.worst_pressure_ratio = snap

        # Largest health degradation jump
        overall_h = frame.get("OverallHealth", None)
        if overall_h is not None and self._prev_overall_health is not None:
            drop = self._prev_overall_health - float(overall_h)
            current_jump = self.largest_degradation_jump.get("_drop_val", 0.0) if self.largest_degradation_jump else 0.0
            if drop > current_jump:
                snap = dict(frame)
                snap["_drop_val"] = drop
                snap["_position"] = position
                self.largest_degradation_jump = snap
        if overall_h is not None:
            self._prev_overall_health = float(overall_h)

        # Stable region tracking
        if overall_h is not None and self._prev_overall_health is not None:
            delta = abs(float(overall_h) - self._prev_overall_health)
            if delta < STABLE_HEALTH_THRESHOLD:
                self.current_stable_streak += 1
                if self.current_stable_streak > self.longest_stable_region["length"]:
                    self.longest_stable_region = {
                        "length": self.current_stable_streak,
                        "end_pos": position
                    }
            else:
                self.current_stable_streak = 0

    def build_normal_profile(self) -> Dict:
        """Compute mean ± std for each sensor from accumulated values."""
        profile = {}
        for key, vals in self._sensor_accum.items():
            arr = np.array(vals)
            profile[key] = {
                "mean": float(arr.mean()),
                "std":  float(arr.std()) if len(arr) > 1 else 0.0,
                "min":  float(arr.min()),
                "max":  float(arr.max()),
            }
        self.normal_operating_profile = profile
        return profile

    def to_dict(self) -> Dict:
        """Serialize experience profile to dictionary."""
        return {
            "total_cycles":            self.total_cycles,
            "normal_operating_profile": self.build_normal_profile(),
            "worst_thermal_load":       self.worst_thermal_load,
            "worst_pressure_ratio":     self.worst_pressure_ratio,
            "largest_degradation_jump": self.largest_degradation_jump,
            "longest_stable_region":    self.longest_stable_region,
        }


class EngineHistoryStore:
    """
    Dual-layer per-engine history store.

    RAM layer  : deque of last RAM_BUFFER_CYCLES frames (fast temporal feature computation)
    SQLite layer: complete cycle history (persistence, playback, fleet analytics)
    Experience  : rich operational memory per engine beyond raw cycles
    """

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path or _DEFAULT_DB_PATH
        self._ram: Dict[str, deque] = {}          # engine_id → deque of frame dicts
        self._experience: Dict[str, EngineExperienceProfile] = {}
        self._position: Dict[str, int] = {}       # positional counter (not cycle number)
        self._lock = threading.Lock()
        self._db_initialized = False
        self._init_db()

    def _init_db(self):
        """Initialize SQLite table for full history persistence."""
        try:
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {DB_TABLE} (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    engine_id   TEXT NOT NULL,
                    cycle       INTEGER NOT NULL,
                    position    INTEGER NOT NULL,
                    frame_json  TEXT NOT NULL,
                    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(engine_id, cycle)
                )
            """)
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_engine_cycle ON {DB_TABLE}(engine_id, cycle)")
            conn.commit()
            conn.close()
            self._db_initialized = True
        except Exception as e:
            print(f"[EngineHistoryStore] SQLite init warning: {e}. Falling back to RAM-only mode.")

    def add_cycle(self, engine_id: str, frame: dict):
        """
        Add a new telemetry frame for an engine.
        Updates both RAM buffer and SQLite store.
        """
        eng = str(engine_id)
        with self._lock:
            # RAM buffer
            if eng not in self._ram:
                self._ram[eng] = deque(maxlen=RAM_BUFFER_CYCLES)
                self._experience[eng] = EngineExperienceProfile()
                self._position[eng] = 0

            self._ram[eng].append(frame)
            pos = self._position[eng]
            self._position[eng] = pos + 1
            self._experience[eng].update(frame, pos)

            # SQLite persistence
            if self._db_initialized:
                try:
                    conn = sqlite3.connect(self._db_path, check_same_thread=False)
                    cycle = int(frame.get("Cycle", pos))
                    conn.execute(
                        f"INSERT OR REPLACE INTO {DB_TABLE} (engine_id, cycle, position, frame_json) VALUES (?, ?, ?, ?)",
                        (eng, cycle, pos, json.dumps({k: v for k, v in frame.items() if isinstance(v, (int, float, str))}))
                    )
                    conn.commit()
                    conn.close()
                except Exception:
                    pass  # SQLite errors don't break inference

    def get_history(self, engine_id: str, window: int = 20) -> pd.DataFrame:
        """
        Returns the last `window` cycles for an engine as a DataFrame.
        Used for temporal feature computation.
        """
        eng = str(engine_id)
        with self._lock:
            buf = self._ram.get(eng, deque())
            frames = list(buf)[-window:]

        if not frames:
            return pd.DataFrame()

        return pd.DataFrame(frames)

    def get_full_history_from_db(self, engine_id: str) -> pd.DataFrame:
        """
        Retrieves complete engine history from SQLite (for analytics / report generation).
        """
        eng = str(engine_id)
        if not self._db_initialized:
            return self.get_history(eng, window=RAM_BUFFER_CYCLES)

        try:
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            rows = conn.execute(
                f"SELECT frame_json FROM {DB_TABLE} WHERE engine_id=? ORDER BY cycle ASC", (eng,)
            ).fetchall()
            conn.close()
            if not rows:
                return pd.DataFrame()
            frames = [json.loads(r[0]) for r in rows]
            return pd.DataFrame(frames)
        except Exception:
            return self.get_history(eng, window=RAM_BUFFER_CYCLES)

    def get_experience(self, engine_id: str) -> Dict:
        """Returns the rich experience profile for an engine."""
        eng = str(engine_id)
        with self._lock:
            if eng in self._experience:
                return self._experience[eng].to_dict()
        return {}

    def compute_temporal_context(self, engine_id: str) -> Dict:
        """
        Computes a compact temporal context dict from RAM buffer for inference.
        Used to enrich single-frame predictions with historical awareness.
        No Cycle column used in computations.
        """
        history_df = self.get_history(engine_id, window=RAM_BUFFER_CYCLES)
        if history_df.empty or len(history_df) < 2:
            return {"history_length": 0, "temporal_context_available": False}

        ctx = {"history_length": len(history_df), "temporal_context_available": True}

        # Health trend (slope over last min(20, N) cycles)
        for hcol in ["OverallHealth", "CompressorHealth", "CombustorHealth", "TurbineHealth"]:
            if hcol not in history_df.columns:
                continue
            vals = history_df[hcol].dropna().values
            if len(vals) >= 2:
                slope = float(np.polyfit(np.arange(len(vals)), vals, 1)[0])
                ctx[f"{hcol}_slope_per_cycle"] = slope
                ctx[f"{hcol}_current"]          = float(vals[-1])
                ctx[f"{hcol}_20cycle_change"]   = float(vals[-1] - vals[0])

        # Sensor drift signals (last 10 cycles vs baseline)
        for scol in ["T4_K", "T3_K", "PR_compressor"]:
            col = scol.replace("PR_compressor", "")
            if scol in history_df.columns:
                recent = history_df[scol].dropna().values
                if len(recent) >= 5:
                    ema = pd.Series(recent).ewm(span=7, min_periods=1).mean().values
                    ctx[f"{scol}_ema_drift"] = float(recent[-1] - ema[-1])

        # Cumulative degradation (from RAM window)
        if "OverallHealth" in history_df.columns:
            health = history_df["OverallHealth"].dropna().values
            losses = np.diff(health).clip(max=0)
            ctx["cumsum_health_loss_window"] = float(abs(losses).sum())
            ctx["degradation_acceleration"]  = float(np.diff(losses)[-1]) if len(losses) > 1 else 0.0

        # Instability (CV of T3 over window)
        if "T3_K" in history_df.columns:
            t3 = history_df["T3_K"].dropna().values
            if len(t3) > 3:
                ctx["T3_CV"] = float(np.std(t3) / (np.mean(t3) + 1e-9))

        return ctx

    def get_all_engine_ids(self) -> List[str]:
        """Returns all engine IDs with stored history."""
        if self._db_initialized:
            try:
                conn = sqlite3.connect(self._db_path, check_same_thread=False)
                rows = conn.execute(f"SELECT DISTINCT engine_id FROM {DB_TABLE}").fetchall()
                conn.close()
                return [r[0] for r in rows]
            except Exception:
                pass
        return list(self._ram.keys())

    def clear(self, engine_id: str):
        """Clears RAM buffer for an engine (SQLite history is preserved)."""
        eng = str(engine_id)
        with self._lock:
            self._ram.pop(eng, None)
            self._experience.pop(eng, None)
            self._position.pop(eng, None)

    def clear_all(self):
        """Clears all RAM buffers (SQLite history is preserved)."""
        with self._lock:
            self._ram.clear()
            self._experience.clear()
            self._position.clear()


# Global singleton for use by routes.py
_global_store: Optional[EngineHistoryStore] = None


def get_global_store(db_path: Optional[str] = None) -> EngineHistoryStore:
    """Returns (or creates) the global singleton EngineHistoryStore."""
    global _global_store
    if _global_store is None:
        _global_store = EngineHistoryStore(db_path=db_path)
    return _global_store
