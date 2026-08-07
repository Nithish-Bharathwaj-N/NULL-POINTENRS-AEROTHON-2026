"""Overall whole-engine Brayton-cycle performance features."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .efficiency_features import mass_flow_rate_kg_s
from .feature_engineering import build_physics_features


def build_overall_engine_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build measured-station engine performance features."""

    enriched = build_physics_features(df)
    cp_air = enriched["atm_cp_air_j_kgk"].astype(float)
    index = enriched.index
    tamb = enriched.get("Tamb_K", enriched["atm_temperature_k"]).astype(float)
    t2 = enriched.get("T2_K", pd.Series(np.nan, index=index)).astype(float)
    t3 = enriched.get("T3_K", pd.Series(np.nan, index=index)).astype(float)
    t4 = enriched.get("T4_K", pd.Series(np.nan, index=index)).astype(float)
    p2 = enriched.get("P2_Pa", pd.Series(np.nan, index=index)).astype(float)
    p3 = enriched.get("P3_Pa", pd.Series(np.nan, index=index)).astype(float)
    p4 = enriched.get("P4_Pa", pd.Series(np.nan, index=index)).astype(float)
    pamb = enriched.get("Pamb_Pa", enriched["atm_pressure_pa"]).astype(float)

    mass_flow = mass_flow_rate_kg_s(enriched)
    thrust = enriched.get("Thrust_N", pd.Series(np.nan, index=index)).astype(float)
    fuel_flow = enriched.get("FuelFlow_kg_s", pd.Series(np.nan, index=index)).astype(float)
    pressure_ratio = p2 / pamb.replace(0.0, np.nan)
    temperature_ratio = t2 / tamb.replace(0.0, np.nan)
    expansion_ratio = p3 / p4.replace(0.0, np.nan)
    gamma = enriched["atm_gamma"].astype(float)

    out = pd.DataFrame(index=index)
    if "EngineID" in enriched.columns:
        out["EngineID"] = enriched["EngineID"]
    out["overall_pressure_ratio"] = pressure_ratio
    out["compressor_temperature_ratio"] = temperature_ratio
    out["turbine_expansion_ratio"] = expansion_ratio
    out["brayton_thermal_efficiency"] = 1.0 - (
        1.0 / pressure_ratio
    ) ** ((gamma - 1.0) / gamma)
    compressor_work = cp_air * (t2 - tamb)
    turbine_work = cp_air * (t3 - t4)
    out["compressor_work_j_kg"] = compressor_work
    out["turbine_work_j_kg"] = turbine_work
    out["net_work_j_kg"] = turbine_work - compressor_work
    out["heat_added_j_kg"] = cp_air * (t3 - t2)
    out["heat_rejected_j_kg"] = cp_air * (t4 - tamb)
    out["tsfc_kg_per_n_s"] = np.where(
        thrust.abs() > 1e-9,
        fuel_flow / thrust,
        np.nan,
    )
    out["thrust_n"] = thrust
    out["specific_thrust_n_s_per_kg"] = np.where(
        mass_flow > 1e-9,
        thrust / mass_flow,
        np.nan,
    )
    out["fuel_air_ratio"] = enriched["fuel_air_ratio"].astype(float)
    out["mass_flow_rate_kg_s"] = mass_flow
    return out