"""Turbine modeling helpers for turbomachinery analysis."""

from __future__ import annotations

import math


def turbine_power_ratio(
    temperature_in_k: float,
    temperature_out_k: float,
) -> float:
    """
    Compute the turbine work ratio.

    The ratio represents the fraction of turbine inlet thermal energy
    extracted by the turbine.

    Returns
    -------
    float
        Turbine work ratio in the range [0, 1] whenever physically valid.
        Returns NaN for invalid inputs.
    """

    if (
        not math.isfinite(temperature_in_k)
        or not math.isfinite(temperature_out_k)
        or temperature_in_k <= 0.0
    ):
        return float("nan")

    ratio = (
        temperature_in_k - temperature_out_k
    ) / temperature_in_k

    # Clamp to physically meaningful limits
    return float(max(0.0, min(1.0, ratio)))