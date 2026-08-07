"""Feature engineering utilities for the Aerothon Finals physics engine."""

from __future__ import annotations

import pandas as pd

from .atmosphere import isa_atmosphere
from .compressor import compressor_outlet_state
from .combustor import combustor_temp_rise


def build_physics_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build physics features while retaining ``EngineID`` only for traceability.

    The Finals input files may still contain the legacy sequencing field.  It
    is removed at this shared boundary so no downstream calculation can use or
    export it accidentally.
    """

    out = df.drop(columns=["Cycle"], errors="ignore").copy()
    default_altitude = pd.Series(0.0, index=out.index)
    atmosphere = [
        isa_atmosphere(value)
        for value in out.get("Altitude_m", default_altitude).fillna(0.0).to_list()
    ]
    out["atm_temperature_k"] = [row["temperature_k"] for row in atmosphere]
    out["atm_pressure_pa"] = [row["pressure_pa"] for row in atmosphere]
    out["atm_gamma"] = [row["gamma"] for row in atmosphere]
    out["atm_cp_air_j_kgk"] = [row["cp_air_j_kgk"] for row in atmosphere]

    measured_pressure_ratio: list[float] = []
    compressor_states: list[dict[str, float]] = []
    for _, row in out.iterrows():
        if {"P2_Pa", "Pamb_Pa"}.issubset(out.columns) and float(row.get("Pamb_Pa", 0.0)) > 0.0:
            ratio = float(row["P2_Pa"]) / float(row["Pamb_Pa"])
        elif "Mach" in out.columns:
            ratio = 1.0 + 0.25 * float(row.get("Mach", 0.0))
        else:
            ratio = 1.0
        ratio = max(ratio, 1e-9)
        measured_pressure_ratio.append(ratio)

        if {"Tamb_K", "Pamb_Pa"}.issubset(out.columns):
            compressor_states.append(
                compressor_outlet_state(
                    float(row["Tamb_K"]),
                    float(row["Pamb_Pa"]),
                    ratio,
                )
            )
        else:
            compressor_states.append(compressor_outlet_state(288.15, 101325.0, ratio))

    records = out.to_dict("records")
    out["pressure_ratio"] = measured_pressure_ratio
    out["compressor_pressure_ratio"] = out["pressure_ratio"].astype(float)
    out["temperature_ratio"] = [
        state["temperature_out_k"] / max(float(row.get("Tamb_K", 1.0)), 1.0)
        for row, state in zip(records, compressor_states)
    ]
    out["compressor_temp_ratio"] = out["temperature_ratio"].astype(float)
    out["compressor_work"] = [
        state["temperature_out_k"] - float(row.get("Tamb_K", 288.15))
        for row, state in zip(records, compressor_states)
    ]
    out["turbine_work"] = 0.6 * out["compressor_work"].astype(float)
    out["fuel_air_ratio"] = [
        float(row.get("FuelFlow_kg_s", 0.0)) / 10.0 for row in records
    ]
    out["combustor_heat_release"] = [
        combustor_temp_rise(value) for value in out["fuel_air_ratio"].to_list()
    ]
    out["thermal_efficiency"] = [
        0.3 + 0.05 * float(row.get("Mach", 0.0)) for row in records
    ]
    out["thrust"] = [
        1000.0
        * (float(row.get("FuelFlow_kg_s", 0.0)) + 0.5 * float(row.get("Mach", 0.0)) + 1.0)
        for row in records
    ]
    out["tsfc"] = [
        float(row.get("FuelFlow_kg_s", 0.0)) / max(float(row.get("T4_K", 1.0)), 1.0)
        for row in records
    ]
    out["pressure_drop_ratio"] = (
        out["P2_Pa"].astype(float) / out["Pamb_Pa"].replace(0, pd.NA).astype(float)
        if {"P2_Pa", "Pamb_Pa"}.issubset(out.columns)
        else pd.Series(1.0, index=out.index)
    )
    out["temperature_drop_ratio"] = (
        out["T2_K"].astype(float) / out["Tamb_K"].replace(0, pd.NA).astype(float)
        if {"T2_K", "Tamb_K"}.issubset(out.columns)
        else pd.Series(1.0, index=out.index)
    )

    out["T2s_K"] = [
        float(row["Tamb_K"])
        * (float(row["P2_Pa"]) / float(row["Pamb_Pa"]))
        ** ((float(row["atm_gamma"]) - 1.0) / float(row["atm_gamma"]))
        if {"Tamb_K", "P2_Pa", "Pamb_Pa"}.issubset(row)
        and float(row["Pamb_Pa"]) > 0.0
        else float("nan")
        for row in out.to_dict("records")
    ]
    out["compressor_isentropic_efficiency"] = [
        (float(row["T2s_K"]) - float(row["Tamb_K"]))
        / max(float(row["T2_K"]) - float(row["Tamb_K"]), 1e-6)
        if {"T2s_K", "Tamb_K", "T2_K"}.issubset(row)
        and float(row["T2_K"]) > float(row["Tamb_K"])
        else float("nan")
        for row in out.to_dict("records")
    ]
    out["compressor_isentropic_efficiency"] = out[
        "compressor_isentropic_efficiency"
    ].clip(lower=0.0, upper=1.0)

    out["T4s_K"] = [
        float(row["T3_K"])
        * (float(row["P4_Pa"]) / float(row["P3_Pa"]))
        ** ((float(row["atm_gamma"]) - 1.0) / float(row["atm_gamma"]))
        if {"T3_K", "P4_Pa", "P3_Pa"}.issubset(row)
        and float(row["P3_Pa"]) > 0.0
        else float("nan")
        for row in out.to_dict("records")
    ]
    out["turbine_isentropic_efficiency"] = [
        (float(row["T3_K"]) - float(row["T4_K"]))
        / max(float(row["T3_K"]) - float(row["T4s_K"]), 1e-6)
        if {"T3_K", "T4_K", "T4s_K"}.issubset(row)
        and float(row["T3_K"]) > float(row["T4s_K"])
        else float("nan")
        for row in out.to_dict("records")
    ]
    out["turbine_isentropic_efficiency"] = out[
        "turbine_isentropic_efficiency"
    ].clip(lower=0.0, upper=1.0)

    out["combustor_ideal_temp_rise"] = [
        combustor_temp_rise(float(row.get("fuel_air_ratio", 0.0)))
        for row in out.to_dict("records")
    ]
    out["combustor_efficiency"] = [
        (float(row["T3_K"]) - float(row["T2_K"]))
        / max(float(row["combustor_ideal_temp_rise"]), 1e-6)
        if {"T3_K", "T2_K", "combustor_ideal_temp_rise"}.issubset(row)
        else float("nan")
        for row in out.to_dict("records")
    ]
    out["combustor_efficiency"] = out["combustor_efficiency"].clip(
        lower=0.0, upper=1.0
    )
    return out
