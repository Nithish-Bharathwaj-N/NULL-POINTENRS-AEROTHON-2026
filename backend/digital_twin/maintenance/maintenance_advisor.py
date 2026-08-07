from physics.degradation_physics import PhysicsDegradationSolver

class AIMaintenanceAdvisor:
    """
    Actionable AI Maintenance Advisor module.
    Translates surrogate health predictions, physics degradation laws (Larson-Miller, Paris' Law, ISO 281),
    and active simulation scenarios into concrete aerospace maintenance protocols.
    """

    COMPONENT_SPECS = {
        "Fan Assembly": {"material": "Ti-6Al-4V Titanium Alloy", "mass_kg": 185.0, "max_temp_c": 300, "limit_psi": 25.0, "interval_cycles": 1500},
        "LPC (Low Pressure Compressor)": {"material": "Inconel 718 Superalloy", "mass_kg": 240.0, "max_temp_c": 450, "limit_psi": 40.0, "interval_cycles": 1200},
        "HPC (High Pressure Compressor)": {"material": "Single-Crystal René N5", "mass_kg": 310.0, "max_temp_c": 680, "limit_psi": 65.0, "interval_cycles": 1000},
        "Combustor Assembly": {"material": "CMC (Ceramic Matrix Composite)", "mass_kg": 140.0, "max_temp_c": 1550, "limit_psi": 60.0, "interval_cycles": 800},
        "HPT (High Pressure Turbine)": {"material": "CMSX-4 Single-Crystal", "mass_kg": 195.0, "max_temp_c": 1450, "limit_psi": 50.0, "interval_cycles": 750},
        "LPT (Low Pressure Turbine)": {"material": "Hastelloy X / Inconel 713C", "mass_kg": 220.0, "max_temp_c": 1050, "limit_psi": 30.0, "interval_cycles": 900},
        "Exhaust Nozzle": {"material": "Titanium Aluminide (TiAl)", "mass_kg": 95.0, "max_temp_c": 950, "limit_psi": 20.0, "interval_cycles": 2000},
        "Fuel System & Injectors": {"material": "316L Stainless Steel / Duplex", "mass_kg": 45.0, "max_temp_c": 250, "limit_psi": 120.0, "interval_cycles": 500},
        "Oil & Lube System": {"material": "Aluminum 7075-T6", "mass_kg": 35.0, "max_temp_c": 180, "limit_psi": 80.0, "interval_cycles": 400},
        "Main Bearings": {"material": "Silicon Nitride Ceramic (Si3N4)", "mass_kg": 28.0, "max_temp_c": 350, "limit_psi": 150.0, "interval_cycles": 600},
        "Accessory Gearbox": {"material": "Magnesium Alloy EV31A", "mass_kg": 65.0, "max_temp_c": 200, "limit_psi": 50.0, "interval_cycles": 1000}
    }

    @classmethod
    def generate_recommendations(cls, predictions: dict, telemetry: dict = None, physics_state: dict = None, active_scenario: str = "NORMAL") -> dict:
        if telemetry is None:
            telemetry = {}

        # Compute physics-calculated degradation & RUL
        phys_deg = PhysicsDegradationSolver.calculate_lifespan(telemetry, predictions, physics_state, active_scenario)

        comp_h = float(predictions.get("Compressor Health", 95.0))
        comb_h = float(predictions.get("Combustor Health", 95.0))
        turb_h = float(predictions.get("Turbine Health", 95.0))
        min_h = min(comp_h, comb_h, turb_h)

        rul_cycles = phys_deg["physics_rul_cycles"]
        rul_hours = phys_deg["physics_rul_hours"]

        recommendation = "Continue nominal operational schedule."
        required_parts = ["None"]
        expected_downtime_hrs = 0
        priority = "NOMINAL"

        if min_h < 75.0 or active_scenario in ["COMPRESSOR_SURGE", "HIGH_EGT", "TURBINE_CREEP_RUNAWAY", "COMBUSTOR_BURN_THROUGH", "FOREIGN_OBJECT_DAMAGE"]:
            recommendation = "CRITICAL: Immediate engine teardown & overhaul required before next flight mission."
            priority = "URGENT / CRITICAL"
            expected_downtime_hrs = 72
            required_parts = ["HPT Blade Set (CMSX-4)", "Combustor Fuel Nozzle Ring", "HP Spool Bearing Pack"]
        elif min_h < 85.0 or active_scenario in ["COMPRESSOR_FOULING", "FUEL_INJECTOR_CLOGGING", "SAND_INGESTION_DESERT", "COLD_WEATHER_ICING"]:
            recommendation = "SCHEDULED MAINTENANCE: Perform detergent compressor wash & fuel nozzle replacement."
            priority = "HIGH"
            expected_downtime_hrs = 18
            required_parts = ["Compressor Cleaning Solvent", "Fuel Injector Nozzle Assembly"]
        elif min_h < 92.0 or active_scenario in ["BEARING_WEAR", "TURBINE_BLADE_EROSION", "TBC_COATING_DELAMINATION"]:
            recommendation = "PREVENTIVE MAINTENANCE: Inspect thermal barrier coating and measure blade tip clearance."
            priority = "MEDIUM"
            expected_downtime_hrs = 6
            required_parts = ["Borescope Inspection Kit", "Gasket Seals"]

        return {
            "action_tier": priority,
            "maintenance_action": recommendation,
            "estimated_rul_cycles": int(rul_cycles),
            "estimated_rul_hours": int(rul_hours),
            "limiting_physical_mechanism": phys_deg["dominant_degradation_mechanism"],
            "larson_miller_parameter": phys_deg["larson_miller_parameter"],
            "creep_consumption_pct": phys_deg["creep_life_consumption_pct"],
            "crack_growth_rate_mm_cycle": phys_deg["paris_law_crack_rate_mm_cycle"],
            "tbc_oxidation_microns": phys_deg["tbc_oxidation_microns"],
            "bearing_l10h_hours": phys_deg["bearing_l10h_hours"],
            "recommended_inspection": "Visual Borescope & Acoustic Vibration Sweep",
            "required_parts": required_parts,
            "estimated_downtime_hours": expected_downtime_hrs,
            "component_specs": cls.COMPONENT_SPECS
        }
