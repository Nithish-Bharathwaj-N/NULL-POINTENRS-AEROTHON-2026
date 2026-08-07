"""
AEROTWIN Ω — Failure Mode Scenario Library & Simulation Matrix
===============================================================
16 Physics-Grounded Aerospace Degradation Scenarios for Simulation
and Lifespan Evaluation.
"""

class FailureScenarioLibrary:
    """
    Predefined aerospace failure mode & environmental scenario library.
    Modifies sensor signals and physical degradation parameters for real-time simulation.
    """

    SCENARIOS = {
        "NORMAL": {
            "name": "Normal Operation",
            "category": "Nominal Baseline",
            "desc": "Baseline nominal operating state with standard degradation trajectory.",
            "modifiers": {},
            "creep_multiplier": 1.0,
            "fatigue_multiplier": 1.0,
            "fouling_rate": 0.001
        },
        "COMPRESSOR_FOULING": {
            "name": "Compressor Aerodynamic Fouling",
            "category": "Compressor Failure",
            "desc": "Particulate accumulation on LPC/HPC blades causing flow capacity drop.",
            "modifiers": {"Compressor Exit Temperature (T2)": +18.5, "Compressor Exit Pressure (P2)": -4.2, "RPM": -150.0},
            "creep_multiplier": 1.1,
            "fatigue_multiplier": 1.2,
            "fouling_rate": 0.045
        },
        "COMPRESSOR_SURGE": {
            "name": "Compressor Surge & Stall",
            "category": "Compressor Critical",
            "desc": "Aerodynamic stall producing violent axial pressure oscillations and severe vibration.",
            "modifiers": {"Compressor Exit Pressure (P2)": -8.5, "Combustor Exit Pressure (P3)": -6.0, "RPM": -450.0},
            "creep_multiplier": 1.4,
            "fatigue_multiplier": 3.8,
            "fouling_rate": 0.080
        },
        "COMBUSTOR_EFFICIENCY_LOSS": {
            "name": "Combustor Liner Degradation",
            "category": "Combustor Failure",
            "desc": "Flameholder erosion and liner thermal barrier coating spallation.",
            "modifiers": {"Turbine Inlet Temperature (T3)": -45.0, "Fuel Flow": +0.45},
            "creep_multiplier": 1.5,
            "fatigue_multiplier": 2.2,
            "fouling_rate": 0.010
        },
        "FUEL_INJECTOR_CLOGGING": {
            "name": "Fuel Injector Nozzle Coking",
            "category": "Fuel System Fault",
            "desc": "Fuel nozzle orifice coking leading to circumferential temperature asymmetry.",
            "modifiers": {"Fuel Flow": -0.65, "Turbine Inlet Temperature (T3)": -60.0},
            "creep_multiplier": 1.6,
            "fatigue_multiplier": 2.5,
            "fouling_rate": 0.015
        },
        "BEARING_WEAR": {
            "name": "Bearing Race Spalling & Wear",
            "category": "Mechanical Shaft Fault",
            "desc": "High-pressure spool bearing race pitting, cage wear, and elevated mechanical friction.",
            "modifiers": {"RPM": -300.0, "Fuel Flow": +0.30},
            "creep_multiplier": 1.2,
            "fatigue_multiplier": 1.8,
            "fouling_rate": 0.005
        },
        "TURBINE_BLADE_EROSION": {
            "name": "Turbine NGV Tip Erosion",
            "category": "Turbine Failure",
            "desc": "HPT nozzle guide vane tip clearance increase and aerodynamic profile loss.",
            "modifiers": {"Turbine Exit Temperature (T4)": +35.0, "Turbine Exit Pressure (P4)": -2.1},
            "creep_multiplier": 2.4,
            "fatigue_multiplier": 1.9,
            "fouling_rate": 0.020
        },
        "HIGH_EGT": {
            "name": "High Exhaust Temperature (EGT Excursion)",
            "category": "Thermal Critical",
            "desc": "Critical thermal excursion in low pressure turbine risking blade creep rupture.",
            "modifiers": {"Turbine Exit Temperature (T4)": +65.0, "Turbine Inlet Temperature (T3)": +45.0},
            "creep_multiplier": 4.5,
            "fatigue_multiplier": 2.8,
            "fouling_rate": 0.010
        },
        "LOW_OIL_PRESSURE": {
            "name": "Oil Pressure Scavenge Loss",
            "category": "Lube System Fault",
            "desc": "Scavenge pump pressure drop risking bearing thermal runaway and shaft seizure.",
            "modifiers": {"RPM": -100.0},
            "creep_multiplier": 1.3,
            "fatigue_multiplier": 1.5,
            "fouling_rate": 0.005
        },
        "SAND_INGESTION_DESERT": {
            "name": "Desert Sand Ingestion (CMAS Attack)",
            "category": "Environmental Damage",
            "desc": "Calcia-magnesia-alumino-silicate (CMAS) molten glass deposition on turbine cooling holes.",
            "modifiers": {"Turbine Exit Temperature (T4)": +52.0, "Compressor Exit Pressure (P2)": -5.8, "Fuel Flow": +0.38},
            "creep_multiplier": 3.8,
            "fatigue_multiplier": 2.4,
            "fouling_rate": 0.095
        },
        "COLD_WEATHER_ICING": {
            "name": "Cold Weather Air Inlet Icing",
            "category": "Environmental Operational",
            "desc": "Ice buildup on intake air guide vanes reducing compressor inlet total pressure.",
            "modifiers": {"Compressor Exit Pressure (P2)": -6.2, "RPM": -220.0, "Fuel Flow": +0.25},
            "creep_multiplier": 1.2,
            "fatigue_multiplier": 1.7,
            "fouling_rate": 0.060
        },
        "FOREIGN_OBJECT_DAMAGE": {
            "name": "Foreign Object Damage (FOD)",
            "category": "Structural Critical",
            "desc": "Debris ingestion damaging Fan and Stage 1 LPC blade leading edges.",
            "modifiers": {"RPM": -520.0, "Compressor Exit Pressure (P2)": -9.2, "Turbine Exit Temperature (T4)": +40.0},
            "creep_multiplier": 2.1,
            "fatigue_multiplier": 5.2,
            "fouling_rate": 0.070
        },
        "TURBINE_CREEP_RUNAWAY": {
            "name": "Turbine Larson-Miller Creep Runaway",
            "category": "Thermal Critical",
            "desc": "Accelerated high-temperature Larson-Miller stress rupture of 1st stage HPT blades.",
            "modifiers": {"Turbine Inlet Temperature (T3)": +85.0, "Turbine Exit Temperature (T4)": +72.0},
            "creep_multiplier": 6.8,
            "fatigue_multiplier": 3.1,
            "fouling_rate": 0.015
        },
        "COMBUSTOR_BURN_THROUGH": {
            "name": "Combustor Liner Burn-Through",
            "category": "Combustor Critical",
            "desc": "Local hot-spot flame impingement breaching combustor inner liner wall.",
            "modifiers": {"Fuel Flow": +0.85, "Turbine Inlet Temperature (T3)": +90.0, "Combustor Exit Pressure (P3)": -7.5},
            "creep_multiplier": 5.4,
            "fatigue_multiplier": 4.5,
            "fouling_rate": 0.020
        },
        "ROTOR_IMBALANCE_RESONANCE": {
            "name": "Rotor Dynamic Imbalance & Resonance",
            "category": "Mechanical Critical",
            "desc": "HP spool shaft bow causing 1N rotational vibration resonance at critical speed.",
            "modifiers": {"RPM": -380.0, "Compressor Exit Pressure (P2)": -3.5},
            "creep_multiplier": 1.7,
            "fatigue_multiplier": 4.9,
            "fouling_rate": 0.010
        },
        "TBC_COATING_DELAMINATION": {
            "name": "TBC Thermal Coating Delamination",
            "category": "Materials Degradation",
            "desc": "Thermal cycle spallation of Yttria-Stabilized Zirconia (YSZ) coating from HPT blades.",
            "modifiers": {"Turbine Exit Temperature (T4)": +48.0, "Fuel Flow": +0.32},
            "creep_multiplier": 3.2,
            "fatigue_multiplier": 2.6,
            "fouling_rate": 0.012
        }
    }

    @classmethod
    def apply_scenario(cls, scenario_key: str, base_telemetry: dict) -> dict:
        scenario = cls.SCENARIOS.get(scenario_key.upper(), cls.SCENARIOS["NORMAL"])
        modified = dict(base_telemetry)
        for param, delta in scenario["modifiers"].items():
            if param in modified:
                modified[param] = float(modified[param]) + delta
        modified["Active Scenario Key"] = scenario_key.upper()
        modified["Active Scenario"] = scenario["name"]
        modified["Scenario Category"] = scenario["category"]
        modified["Scenario Description"] = scenario["desc"]
        modified["Creep Multiplier"] = scenario["creep_multiplier"]
        modified["Fatigue Multiplier"] = scenario["fatigue_multiplier"]
        modified["Fouling Rate"] = scenario["fouling_rate"]
        return modified
