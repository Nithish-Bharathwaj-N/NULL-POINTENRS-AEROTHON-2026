"""High-level propulsion performance helpers."""

from __future__ import annotations

import numpy as np

from .atmosphere import isa_atmosphere

# Air properties
_GAMMA = 1.4
_R = 287.05


def thrust_proxy(
    altitude_m: float,
    mach: float,
    fuel_flow_kg_s: float,
    p4_pa: float,
    t4_k: float,
) -> float:
    """
    Physics-based thrust proxy.

    Uses:
      - ISA atmosphere
      - Measured turbine exit pressure (P4)
      - Measured turbine exit temperature (T4)
      - Fuel flow

    Does NOT use Cycle.
    """

    atm = isa_atmosphere(altitude_m)

    p0 = atm["pressure_pa"]
    t0 = atm["temperature_k"]

    if (
        p4_pa <= 0
        or t4_k <= 0
        or fuel_flow_kg_s <= 0
    ):
        return float("nan")

    # Approximate exhaust velocity
    exhaust_velocity = np.sqrt(
        2
        * _GAMMA
        / (_GAMMA - 1)
        * _R
        * t4_k
        * (
            1
            - (p0 / p4_pa) ** ((_GAMMA - 1) / _GAMMA)
        )
    )

    # Flight velocity
    a = np.sqrt(_GAMMA * _R * t0)
    flight_velocity = mach * a

    # Relative thrust proxy
    thrust = fuel_flow_kg_s * (
        exhaust_velocity - flight_velocity
    )

    return float(max(thrust, 0.0))