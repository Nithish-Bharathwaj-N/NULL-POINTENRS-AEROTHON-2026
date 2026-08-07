"""Metadata describing how the physics model was built, for Member 3's use."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

PACKAGE_VERSION = "2.1.0"


def build_physics_metadata(
    exported_features: dict[str, list[str]],
    row_count: int,
    engine_count: int,
    health_baselines: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Assemble the physics_metadata.json payload.
    """

    return {
        "model_name": "Member2 Turbojet Physics Engine",

        "physics_method": (
            "First-principles Brayton-cycle thermodynamics. "
            "Physics-derived station temperatures, efficiencies and health "
            "metrics are computed from ambient conditions and measured engine "
            "sensor data using thermodynamic relationships. "
            "No engine-specific calibration or machine-learning fitting is "
            "performed inside the physics engine."
        ),

        "prediction_target": (
            "Physics-derived station quantities, efficiencies and component "
            "health indicators."
        ),

        "nominal_assumptions": {
            "compressor_relation": (
                "Compressor temperature rise estimated from measured pressure "
                "ratio using ideal Brayton-cycle relations."
            ),
            "turbine_relation": (
                "Isentropic turbine expansion using measured T3, P3 and P4."
            ),
            "combustor_relation": (
                "Combustor efficiency estimated from measured fuel flow and "
                "temperature rise."
            ),
            "gas_properties": (
                "Specific heat and gamma evaluated using CoolProp."
            ),
        },

        "engine_specific_calibration": False,

        # Finals requirement
        "cycle_used_as_prediction_input": False,
        "cycle_used_for_health_estimation": False,
        "cycle_exported": False,

        "input_features": [
            "Altitude_m",
            "Mach",
            "Tamb_K",
            "Pamb_Pa",
            "RPM_rev_min",
            "FuelFlow_kg_s",
            "P2_Pa",
            "T2_K",
            "P3_Pa",
            "T3_K",
            "P4_Pa",
            "T4_K",
        ],

        "identifier_columns": ["EngineID"],

        "excluded_columns": ["Cycle"],

        "engine_id_usage": "Retained only for traceability; never used as an ML feature.",

        "health_baseline_method": (
            f"{health_baselines.get('baseline_percentile',95.0)}th percentile "
            "of each component efficiency across the processed fleet."
            if health_baselines
            else "engine_health_features.csv not generated."
        ),

        "health_baselines": health_baselines or {},

        "dataset_rows_processed": int(row_count),

        "unique_engines_processed": int(engine_count),

        "exported_features": exported_features,

        "version": PACKAGE_VERSION,

        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
    }