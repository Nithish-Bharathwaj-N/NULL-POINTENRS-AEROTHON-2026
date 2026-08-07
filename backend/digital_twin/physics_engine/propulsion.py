"""High-level propulsion performance helpers."""

from __future__ import annotations

from .atmosphere import isa_atmosphere
from .compressor import compressor_outlet_state
from .combustor import combustor_temp_rise


def thrust_proxy(altitude_m: float, mach: float, fuel_flow_kg_s: float) -> float:
    """Create a simple proxy for thrust using atmospheric and combustion terms."""

    atm = isa_atmosphere(altitude_m)
    pressure_ratio = 1.0 + 0.25 * mach
    comp = compressor_outlet_state(atm["temperature_k"], atm["pressure_pa"], pressure_ratio)
    heat_release = combustor_temp_rise(fuel_flow_kg_s / 10.0)
    return float((comp["temperature_out_k"] + heat_release) * (1.0 + mach))
