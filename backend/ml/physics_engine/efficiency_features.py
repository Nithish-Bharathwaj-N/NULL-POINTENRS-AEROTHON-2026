"""Component and engine efficiency features derived from physics calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .feature_engineering import build_physics_features


def _speed_of_sound(
    temperature_k: pd.Series,
    gamma: pd.Series,
    r_specific: float = 287.05,
) -> pd.Series:
    return np.sqrt(gamma.astype(float) * r_specific * temperature_k.astype(float))


def mass_flow_rate_kg_s(enriched: pd.DataFrame) -> pd.Series:
    """Estimate air mass flow from fuel flow and the derived fuel-air ratio."""

    fuel_flow = enriched.get(
        "FuelFlow_kg_s",
        pd.Series(0.0, index=enriched.index),
    ).astype(float)
    far = enriched["fuel_air_ratio"].astype(float)
    return pd.Series(
        np.where(far > 1e-9, fuel_flow / far.replace(0.0, np.nan), np.nan),
        index=enriched.index,
    )


def _propulsive_efficiency(
    enriched: pd.DataFrame,
    mass_flow_kg_s: pd.Series,
) -> pd.Series:
    mach = enriched.get(
        "Mach",
        pd.Series(0.0, index=enriched.index),
    ).astype(float)
    v0 = mach * _speed_of_sound(
        enriched["atm_temperature_k"],
        enriched["atm_gamma"],
    )
    thrust = enriched.get(
        "Thrust_N",
        enriched.get("thrust", pd.Series(0.0, index=enriched.index)),
    ).astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        vj = v0 + np.where(
            mass_flow_kg_s > 1e-9,
            thrust / mass_flow_kg_s,
            np.nan,
        )
    denominator = vj + v0
    values = np.where(
        (v0 > 1e-6) & (denominator > 1e-6),
        2.0 * v0 / denominator,
        0.0,
    )
    return pd.Series(values, index=enriched.index).clip(lower=0.0, upper=1.0)


def build_efficiency_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build one efficiency row per input row.

    ``EngineID`` is copied solely for traceability.  No sequencing column is
    accepted or emitted.
    """

    enriched = build_physics_features(df)
    mass_flow = mass_flow_rate_kg_s(enriched)
    thermal = enriched["thermal_efficiency"].astype(float)
    propulsive = _propulsive_efficiency(enriched, mass_flow)

    out = pd.DataFrame(index=enriched.index)
    if "EngineID" in enriched.columns:
        out["EngineID"] = enriched["EngineID"]
    out["pressure_ratio"] = enriched["pressure_ratio"].astype(float)
    out["temperature_ratio"] = enriched["temperature_ratio"].astype(float)
    out["compressor_efficiency"] = enriched[
        "compressor_isentropic_efficiency"
    ].astype(float)
    out["turbine_efficiency"] = enriched[
        "turbine_isentropic_efficiency"
    ].astype(float)
    out["combustor_efficiency"] = enriched["combustor_efficiency"].astype(float)
    out["thermal_efficiency"] = thermal
    out["propulsive_efficiency"] = propulsive
    out["overall_efficiency"] = (thermal * propulsive).clip(0.0, 1.0)
    return out