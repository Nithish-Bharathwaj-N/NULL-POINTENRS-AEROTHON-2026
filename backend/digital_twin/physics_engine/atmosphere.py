"""Atmospheric property helpers for propulsion modeling."""

from __future__ import annotations

try:
    from CoolProp import CoolProp as CP
    HAS_COOLPROP = True
except ImportError:
    HAS_COOLPROP = False

def isa_atmosphere(altitude_m: float) -> dict[str, float]:
    """Return ISA atmospheric state at the requested altitude in meters."""
    temperature_k = 288.15 - 0.0065 * altitude_m
    pressure_pa = 101325.0 * ((288.15 - 0.0065 * altitude_m) / 288.15) ** 5.2561
    density_kg_m3 = pressure_pa / (287.05 * temperature_k)
    
    if HAS_COOLPROP:
        try:
            cp_air = CP.PropsSI("Cpmass", "T", temperature_k, "P", pressure_pa, "Air")
            cv_air = CP.PropsSI("Cvmass", "T", temperature_k, "P", pressure_pa, "Air")
            gamma = cp_air / cv_air
        except Exception:
            cp_air, cv_air, gamma = 1005.0, 718.0, 1.4
    else:
        cp_air, cv_air, gamma = 1005.0, 718.0, 1.4

    return {
        "altitude_m": float(altitude_m),
        "temperature_k": float(temperature_k),
        "pressure_pa": float(pressure_pa),
        "density_kg_m3": float(density_kg_m3),
        "cp_air_j_kgk": float(cp_air),
        "cv_air_j_kgk": float(cv_air),
        "gamma": float(gamma),
    }
