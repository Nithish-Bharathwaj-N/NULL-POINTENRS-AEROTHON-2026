import os
import pandas as pd
import numpy as np

class TelemetryStreamer:
    """
    Telemetry buffer and playback manager reading from authoritative datasets.
    Supports strict dataset cycle streaming and real-world engine degradation playback.
    """

    def __init__(self, dataset_path="backend/data/turbojet_complete_dataset.csv"):
        self.dataset_path = dataset_path
        self.df = None
        self.current_index = 0
        self.selected_engine_id = "HAL-TJ4-001"
        self.playback_cycle = 1
        self.load_dataset()

    def load_dataset(self):
        self._lookup = {}
        if os.path.exists(self.dataset_path):
            self.df = pd.read_csv(self.dataset_path)
            print(f"[TelemetryStreamer] Loaded {len(self.df)} telemetry frames from {self.dataset_path}")
            # Pre-index for O(1) lookup
            for row in self.df.to_dict("records"):
                eng = str(row.get("EngineID", "1"))
                cyc = int(row.get("Cycle", 1))
                self._lookup[(eng, cyc)] = self._clean_row(row)
        else:
            print(f"[TelemetryStreamer] WARNING: Dataset {self.dataset_path} not found.")

    def get_engines(self) -> list:
        if self.df is not None:
            return list(self.df["EngineID"].unique())
        return ["HAL-TJ4-001", "HAL-TJ4-002", "HAL-TJ4-003", "HAL-TJ4-004", "HAL-TJ4-005"]

    def get_engine_max_cycles(self, engine_id: str) -> int:
        if self.df is not None:
            sub = self.df[self.df["EngineID"] == engine_id]
            if len(sub) > 0:
                return int(sub["Cycle"].max())
        return 250

    def get_next_live_frame(self) -> dict:
        if self.df is None or len(self.df) == 0:
            return self._fallback_frame()
        
        row = self.df.iloc[self.current_index].to_dict()
        self.current_index = (self.current_index + 1) % len(self.df)
        return self._clean_row(row)

    def get_playback_frame(self, engine_id: str, cycle: int) -> dict:
        key = (str(engine_id), int(cycle))
        if hasattr(self, "_lookup") and key in self._lookup:
            return self._lookup[key]
        if hasattr(self, "_lookup") and ("1", int(cycle)) in self._lookup:
            return self._lookup[("1", int(cycle))]
        return self._fallback_frame()

    def _clean_row(self, row: dict) -> dict:
        clean = {}
        for k, v in row.items():
            if k == "EngineID":
                clean[k] = str(v)
            elif k == "Cycle":
                clean[k] = int(v)
            else:
                try:
                    clean[k] = float(v)
                except (ValueError, TypeError):
                    clean[k] = v
        return clean

    def _fallback_frame(self) -> dict:
        return {
            "EngineID": "HAL-TJ4-001",
            "Cycle": 1,
            "Altitude": 30000.0,
            "Mach": 0.78,
            "Ambient Temperature": -45.0,
            "Ambient Pressure": 3.9,
            "RPM": 12500.0,
            "Fuel Flow": 3.45,
            "Compressor Exit Pressure (P2)": 49.0,
            "Compressor Exit Temperature (T2)": 233.0,
            "Combustor Exit Pressure (P3)": 46.0,
            "Turbine Inlet Temperature (T3)": 1770.0,
            "Turbine Exit Pressure (P4)": 14.5,
            "Turbine Exit Temperature (T4)": 1030.0,
            "Compressor Health": 99.5,
            "Combustor Health": 99.5,
            "Turbine Health": 99.5,
            "Overall Health": 99.5,
            "Thrust": 54.0,
            "TSFC": 63.0
        }
