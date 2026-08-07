"""Compressor thermodynamics for a simple turbojet model."""

from __future__ import annotations


def compressor_outlet_state(temperature_in_k: float, pressure_in_pa: float, pressure_ratio: float) -> dict[str, float]:
    """Estimate compressor exit temperature and pressure using an idealized model."""

    temperature_out_k = temperature_in_k * (1.0 + 0.35 * (pressure_ratio - 1.0))
    pressure_out_pa = pressure_in_pa * pressure_ratio
    return {
        "temperature_out_k": float(temperature_out_k),
        "pressure_out_pa": float(pressure_out_pa),
    }
