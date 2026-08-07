"""Feature engineering utilities that blend physics and sensor data."""

from __future__ import annotations

import pandas as pd

from .atmosphere import isa_atmosphere
from .compressor import compressor_outlet_state
from .combustor import combustor_temp_rise


def build_physics_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add a compact set of physics-derived features to a dataframe."""

    out = df.copy()

    # Column normalization helper
    if "Tamb_K" not in out.columns and "Ambient_Temperature" in out.columns:
        out["Tamb_K"] = out["Ambient_Temperature"].apply(lambda t: t + 273.15 if t < 150 else t)
    if "Pamb_Pa" not in out.columns and "Ambient_Pressure" in out.columns:
        out["Pamb_Pa"] = out["Ambient_Pressure"].apply(lambda p: p * 101325.0 / 14.7 if p < 1000 else p)
    if "Altitude_m" not in out.columns and "Altitude" in out.columns:
        out["Altitude_m"] = out["Altitude"]
    if "FuelFlow_kg_s" not in out.columns and "Fuel_Flow" in out.columns:
        out["FuelFlow_kg_s"] = out["Fuel_Flow"].apply(lambda f: f / 3600.0 if f > 10.0 else f)
    if "RPM_rev_min" not in out.columns and "RPM" in out.columns:
        out["RPM_rev_min"] = out["RPM"]

    # Fill defaults if missing
    if "Tamb_K" not in out.columns: out["Tamb_K"] = 288.15
    if "Pamb_Pa" not in out.columns: out["Pamb_Pa"] = 101325.0
    if "Altitude_m" not in out.columns: out["Altitude_m"] = 0.0
    if "Mach" not in out.columns: out["Mach"] = 0.0
    if "FuelFlow_kg_s" not in out.columns: out["FuelFlow_kg_s"] = 0.5
    if "RPM_rev_min" not in out.columns: out["RPM_rev_min"] = 12500.0
    atmosphere = [isa_atmosphere(a) for a in out.get("Altitude_m", pd.Series([0.0] * len(out))).to_list()]
    out["atm_temperature_k"] = [row["temperature_k"] for row in atmosphere]
    out["atm_pressure_pa"] = [row["pressure_pa"] for row in atmosphere]

    compressor_states = [
        compressor_outlet_state(row["Tamb_K"], row["Pamb_Pa"], 1.0 + 0.25 * row["Mach"])
        if {"Tamb_K", "Pamb_Pa", "Mach"}.issubset(out.columns)
        else compressor_outlet_state(288.15, 101325.0, 1.0)
        for _, row in out.iterrows()
    ]
    out["pressure_ratio"] = [1.0 + 0.25 * row["Mach"] for _, row in out.iterrows()] if "Mach" in out.columns else 1.0
    out["temperature_ratio"] = [
        state["temperature_out_k"] / max(row["Tamb_K"], 1.0) for _, (row, state) in enumerate(zip(out.to_dict("records"), compressor_states))
    ]
    out["compressor_efficiency"] = [0.85 + 0.01 * row.get("Mach", 0.0) for _, row in out.iterrows()]
    out["combustor_efficiency"] = [0.90 + 0.002 * row.get("FuelFlow_kg_s", 0.0) for _, row in out.iterrows()]
    out["turbine_efficiency"] = [0.88 + 0.01 * row.get("Mach", 0.0) for _, row in out.iterrows()]
    out["compressor_work"] = [state["temperature_out_k"] - row["Tamb_K"] for _, (row, state) in enumerate(zip(out.to_dict("records"), compressor_states))]
    out["turbine_work"] = [0.6 * (state["temperature_out_k"] - row["Tamb_K"]) for _, (row, state) in enumerate(zip(out.to_dict("records"), compressor_states))]
    out["thermal_efficiency"] = [0.3 + 0.05 * row.get("Mach", 0.0) for _, row in out.iterrows()]
    out["thrust"] = [
        1000.0 * (row.get("FuelFlow_kg_s", 0.0) + 0.5 * row.get("Mach", 0.0) + 1.0)
        for _, row in out.iterrows()
    ]
    out["tsfc"] = [
        row.get("FuelFlow_kg_s", 0.0) / max(row.get("T4_K", 1.0), 1.0) for _, row in out.iterrows()
    ]
    out["fuel_air_ratio"] = [row.get("FuelFlow_kg_s", 0.0) / 10.0 for _, row in out.iterrows()]
    out["combustor_heat_release"] = [combustor_temp_rise(r) for r in out["fuel_air_ratio"].to_list()]
    out["pressure_drop_ratio"] = out["P2_Pa"] / out["Pamb_Pa"] if "P2_Pa" in out.columns and "Pamb_Pa" in out.columns else 1.0
    out["temperature_drop_ratio"] = out["T2_K"] / out["Tamb_K"] if "T2_K" in out.columns and "Tamb_K" in out.columns else 1.0
    return out
