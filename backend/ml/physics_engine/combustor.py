"""
combustor.py
============

Physics-based combustor model.

Computes combustor outlet temperature using
energy balance and combustion efficiency.

Outputs:
- Combustor outlet temperature (T3)
- Fuel-Air Ratio (FAR)
- Heat Released
"""

from __future__ import annotations

from CoolProp import CoolProp as CP


# Jet-A lower heating value
LHV = 43e6            # J/kg

# Typical combustion efficiency
ETA_COMB = 0.99


def combustor_temp_rise(
    fuel_air_ratio: float,
    lower_heating_value_j_kg: float = LHV,
    cp_air_j_kgk: float = 1005.0,
) -> float:
    """Return the ideal temperature rise for a fuel-air ratio.

    This helper is the feature-engineering form of the same energy balance
    used by :func:`combustor_temperature`.  Keeping it here avoids duplicating
    the combustion relation in the feature pipeline.
    """

    return float(
        fuel_air_ratio * lower_heating_value_j_kg / cp_air_j_kgk
    )


def combustor_temperature(
    inlet_temperature_k: float,
    fuel_flow_kg_s: float,
    air_mass_flow_kg_s: float = 45.0,
    combustion_efficiency: float = ETA_COMB,
) -> dict[str, float]:
    """
    Compute combustor outlet state.

    Parameters
    ----------
    inlet_temperature_k : float
        Compressor outlet temperature (T2)

    fuel_flow_kg_s : float
        Fuel flow

    air_mass_flow_kg_s : float
        Compressor air flow

    Returns
    -------
    dict
    """

    # Specific heat of air
    cp_air = CP.PropsSI(
        "Cpmass",
        "T", inlet_temperature_k,
        "P", 101325,
        "Air",
    )

    # Fuel-Air Ratio
    fuel_air_ratio = fuel_flow_kg_s / air_mass_flow_kg_s

    # Heat released
    heat_release = (
        fuel_flow_kg_s
        * LHV
        * combustion_efficiency
    )

    # Temperature rise
    delta_T = heat_release / (
        air_mass_flow_kg_s
        * cp_air
    )

    # Combustor outlet temperature
    outlet_temperature = (
        inlet_temperature_k
        + delta_T
    )

    return {

        "temperature_out_k": outlet_temperature,

        "temperature_rise_k": delta_T,

        "fuel_air_ratio": fuel_air_ratio,

        "heat_release_J_s": heat_release,

        "combustion_efficiency": combustion_efficiency,
    }