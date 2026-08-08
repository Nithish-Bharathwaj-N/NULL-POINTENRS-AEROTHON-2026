"""
HAL / IIT Indore Aerothon 2026 - Aerospace-Grade Dataset Processing Pipeline
=============================================================================
Provides physics-aware preprocessing, sensor validation, flight-condition normalization,
outlier clipping, temporal degradation analysis, drift detection, and leakage prevention
for single-spool four-stage turbojet digital twin telemetry datasets.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any

# Standard Sea Level Atmosphere (ISA) Constants
T_STD_K = 288.15
P_STD_PA = 101325.0
GAMMA = 1.4

# Sensor Validity Operational Ranges for 4-Stage Turbojet
SENSOR_RANGES = {
    "Altitude_m": (0.0, 15000.0),
    "Mach": (0.0, 2.5),
    "Tamb_K": (180.0, 350.0),
    "Pamb_Pa": (10000.0, 110000.0),
    "RPM_rev_min": (5000.0, 50000.0),
    "FuelFlow_kg_s": (0.05, 5.0),
    "P2_Pa": (10000.0, 500000.0),
    "T2_K": (180.0, 600.0),
    "P3_Pa": (100000.0, 3500000.0),
    "T3_K": (800.0, 3800.0),
    "P4_Pa": (20000.0, 500000.0),
    "T4_K": (400.0, 3500.0),
}

# Leakage columns to drop unconditionally
LEAKAGE_COLUMNS = [
    "residual_Thrust_N",
    "residual_TSFC_g_N_s",
    "thrust_n",
    "tsfc_kg_per_n_s",
    "specific_thrust_n_s_per_kg",
    "mass_flow_rate_kg_s",
    "fuel_air_ratio"
]

class AerospaceDatasetPipeline:
    """
    Robust, physics-consistent dataset processor enforcing sensor validation,
    aero-thermal normalization, temporal degradation modeling, and leakage guards.
    """

    @staticmethod
    def validate_and_clean_sensors(df: pd.DataFrame) -> pd.DataFrame:
        """Enforce physical validity bounds, out-of-range clipping, and missing value imputation."""
        out = df.copy()

        # 1. Physical Sensor Boundary Validation & Outlier Clipping
        for sensor, (min_val, max_val) in SENSOR_RANGES.items():
            if sensor in out.columns:
                # Flag out-of-range sensor readings as NaN for intelligent imputation
                out[sensor] = out[sensor].apply(lambda x: x if min_val <= x <= max_val else np.nan)

        # 2. Physics-Consistent Imputation Strategy
        # Group-wise forward-fill by EngineID, followed by median fallback
        if "EngineID" in out.columns:
            fill_cols = [c for c in out.columns if c != "EngineID"]
            out[fill_cols] = out.groupby("EngineID")[fill_cols].transform(lambda g: g.ffill().bfill())

        # Fallback to column median for any remaining NaNs
        numeric_cols = out.select_dtypes(include=[np.number]).columns
        out[numeric_cols] = out[numeric_cols].fillna(out[numeric_cols].median())

        return out

    @staticmethod
    def normalize_flight_conditions(df: pd.DataFrame) -> pd.DataFrame:
        """
        Aero-thermal Normalization:
        Divides pressures, temperatures, and shaft speeds by atmospheric ratios
        (theta = Tamb / 288.15, delta = Pamb / 101325) to isolate component wear
        from altitude & Mach variations.
        """
        out = df.copy()
        eps = 1e-6

        theta = np.maximum(eps, out["Tamb_K"] / T_STD_K)
        delta = np.maximum(eps, out["Pamb_Pa"] / P_STD_PA)

        # Corrected Shaft Speed & Mass Flow Proxies
        out["RPM_corrected"] = out["RPM_rev_min"] / np.sqrt(theta)
        out["FuelFlow_corrected"] = out["FuelFlow_kg_s"] / (delta * np.sqrt(theta))

        # Station Non-Dimensional Ratios
        out["P2_over_Pamb"] = out["P2_Pa"] / np.maximum(eps, out["Pamb_Pa"])
        out["P3_over_P2"] = out["P3_Pa"] / np.maximum(eps, out["P2_Pa"])
        out["P3_over_P4"] = out["P3_Pa"] / np.maximum(eps, out["P4_Pa"])

        out["T2_over_Tamb"] = out["T2_K"] / np.maximum(eps, out["Tamb_K"])
        out["T3_over_T2"] = out["T3_K"] / np.maximum(eps, out["T2_K"])
        out["T4_over_T3"] = out["T4_K"] / np.maximum(eps, out["T3_K"])

        # Isentropic Compressor Efficiency Proxy
        isentropic_term = np.maximum(0.0, (out["P2_Pa"] / np.maximum(eps, out["Pamb_Pa"])) ** ((GAMMA - 1) / GAMMA) - 1.0)
        out["Compressor_Efficiency_Proxy"] = (out["T2_K"] - out["Tamb_K"]) / (isentropic_term * out["Tamb_K"] + eps)

        # Turbine Work Extraction Coefficient
        out["Work_Coefficient"] = (out["T3_K"] - out["T4_K"]) / np.maximum(eps, out["T3_K"])

        return out

    @staticmethod
    def extract_temporal_degradation(df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute engine cycle degradation velocity and drift detection signals.
        """
        out = df.copy()

        if "EngineID" in out.columns and "Cycle" in out.columns:
            out = out.sort_values(["EngineID", "Cycle"])

            # Normalized operating life fraction
            max_cycles = out.groupby("EngineID")["Cycle"].transform("max")
            out["Life_Fraction"] = out["Cycle"] / np.maximum(1.0, max_cycles)

            # 5-Cycle Exponential Moving Average Drift
            for sensor in ["P3_Pa", "T4_K", "RPM_rev_min"]:
                if sensor in out.columns:
                    ema = out.groupby("EngineID")[sensor].transform(lambda s: s.ewm(span=5, min_periods=1).mean())
                    out[f"{sensor}_drift_5cycle"] = out[sensor] - ema

        return out

    @classmethod
    def process_dataset(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Full aerospace dataset execution pipeline:
        1. Leakage Guard removal
        2. Sensor Validation & Imputation
        3. Aero-thermal Flight-Condition Normalization
        4. Temporal Degradation & Drift Feature Extraction
        """
        # Drop known leakage columns
        clean_df = df.drop(columns=[c for c in LEAKAGE_COLUMNS if c in df.columns], errors="ignore")
        
        # Step-by-step pipeline
        validated = cls.validate_and_clean_sensors(clean_df)
        normalized = cls.normalize_flight_conditions(validated)
        processed = cls.extract_temporal_degradation(normalized)

        return processed

if __name__ == "__main__":
    import os
    dataset_path = r"c:\Users\praja\Downloads\AEROTHON2026-main (2)\Dataset-20260724T080808Z-1-001\Dataset\turbojet_complete_dataset.csv"
    if os.path.exists(dataset_path):
        raw_df = pd.read_csv(dataset_path)
        processed_df = AerospaceDatasetPipeline.process_dataset(raw_df)
        print(f"[AerospaceDatasetPipeline SUCCESS] Input shape: {raw_df.shape} -> Processed shape: {processed_df.shape}")
        print("Engineered Columns:", [c for c in processed_df.columns if c not in raw_df.columns])
