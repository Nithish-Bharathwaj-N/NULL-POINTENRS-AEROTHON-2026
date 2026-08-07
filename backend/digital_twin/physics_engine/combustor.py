"""Combustor models for estimating temperature rise."""

from __future__ import annotations


def combustor_temp_rise(fuel_air_ratio: float, lower_heating_value_j_kg: float = 4.3e7) -> float:
    """Return an approximate temperature rise from fuel addition."""

    return float(fuel_air_ratio * lower_heating_value_j_kg / 1005.0)
