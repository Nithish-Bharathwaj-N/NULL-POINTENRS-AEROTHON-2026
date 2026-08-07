import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_selection import SelectKBest, mutual_info_regression
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


RAW_FEATURE_COLUMNS = [
    "Altitude_m", "Mach", "Tamb_K", "Pamb_Pa",
    "RPM_rev_min", "FuelFlow_kg_s",
    "P2_Pa", "T2_K", "P3_Pa", "T3_K", "P4_Pa", "T4_K",
]

SENSOR_COLUMNS = [
    "RPM_rev_min", "FuelFlow_kg_s", "P2_Pa", "T2_K",
    "P3_Pa", "T3_K", "P4_Pa", "T4_K",
]


def nasa_phm_score(y_true, y_pred):
    err = np.asarray(y_pred) - np.asarray(y_true)
    return float(np.sum(np.where(err < 0, np.exp(-err / 13.0) - 1.0, np.exp(err / 10.0) - 1.0)))


class AdvancedFeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self, include_temporal=True, include_interactions=True):
        self.include_temporal = include_temporal
        self.include_interactions = include_interactions
        self.feature_names_ = None

    def fit(self, X, y=None):
        Xt = self._transform_frame(X)
        self.feature_names_ = Xt.columns.tolist()
        return self

    def transform(self, X):
        Xt = self._transform_frame(X)
        for col in self.feature_names_:
            if col not in Xt:
                Xt[col] = 0.0
        return Xt[self.feature_names_].replace([np.inf, -np.inf], np.nan)

    def _transform_frame(self, X):
        df = pd.DataFrame(X).copy()
        for col in RAW_FEATURE_COLUMNS:
            if col not in df:
                df[col] = np.nan
        if "EngineID" not in df:
            df["EngineID"] = 0
        if "Cycle" not in df:
            df["Cycle"] = np.arange(len(df), dtype=float)

        df = df.sort_values(["EngineID", "Cycle"], kind="mergesort").reset_index(drop=True)
        out = df[RAW_FEATURE_COLUMNS + ["Cycle"]].astype(float).copy()
        eps = 1e-9
        gamma_factor = (1.4 - 1.0) / 1.4
        ram_temp_ratio = 1.0 + 0.2 * out["Mach"] ** 2
        pt0 = out["Pamb_Pa"] * ram_temp_ratio ** 3.5
        tt0 = out["Tamb_K"] * ram_temp_ratio

        out["PR_2_0"] = out["P2_Pa"] / (pt0 + eps)
        out["PR_3_2"] = out["P3_Pa"] / (out["P2_Pa"] + eps)
        out["PR_4_3"] = out["P4_Pa"] / (out["P3_Pa"] + eps)
        out["PR_4_0"] = out["P4_Pa"] / (out["Pamb_Pa"] + eps)
        out["TR_2_0"] = out["T2_K"] / (tt0 + eps)
        out["TR_3_2"] = out["T3_K"] / (out["T2_K"] + eps)
        out["TR_4_3"] = out["T4_K"] / (out["T3_K"] + eps)
        out["FuelFlow_per_RPM"] = out["FuelFlow_kg_s"] / (out["RPM_rev_min"] + eps)
        out["RPM_corrected"] = out["RPM_rev_min"] / np.sqrt(out["Tamb_K"].clip(lower=eps))
        out["dT_compressor"] = out["T3_K"] - out["T2_K"]
        out["dT_combustor"] = out["T3_K"] - out["T2_K"]
        out["dT_turbine"] = out["T3_K"] - out["T4_K"]
        out["eta_c_proxy"] = (out["T2_K"] * (out["PR_3_2"].clip(lower=eps) ** gamma_factor) - out["T2_K"]) / (out["dT_compressor"] + eps)
        out["thermal_load"] = out["FuelFlow_kg_s"] * out["T3_K"]

        if self.include_interactions:
            out["rpm_fuel"] = out["RPM_rev_min"] * out["FuelFlow_kg_s"]
            out["mach_altitude"] = out["Mach"] * out["Altitude_m"]
            out["pr_temp_interaction"] = out["PR_3_2"] * out["TR_3_2"]
            out["turbine_work_proxy"] = out["PR_4_3"] * out["dT_turbine"]

        if self.include_temporal:
            grouped = df.groupby("EngineID", sort=False)
            for col in SENSOR_COLUMNS:
                out[f"{col}_lag1"] = grouped[col].shift(1).astype(float)
                out[f"{col}_delta1"] = grouped[col].diff().astype(float)
                out[f"{col}_grad"] = grouped[col].diff().astype(float)
                out[f"{col}_second_derivative"] = grouped[col].diff().diff().astype(float)
                out[f"{col}_roll3_mean"] = grouped[col].transform(lambda s: s.rolling(3, min_periods=1).mean())
                out[f"{col}_roll3_std"] = grouped[col].transform(lambda s: s.rolling(3, min_periods=2).std())
                out[f"{col}_roll3_rms"] = grouped[col].transform(lambda s: np.sqrt(s.pow(2).rolling(3, min_periods=1).mean()))
                out[f"{col}_ema3"] = grouped[col].transform(lambda s: s.ewm(span=3, adjust=False).mean())
                out[f"{col}_ewm5"] = grouped[col].transform(lambda s: s.ewm(span=5, adjust=False).mean())

        return out


def make_preprocessor(k="all", scale=False):
    steps = [("features", AdvancedFeatureEngineer()), ("imputer", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scaler", StandardScaler()))
    if k != "all":
        steps.append(("selector", SelectKBest(mutual_info_regression, k=k)))
    return Pipeline(steps)


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
