"""
brayton_cycle.py
================

Physics-Based Brayton Cycle Model

Computes compressor, combustor and turbine state
for every engine sample using thermodynamic relations.

Outputs are used by Member 2 to generate predicted
engine parameters and residuals.
"""

from __future__ import annotations

from CoolProp import CoolProp as CP

from .atmosphere import isa_atmosphere
from .compressor import compressor_outlet_state
from .combustor import combustor_temperature
from .turbine import turbine_exit_state


def brayton_cycle_state(
    altitude_m: float,
    mach: float,
    pressure_ratio: float,
    fuel_flow_kg_s: float,
    compressor_efficiency: float = 0.88,
    turbine_efficiency: float = 0.90,
) -> dict[str, float]:
    """
    Compute one complete Brayton cycle.

    Parameters
    ----------
    altitude_m
    mach
    pressure_ratio
    fuel_flow_kg_s

    Returns
    -------
    dict
    """

    # ------------------------
    # Atmospheric Conditions
    # ------------------------

    atmosphere = isa_atmosphere(altitude_m)

    T1 = atmosphere["temperature_k"]
    P1 = atmosphere["pressure_pa"]
    gamma = atmosphere["gamma"]
    cp = atmosphere["cp_air_j_kgk"]

    # ------------------------
    # Compressor
    # ------------------------

    compressor = compressor_outlet_state(
        inlet_temperature_k=T1,
        inlet_pressure_pa=P1,
        pressure_ratio=pressure_ratio,
        efficiency=compressor_efficiency,
    )

    T2 = compressor["temperature_out_k"]
    P2 = compressor["pressure_out_pa"]

    # ------------------------
    # Combustor
    # ------------------------

    combustor = combustor_temperature(
        inlet_temperature_k=T2,
        fuel_flow_kg_s=fuel_flow_kg_s,
    )

    T3 = combustor["temperature_out_k"]
    fuel_air_ratio = combustor["fuel_air_ratio"]

    # ------------------------
    # Turbine
    # ------------------------

    turbine = turbine_exit_state(
        inlet_temperature_k=T3,
        pressure_ratio=pressure_ratio,
        efficiency=turbine_efficiency,
    )

    T4 = turbine["temperature_out_k"]

    # ------------------------
    # Brayton Efficiency
    # ------------------------

    thermal_efficiency = (
        1.0
        - (1.0 / pressure_ratio)
        ** ((gamma - 1.0) / gamma)
    )

    # ------------------------
    # Compressor Work
    # ------------------------

    compressor_work = cp * (T2 - T1)

    # ------------------------
    # Turbine Work
    # ------------------------

    turbine_work = cp * (T3 - T4)

    # ------------------------
    # Net Cycle Work
    # ------------------------

    net_specific_work = turbine_work - compressor_work

    return {

        "altitude_m": altitude_m,
        "mach": mach,

        "T1_K": T1,
        "P1_Pa": P1,

        "T2_K": T2,
        "P2_Pa": P2,

        "T3_K": T3,

        "T4_K": T4,

        "fuel_air_ratio": fuel_air_ratio,

        "compressor_work_J_kg": compressor_work,

        "turbine_work_J_kg": turbine_work,

        "net_specific_work_J_kg": net_specific_work,

        "thermal_efficiency": thermal_efficiency,

        "cp_air_J_kgK": cp,

        "gamma": gamma,
    }