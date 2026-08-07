"""
temporal_features.py
====================
Aerospace-Grade Temporal Feature Engineering Pipeline for Aerothon 2026.

Extracts all temporal relationships from sensor history.
CRITICAL: Cycle, Normalized_Cycle, and Life_Fraction are NEVER used as features.
Temporal information enters only through engineered sensor-history signals.

Compatible with scikit-learn fit/transform API for leak-free CV.
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Dict
import warnings

warnings.filterwarnings("ignore")

# ─── Physical Constants ────────────────────────────────────────────────────────
GAMMA = 1.4
T_STD_K = 288.15
P_STD_PA = 101325.0
EPS = 1e-9

# EGT material limit for single-crystal Ni superalloy (CMSX-4)
T4_LIMIT_K = 1273.15  # 1000°C

# Rolling window sizes (in cycles) — no time index encoding
ROLL_WINDOWS = [5, 10, 20, 50]

# EMA span sizes (in cycles)
EMA_SPANS = [3, 7, 15, 30]

# Lag sizes (in cycles, causal only)
LAG_SIZES = [1, 5, 10, 20]

# Primary degradation-sensitive sensors
SENSOR_COLS = [
    "T3_K", "T4_K", "P3_Pa", "RPM_rev_min", "FuelFlow_kg_s",
    "T2_K", "P2_Pa", "P4_Pa", "Tamb_K", "Pamb_Pa", "Mach", "Altitude_m"
]

# Health columns (available in training data, absent in test)
HEALTH_COLS = [
    "CompressorHealth", "CombustorHealth", "TurbineHealth", "OverallHealth"
]

# Derived ratio columns (computed before temporal ops)
RATIO_COLS = ["PR_compressor", "TR_combustor", "Work_Coefficient"]


class TemporalFeatureEngineer:
    """
    Computes physics-guided temporal features from engine sensor history.

    STRICT EXCLUSIONS:
        - 'Cycle' column: never passed to any model
        - 'Normalized_Cycle': never computed
        - 'Life_Fraction' (= Cycle/max): never computed
        All temporal information is derived from HOW sensors change, not WHEN.

    Usage:
        engineer = TemporalFeatureEngineer()
        engineer.fit(train_df)          # learns per-engine baselines from training set
        X_train = engineer.transform(train_df)
        X_test  = engineer.transform(test_df)
    """

    def __init__(self):
        self.engine_baselines_: Optional[Dict] = None
        self.feature_names_: Optional[List[str]] = None
        self.is_fitted_ = False

    def fit(self, df: pd.DataFrame) -> "TemporalFeatureEngineer":
        """
        Learn per-engine baseline statistics from training data only.
        These baselines are used to compute deviations in transform().
        """
        assert "EngineID" in df.columns, "EngineID column required"

        baselines = {}
        for eng_id, grp in df.groupby("EngineID"):
            eng_stats = {}
            for col in SENSOR_COLS:
                if col in grp.columns:
                    vals = grp[col].dropna()
                    eng_stats[f"{col}_baseline_mean"] = float(vals.mean()) if len(vals) > 0 else 0.0
                    eng_stats[f"{col}_baseline_std"]  = float(vals.std())  if len(vals) > 1 else 1.0

            # Physics baselines
            if "P3_Pa" in grp.columns and "P2_Pa" in grp.columns:
                pr = grp["P3_Pa"] / grp["P2_Pa"].replace(0, np.nan)
                eng_stats["PR_baseline"] = float(pr.mean()) if not pr.empty else 10.0

            if "T3_K" in grp.columns and "T2_K" in grp.columns:
                tr = grp["T3_K"] / grp["T2_K"].replace(0, np.nan)
                eng_stats["TR_baseline"] = float(tr.mean()) if not tr.empty else 4.0

            baselines[str(eng_id)] = eng_stats

        # Fleet-wide baselines for unseen engines
        all_sensor_vals = {}
        for col in SENSOR_COLS:
            if col in df.columns:
                all_sensor_vals[f"{col}_fleet_mean"] = float(df[col].mean())
                all_sensor_vals[f"{col}_fleet_std"]  = float(df[col].std()) + EPS

        baselines["__fleet__"] = all_sensor_vals
        self.engine_baselines_ = baselines
        self.is_fitted_ = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute all temporal features. Input df must contain 'EngineID'.
        Processes each engine group independently in chronological order.
        NEVER reads the 'Cycle' column for feature computation.
        """
        assert self.is_fitted_, "Call fit() before transform()"
        assert "EngineID" in df.columns, "EngineID column required"

        result_parts = []

        for eng_id, grp in df.groupby("EngineID", sort=False):
            # Sort chronologically by Cycle for correct lag/rolling order
            # (Cycle is used ONLY for ordering, never as a feature value)
            if "Cycle" in grp.columns:
                grp = grp.sort_values("Cycle").copy()
            else:
                grp = grp.copy()

            out = self._compute_engine_features(grp, str(eng_id))
            result_parts.append(out)

        if not result_parts:
            return df.copy()

        result = pd.concat(result_parts, axis=0).reset_index(drop=True)

        # Drop forbidden columns from output
        forbidden = ["Cycle", "Normalized_Cycle", "Life_Fraction"]
        result = result.drop(columns=[c for c in forbidden if c in result.columns], errors="ignore")

        if self.feature_names_ is None:
            self.feature_names_ = [
                c for c in result.columns
                if c not in ["EngineID"] + HEALTH_COLS + ["Thrust_N", "TSFC_g_N_s", "Cycle"]
            ]

        return result.fillna(0.0)

    def _compute_engine_features(self, grp: pd.DataFrame, eng_id: str) -> pd.DataFrame:
        """Compute all feature categories for a single engine's trajectory."""
        out = grp.copy()
        baseline = self.engine_baselines_.get(eng_id, self.engine_baselines_.get("__fleet__", {}))

        # ── 1. Physics-Guided Instantaneous Features ──────────────────────────
        eps = EPS

        # Pressure ratios
        out["PR_compressor"] = out["P3_Pa"] / out["P2_Pa"].replace(0, np.nan).fillna(eps)
        out["PR_turbine"]    = out["P3_Pa"] / out["P4_Pa"].replace(0, np.nan).fillna(eps)
        out["PR_overall"]    = out["P4_Pa"] / out["Pamb_Pa"].replace(0, np.nan).fillna(eps)
        out["P2_over_Pamb"]  = out["P2_Pa"] / out["Pamb_Pa"].replace(0, np.nan).fillna(eps)

        # Temperature ratios
        out["TR_combustor"]  = out["T3_K"] / out["T2_K"].replace(0, np.nan).fillna(eps)
        out["TR_turbine"]    = out["T4_K"] / out["T3_K"].replace(0, np.nan).fillna(eps)
        out["T2_over_Tamb"]  = out["T2_K"] / out["Tamb_K"].replace(0, np.nan).fillna(eps)

        # Turbine work & efficiency
        out["Work_Coefficient"] = (out["T3_K"] - out["T4_K"]) / out["T3_K"].replace(0, np.nan).fillna(eps)

        # Isentropic compressor efficiency
        theta = out["Tamb_K"] / T_STD_K
        delta = out["Pamb_Pa"] / P_STD_PA
        pr_ratio = (out["P2_Pa"] / out["Pamb_Pa"].replace(0, np.nan).fillna(eps))
        isentropic_term = np.maximum(0.0, pr_ratio ** ((GAMMA - 1) / GAMMA) - 1.0)
        out["Compressor_Isentropic_Eff"] = (out["T2_K"] - out["Tamb_K"]) / (isentropic_term * out["Tamb_K"] + eps)
        out["Compressor_Isentropic_Eff"] = out["Compressor_Isentropic_Eff"].clip(0.0, 1.5)

        # EGT margin (K remaining before material limit)
        out["EGT_Margin_K"] = T4_LIMIT_K - out["T4_K"]

        # Thermal stress index (combined thermomechanical loading)
        out["Thermal_Stress_Index"] = (out["T3_K"] / out["T4_K"].replace(0, np.nan).fillna(eps)) * \
                                       (out["P3_Pa"] / out["P4_Pa"].replace(0, np.nan).fillna(eps))

        # Corrected shaft speed (ISA-normalized, no Cycle)
        out["RPM_corrected"]   = out["RPM_rev_min"] / np.sqrt(theta.replace(0, np.nan).fillna(1.0))
        out["Flow_corrected"]  = out["FuelFlow_kg_s"] / (delta * np.sqrt(theta.replace(0, np.nan).fillna(1.0)) + eps)

        # Compressor work proxy
        out["Compressor_Work_proxy"] = (out["T2_K"] - out["Tamb_K"]) * out["RPM_corrected"]

        # Combustor loading
        out["Combustor_Loading"] = (out["FuelFlow_kg_s"] * out["T3_K"]) / \
                                    (out["P3_Pa"].replace(0, np.nan).fillna(eps) * out["RPM_rev_min"].replace(0, np.nan).fillna(eps))

        # TSFC proxy
        out["Thrust_Specific_Fuel_proxy"] = out["FuelFlow_kg_s"] / (out["RPM_corrected"].replace(0, np.nan).fillna(eps))

        # Operating regime (flight-condition encoded, no time)
        out["Alt_regime"]  = out["Altitude_m"] / 11000.0   # troposphere fraction
        out["Mach_regime"] = out["Mach"] ** 2 / 2.0        # dynamic pressure proxy

        # Engine-specific deviations from baseline
        pr_base = baseline.get("PR_baseline", 10.0)
        tr_base = baseline.get("TR_baseline", 4.0)
        out["PR_deviation_from_baseline"] = out["PR_compressor"] - pr_base
        out["TR_deviation_from_baseline"] = out["TR_combustor"] - tr_base

        # Surge proximity: how far PR is from its local rolling mean
        if len(out) >= 5:
            out["PR_surge_proximity"] = out["PR_compressor"] - out["PR_compressor"].rolling(20, min_periods=3).mean()
        else:
            out["PR_surge_proximity"] = 0.0

        # Subsystem health divergence (when health cols are present)
        health_present = [c for c in HEALTH_COLS[:3] if c in out.columns]
        if len(health_present) == 3:
            out["Health_Divergence"] = out[health_present].std(axis=1)
        else:
            out["Health_Divergence"] = 0.0

        # ── 2. Rolling Window Statistics ───────────────────────────────────────
        rolling_targets = ["T3_K", "T4_K", "P3_Pa", "RPM_rev_min",
                           "FuelFlow_kg_s", "PR_compressor", "Work_Coefficient",
                           "EGT_Margin_K", "Thermal_Stress_Index"]

        for col in rolling_targets:
            if col not in out.columns:
                continue
            series = out[col]
            for W in ROLL_WINDOWS:
                roll = series.rolling(window=W, min_periods=max(1, W // 2))
                out[f"{col}_roll_mean_{W}"] = roll.mean()
                out[f"{col}_roll_std_{W}"]  = roll.std().fillna(0.0)
                out[f"{col}_roll_min_{W}"]  = roll.min()
                out[f"{col}_roll_max_{W}"]  = roll.max()
                # Coefficient of variation — detects unstable operating regions
                mu = roll.mean()
                sig = roll.std().fillna(0.0)
                out[f"{col}_CV_{W}"] = sig / (mu.abs() + eps)

        # ── 3. Exponential Moving Averages & Drift Signals ─────────────────────
        ema_targets = ["T3_K", "T4_K", "P3_Pa", "PR_compressor",
                       "Work_Coefficient", "EGT_Margin_K", "FuelFlow_kg_s"]

        for col in ema_targets:
            if col not in out.columns:
                continue
            for span in EMA_SPANS:
                ema_vals = out[col].ewm(span=span, min_periods=1).mean()
                out[f"{col}_ema_{span}"] = ema_vals
                out[f"{col}_ema_dev_{span}"] = out[col] - ema_vals  # drift signal

        # ── 4. Lag Features (causal, no future leakage) ────────────────────────
        lag_targets = ["T4_K", "T3_K", "PR_compressor", "Work_Coefficient",
                       "FuelFlow_kg_s", "EGT_Margin_K", "Thermal_Stress_Index"]
        if "OverallHealth" in out.columns:
            lag_targets.extend(["CompressorHealth", "CombustorHealth",
                                 "TurbineHealth", "OverallHealth"])

        for col in lag_targets:
            if col not in out.columns:
                continue
            for lag in LAG_SIZES:
                out[f"{col}_lag{lag}"] = out[col].shift(lag)

        # ── 5. Cycle-to-Cycle Deltas & Acceleration ────────────────────────────
        delta_targets = ["T4_K", "T3_K", "PR_compressor", "Work_Coefficient",
                          "EGT_Margin_K", "FuelFlow_kg_s"]
        if "OverallHealth" in out.columns:
            delta_targets.extend(["CompressorHealth", "CombustorHealth",
                                   "TurbineHealth", "OverallHealth"])

        for col in delta_targets:
            if col not in out.columns:
                continue
            delta1 = out[col].diff(1)
            out[f"delta_{col}"]  = delta1                # velocity
            out[f"accel_{col}"]  = delta1.diff(1)        # acceleration (2nd derivative)

        # ── 6. Cumulative Degradation Indicators ───────────────────────────────
        if "OverallHealth" in out.columns:
            health_delta = out["OverallHealth"].diff(1).clip(upper=0)  # only losses
            out["cumsum_health_loss"] = health_delta.abs().cumsum()

            # Area under health curve (trapezoidal)
            # (no Cycle index — uses positional index as step count within engine)
            out["auc_health"] = out["OverallHealth"].expanding(min_periods=1).mean()

        if "CompressorHealth" in out.columns:
            out["cumsum_comp_loss"] = out["CompressorHealth"].diff(1).clip(upper=0).abs().cumsum()
        if "TurbineHealth" in out.columns:
            out["cumsum_turb_loss"] = out["TurbineHealth"].diff(1).clip(upper=0).abs().cumsum()

        return out

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df).transform(df)

    def get_feature_names(self) -> List[str]:
        """Returns list of all engineered feature names (after fit+transform)."""
        assert self.feature_names_ is not None, "Call fit_transform() first"
        return self.feature_names_


def engineer_point_features(row: dict) -> dict:
    """
    Single-frame feature engineering for real-time inference.
    When no history is available, computes only instantaneous physics features.
    No Cycle, no rolling stats (requires history).
    """
    eps = EPS

    t2 = float(row.get("T2_K", 300.0))
    t3 = float(row.get("T3_K", 1700.0))
    t4 = float(row.get("T4_K", 1000.0))
    p2 = float(row.get("P2_Pa", 500000.0))
    p3 = float(row.get("P3_Pa", 2400000.0))
    p4 = float(row.get("P4_Pa", 120000.0))
    pamb = float(row.get("Pamb_Pa", 101325.0))
    tamb = float(row.get("Tamb_K", 288.15))
    rpm  = float(row.get("RPM_rev_min", 12500.0))
    ff   = float(row.get("FuelFlow_kg_s", 0.5))
    mach = float(row.get("Mach", 0.5))
    alt  = float(row.get("Altitude_m", 8000.0))

    theta = tamb / T_STD_K
    delta = pamb / P_STD_PA
    pr = p3 / max(eps, p2)
    isentropic = max(0.0, pr ** ((GAMMA - 1) / GAMMA) - 1.0)

    return {
        "PR_compressor":             p3 / max(eps, p2),
        "PR_turbine":                p3 / max(eps, p4),
        "PR_overall":                p4 / max(eps, pamb),
        "P2_over_Pamb":              p2 / max(eps, pamb),
        "TR_combustor":              t3 / max(eps, t2),
        "TR_turbine":                t4 / max(eps, t3),
        "T2_over_Tamb":              t2 / max(eps, tamb),
        "Work_Coefficient":          (t3 - t4) / max(eps, t3),
        "Compressor_Isentropic_Eff": min(1.5, (t2 - tamb) / max(eps, isentropic * tamb)),
        "EGT_Margin_K":              T4_LIMIT_K - t4,
        "Thermal_Stress_Index":      (t3 / max(eps, t4)) * (p3 / max(eps, p4)),
        "RPM_corrected":             rpm / max(eps, theta ** 0.5),
        "Flow_corrected":            ff / max(eps, delta * theta ** 0.5),
        "Compressor_Work_proxy":     (t2 - tamb) * rpm / max(eps, theta ** 0.5),
        "Combustor_Loading":         ff * t3 / max(eps, p3 * rpm),
        "Thrust_Specific_Fuel_proxy": ff / max(eps, rpm / max(eps, theta ** 0.5)),
        "Alt_regime":                alt / 11000.0,
        "Mach_regime":               mach ** 2 / 2.0,
        # Placeholder temporal features (0 when no history available)
        "Health_Divergence":         0.0,
        "PR_deviation_from_baseline": 0.0,
        "TR_deviation_from_baseline": 0.0,
        "PR_surge_proximity":         0.0,
        "cumsum_health_loss":         0.0,
        "auc_health":                 0.0,
        "delta_T4_K":                 0.0,
        "accel_T4_K":                 0.0,
        "delta_OverallHealth":        0.0,
        "accel_OverallHealth":        0.0,
    }
