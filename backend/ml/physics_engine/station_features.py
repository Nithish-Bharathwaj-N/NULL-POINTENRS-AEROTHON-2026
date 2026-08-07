"""Gas-path station analysis.

Construct physics station features from measured engine sensors.

Stations:
    Station 1 : Ambient / Intake
    Station 2 : Compressor Exit
    Station 3 : Combustor Exit
    Station 4 : Turbine Exit
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .feature_engineering import build_physics_features


def _get_column(
    df: pd.DataFrame,
    column: str,
    fallback: str | None = None,
) -> pd.Series:
    """
    Return a column if available, otherwise use fallback or NaNs.
    """

    if column in df.columns:
        return df[column].astype(float)

    if fallback is not None and fallback in df.columns:
        return df[fallback].astype(float)

    return pd.Series(np.nan, index=df.index, dtype=float)


def build_station_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build gas-path station features.
    """

    enriched = build_physics_features(df)

    tamb = _get_column(enriched, "Tamb_K", "atm_temperature_k")
    pamb = _get_column(enriched, "Pamb_Pa", "atm_pressure_pa")

    t2 = _get_column(enriched, "T2_K")
    p2 = _get_column(enriched, "P2_Pa")

    t3 = _get_column(enriched, "T3_K")
    p3 = _get_column(enriched, "P3_Pa")

    t4 = _get_column(enriched, "T4_K")
    p4 = _get_column(enriched, "P4_Pa")

    out = pd.DataFrame(index=enriched.index)

    # Keep only EngineID for traceability
    if "EngineID" in enriched.columns:
        out["EngineID"] = enriched["EngineID"]

    # ----------------------------
    # Station 1
    # ----------------------------

    out["Station1_Intake_Temperature_K"] = tamb
    out["Station1_Intake_Pressure_Pa"] = pamb

    # ----------------------------
    # Station 2
    # ----------------------------

    out["Station2_Compressor_Exit_Temperature_K"] = t2
    out["Station2_Compressor_Exit_Pressure_Pa"] = p2

    out["Station2_Temperature_Rise_K"] = t2 - tamb

    out["Station2_Pressure_Ratio"] = (
        p2 / pamb.replace(0, np.nan)
    )

    out["Station2_Temperature_Ratio"] = (
        t2 / tamb.replace(0, np.nan)
    )

    # ----------------------------
    # Station 3
    # ----------------------------

    out["Station3_Combustor_Exit_Temperature_K"] = t3
    out["Station3_Combustor_Exit_Pressure_Pa"] = p3

    out["Station3_Temperature_Rise_K"] = t3 - t2

    out["Station3_Pressure_Ratio"] = (
        p3 / p2.replace(0, np.nan)
    )

    out["Station3_Temperature_Ratio"] = (
        t3 / t2.replace(0, np.nan)
    )

    # ----------------------------
    # Station 4
    # ----------------------------

    out["Station4_Turbine_Exit_Temperature_K"] = t4
    out["Station4_Turbine_Exit_Pressure_Pa"] = p4

    out["Station4_Temperature_Drop_K"] = t3 - t4

    out["Station4_Pressure_Ratio"] = (
        p4 / p3.replace(0, np.nan)
    )

    out["Station4_Temperature_Ratio"] = (
        t4 / t3.replace(0, np.nan)
    )

    return out