"""A compact Brayton cycle wrapper for engine-state estimation."""

from __future__ import annotations

from CoolProp import CoolProp as CP

from .atmosphere import isa_atmosphere
from .compressor import compressor_outlet_state
from .combustor import combustor_temp_rise
from .turbine import turbine_power_ratio


def brayton_cycle_state(altitude_m: float, mach: float, fuel_flow_kg_s: float, pressure_ratio: float = 2.0) -> dict[str, float]:
    """Estimate a simplified Brayton cycle state using idealized Brayton relations and CoolProp."""

    atm = isa_atmosphere(altitude_m)
    comp = compressor_outlet_state(atm["temperature_k"], atm["pressure_pa"], pressure_ratio)
    fuel_air_ratio = fuel_flow_kg_s / 10.0
    combustor_heat = combustor_temp_rise(fuel_air_ratio)
    turbine_ratio = turbine_power_ratio(comp["temperature_out_k"], comp["temperature_out_k"] + combustor_heat)
    thermal_efficiency = 1.0 - (1.0 / pressure_ratio) ** 0.286
    cp_air = CP.PropsSI("Cpmass", "T", comp["temperature_out_k"], "P", comp["pressure_out_pa"], "Air")
    return {
        "altitude_m": float(altitude_m),
        "mach": float(mach),
        "compressor_outlet_temp_k": float(comp["temperature_out_k"]),
        "compressor_outlet_pressure_pa": float(comp["pressure_out_pa"]),
        "combustor_heat_release": float(combustor_heat),
        "turbine_power_ratio": float(turbine_ratio),
        "thermal_efficiency": float(thermal_efficiency),
        "cp_air_j_kgk": float(cp_air),
    }
