"""
AEROTWIN Ω — Physics-Informed Degradation & Lifespan Solver
============================================================
Calculates physical lifespan consumption and Remaining Useful Life (RUL)
using first-principles thermodynamics and fracture/materials mechanics:

1. Larson-Miller Parameter (LMP) — High-Temperature Turbine Blade Creep
2. Paris' Law — Thermal Cycle Fatigue Crack Growth (da/dN = C(ΔK)^m)
3. Arrhenius Oxidation Kinetics — Thermal Barrier Coating Depletion
4. ISO 281 Bearing L10h Life — Vibration-Amplified Bearing Dynamic Load
5. Compressor Aerodynamic Capacity Loss — Contaminate Deposition Kinetics
"""

import math


class PhysicsDegradationSolver:
    """
    Computes component lifespan degradation and Remaining Useful Life (RUL)
    from operating physical states (T2, T3, T4, P2, P3, P4, RPM, Vibration).
    """

    # Physical Constants
    GAS_CONSTANT_R = 8.314        # J/(mol·K)
    ACTIVATION_ENERGY_OX = 145000 # J/mol (Oxidation activation energy for Ni-superalloy)
    LARSON_MILLER_C = 20.0        # Constant for Single-Crystal Nickel Alloy (CMSX-4)
    CREEP_ACTIVATION_Q = 280000   # J/mol (Creep activation energy)
    BEARING_C_RATING = 48000.0    # Dynamic load rating (N) for HP spool bearing pack
    NOMINAL_DESIGN_LIFE_CYCLES = 1200.0 # Standard design life baseline cycles

    @classmethod
    def calculate_lifespan(cls, telemetry: dict, predictions: dict, physics_state: dict, active_scenario: str = "NORMAL") -> dict:
        """
        Executes physics degradation equations for the current telemetry frame.

        Returns:
            dict containing:
            - physics_rul_cycles (float): Physics-calculated RUL in cycles
            - physics_rul_hours (float): Physics-calculated RUL in operating hours
            - creep_life_consumption_pct (float): Larson-Miller creep damage %
            - thermal_fatigue_damage_rate (float): Paris' Law crack growth rate mm/cycle
            - coating_oxidation_depth_um (float): Surface oxidation layer depth (microns)
            - bearing_l10h_remaining (float): ISO 281 Bearing life (hours)
            - dominant_degradation_mechanism (str): Primary physical driver of lifespan loss
        """
        rpm = float(telemetry.get("RPM", 12500.0))
        T2_C = float(telemetry.get("Compressor Exit Temperature (T2)", 233.0))
        T3_C = float(telemetry.get("Turbine Inlet Temperature (T3)", 1770.0))
        T4_C = float(telemetry.get("Turbine Exit Temperature (T4)", 1030.0))
        P2 = float(telemetry.get("Compressor Exit Pressure (P2)", 49.0))
        P3 = float(telemetry.get("Combustor Exit Pressure (P3)", 46.0))
        P4 = float(telemetry.get("Turbine Exit Pressure (P4)", 14.5))
        cycle = float(telemetry.get("Cycle", 1.0))

        # Convert temperatures to Kelvin
        T2_K = T2_C + 273.15
        T3_K = T3_C + 273.15
        T4_K = T4_C + 273.15

        # Get overall health prediction from PINN
        ov_health = float(predictions.get("Overall Health", 99.5))
        comp_health = float(predictions.get("Compressor Health", 99.5))
        comb_health = float(predictions.get("Combustor Health", 99.5))
        turb_health = float(predictions.get("Turbine Health", 99.5))

        # ── 1. Larson-Miller Creep Damage (Turbine Blades) ────────────────
        # Larson-Miller Parameter P = T_K * (20 + log10(t_rupture))
        # Rupture time t_r (hours) decreases exponentially with T4_K temperature excess:
        nom_T4_K = 1030.0 + 273.15  # 1303.15 K
        thermal_overstress_ratio = max(1.0, T4_K / nom_T4_K)
        
        # Exponential creep acceleration factor via Arrhenius-type equation
        creep_acceleration = math.exp((cls.CREEP_ACTIVATION_Q / cls.GAS_CONSTANT_R) * (1/nom_T4_K - 1/T4_K))
        creep_damage_per_cycle = 0.0008 * creep_acceleration * (1.0 + (100.0 - turb_health) / 20.0)
        creep_consumption_pct = min(100.0, cycle * creep_damage_per_cycle * 100.0)

        # Larson-Miller Parameter value
        larson_miller_val = (T4_K * (cls.LARSON_MILLER_C + math.log10(max(100.0, 5000.0 / creep_acceleration)))) / 1000.0

        # ── 2. Paris' Law Low-Cycle Thermal Fatigue (LCF) ───────────────
        # da/dN = C * (ΔK)^m where ΔK is proportional to thermal stress gradient (T3 - T2)
        delta_T = max(100.0, T3_K - T2_K)
        nom_delta_T = 1770.0 - 233.0 # 1537 K
        stress_intensity_factor = (delta_T / nom_delta_T) ** 2.5
        
        # Paris' Law crack growth rate in mm/cycle
        crack_growth_rate_mm = 1.2e-4 * stress_intensity_factor * (1.0 + (100.0 - comb_health) / 30.0)
        accumulated_crack_len_mm = min(5.0, cycle * crack_growth_rate_mm)

        # ── 3. Arrhenius Thermal Barrier Coating (TBC) Oxidation ───────
        # Oxidation growth thickness x^2 = k_ox * t
        t_hours = cycle * 3.5  # average 3.5 hours per mission cycle
        k_ox = 0.05 * math.exp(-cls.ACTIVATION_ENERGY_OX / (cls.GAS_CONSTANT_R * T4_K)) * 1e5
        tbc_oxidation_microns = math.sqrt(max(0.001, k_ox * t_hours))

        # ── 4. ISO 281 Bearing L10h Fatigue Life ───────────────────────
        # Dynamic equivalent load P amplified by rotor imbalance vibration
        vibration_amp = 0.0003
        if physics_state and "vibration" in physics_state:
            vibration_amp = physics_state["vibration"].get("total_amplitude", 0.0003)
            
        load_factor = 1.0 + vibration_amp * 2500.0  # vibration amplifies radial load
        dynamic_load_P = 8500.0 * load_factor
        
        # ISO 281 L10h life equation for roller bearings: L10h = (10^6 / (60 * RPM)) * (C / P)^(10/3)
        bearing_l10h = (1e6 / (60.0 * max(rpm, 100.0))) * ((cls.BEARING_C_RATING / max(dynamic_load_P, 1.0)) ** 3.333)

        # ── 5. Combined Physics Lifespan Integration ────────────────────
        # Determine limiting physical mechanism
        life_factors = {
            "Turbine Blade Thermal Creep (Larson-Miller)": 1.0 / max(0.1, creep_acceleration),
            "Low-Cycle Thermal Fatigue Crack Growth": 1.0 / max(0.1, stress_intensity_factor),
            "TBC Coating Oxidation & Spallation": 1.0 / max(0.1, math.sqrt(tbc_oxidation_microns + 0.1)),
            "Compressor Aero Fouling & Flow Stall": comp_health / 100.0,
            "High-Spool Bearing Mechanical Fatigue": min(1.5, bearing_l10h / 6000.0)
        }

        # Find limiting mechanism
        limiting_mechanism = min(life_factors, key=life_factors.get)
        limiting_factor = life_factors[limiting_mechanism]

        # Calculate Physics RUL in cycles and flight hours
        base_rul = (ov_health / 100.0) * cls.NOMINAL_DESIGN_LIFE_CYCLES
        physics_rul_cycles = max(5.0, round(base_rul * min(1.0, limiting_factor), 1))
        physics_rul_hours = max(15.0, round(physics_rul_cycles * 3.5, 1))

        return {
            "physics_rul_cycles": physics_rul_cycles,
            "physics_rul_hours": physics_rul_hours,
            "larson_miller_parameter": round(larson_miller_val, 2),
            "creep_life_consumption_pct": round(creep_consumption_pct, 2),
            "paris_law_crack_rate_mm_cycle": round(crack_growth_rate_mm, 6),
            "accumulated_crack_length_mm": round(accumulated_crack_len_mm, 3),
            "tbc_oxidation_microns": round(tbc_oxidation_microns, 2),
            "bearing_l10h_hours": round(bearing_l10h, 1),
            "limiting_factor_ratio": round(limiting_factor, 3),
            "dominant_degradation_mechanism": limiting_mechanism
        }
