"""Turbine modeling helpers for turbomachinery analysis."""

from __future__ import annotations


def turbine_power_ratio(temperature_in_k: float, temperature_out_k: float) -> float:
    """Return a simple turbine work ratio from inlet/outlet temperatures."""

    return float((temperature_in_k - temperature_out_k) / max(temperature_in_k, 1.0))
