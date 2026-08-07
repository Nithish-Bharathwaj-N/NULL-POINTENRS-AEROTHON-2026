"""
compressor.py
=============

Physics-based compressor model.

Computes compressor outlet temperature, pressure,
compressor work and compressor efficiency using
isentropic compression relations.

Outputs
-------
- Compressor outlet temperature (T2)
- Compressor outlet pressure (P2)
- Compressor work
- Isentropic outlet temperature
"""

from __future__ import annotations

from CoolProp import CoolProp as CP


def compressor_outlet_state(
    inlet_temperature_k: float,
    inlet_pressure_pa: float,
    pressure_ratio: float,
    efficiency: float = 0.88,
) -> dict[str, float]:
    """
    Calculate compressor outlet state.

    Parameters
    ----------
    inlet_temperature_k : float
        Compressor inlet temperature (T1)

    inlet_pressure_pa : float
        Compressor inlet pressure (P1)

    pressure_ratio : float
        Compressor pressure ratio

    efficiency : float
        Compressor isentropic efficiency
    """

    # Air properties
    cp = CP.PropsSI(
        "Cpmass",
        "T", inlet_temperature_k,
        "P", inlet_pressure_pa,
        "Air",
    )

    cv = CP.PropsSI(
        "Cvmass",
        "T", inlet_temperature_k,
        "P", inlet_pressure_pa,
        "Air",
    )

    gamma = cp / cv

    # Outlet pressure
    pressure_out_pa = inlet_pressure_pa * pressure_ratio

    # Ideal (isentropic) outlet temperature
    temperature_isentropic = (
        inlet_temperature_k
        * pressure_ratio ** ((gamma - 1.0) / gamma)
    )

    # Actual outlet temperature
    temperature_out_k = (
        inlet_temperature_k
        + (
            temperature_isentropic
            - inlet_temperature_k
        ) / efficiency
    )

    # Compressor specific work
    compressor_work = cp * (
        temperature_out_k
        - inlet_temperature_k
    )

    return {

        "temperature_out_k": temperature_out_k,

        "pressure_out_pa": pressure_out_pa,

        "temperature_isentropic_k": temperature_isentropic,

        "compressor_work_j_kg": compressor_work,

        "compressor_efficiency": efficiency,

        "gamma": gamma,

        "cp_air_j_kgk": cp,
    }