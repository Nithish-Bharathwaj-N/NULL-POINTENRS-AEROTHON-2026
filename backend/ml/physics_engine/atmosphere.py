"""
atmosphere.py
=============

International Standard Atmosphere (ISA) model with CoolProp support.

This module computes atmospheric properties required for the
physics-based gas turbine engine model.

Outputs
-------
- Temperature (K)
- Pressure (Pa)
- Density (kg/m³)
- Specific Heat (Cp)
- Specific Heat (Cv)
- Gamma
- Speed of Sound
"""

from __future__ import annotations

import math
from CoolProp import CoolProp as CP

# -----------------------------
# ISA Constants
# -----------------------------
T0 = 288.15          # Sea-level temperature (K)
P0 = 101325.0        # Sea-level pressure (Pa)
L = 0.0065           # Temperature lapse rate (K/m)
R = 287.05           # Gas constant for air (J/kg/K)
G = 9.80665          # Gravity (m/s²)


def isa_atmosphere(altitude_m: float) -> dict[str, float]:
    """
    Calculate ISA atmospheric properties.

    Parameters
    ----------
    altitude_m : float
        Altitude above mean sea level (m).

    Returns
    -------
    dict
        Atmospheric state.
    """

    altitude_m = max(float(altitude_m), 0.0)

    # ISA Temperature
    temperature_k = T0 - (L * altitude_m)

    # ISA Pressure
    pressure_pa = P0 * (temperature_k / T0) ** (G / (R * L))

    # Density
    density_kg_m3 = pressure_pa / (R * temperature_k)

    # CoolProp properties
    cp_air = CP.PropsSI(
        "Cpmass",
        "T", temperature_k,
        "P", pressure_pa,
        "Air",
    )

    cv_air = CP.PropsSI(
        "Cvmass",
        "T", temperature_k,
        "P", pressure_pa,
        "Air",
    )

    gamma = cp_air / cv_air

    # Speed of Sound
    speed_of_sound = math.sqrt(
        gamma * R * temperature_k
    )

    return {
        "altitude_m": altitude_m,
        "temperature_k": temperature_k,
        "pressure_pa": pressure_pa,
        "density_kg_m3": density_kg_m3,
        "cp_air_j_kgk": cp_air,
        "cv_air_j_kgk": cv_air,
        "gamma": gamma,
        "speed_of_sound_m_s": speed_of_sound,
    }