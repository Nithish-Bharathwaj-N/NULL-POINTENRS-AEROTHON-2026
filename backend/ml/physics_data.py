"""
physics_data.py
================
BEGINNER NOTE: this file loads the physics-derived features Member 2
computed (compressor/turbine/combustor efficiency, station-by-station
gas path data, residuals) and merges them onto our sensor data.

WHY THESE FEATURES ARE SO MUCH BETTER than the raw sensors or even
our own engineered ratios: compressor_efficiency, for example, is
computed by comparing the ACTUAL temperature rise across the
compressor to the IDEAL (isentropic, thermodynamically perfect)
temperature rise a brand-new compressor would produce at that exact
pressure ratio. A fouled/eroded compressor does less useful work per
unit of temperature rise than an ideal one - so this ratio drops as
the component wears, almost regardless of what altitude or Mach
number the engine happens to be flying at. That's exactly the
"cancel out flight-condition noise, keep wear signal" property we
wanted back when we first tried doing this ourselves with simple
ratios - Member 2's version does it properly, using real
thermodynamics (isentropic relations + CoolProp gas properties)
instead of the crude approximation we used as a placeholder.

LEAKAGE GUARD: residual_Thrust_N and residual_TSFC_g_N_s are dropped
here, unconditionally. Why: predicted_X + residual_X = the actual
measured X, exactly (verified to 11 decimal places). If a model got
BOTH residual_Thrust_N and predicted_Thrust_N as inputs while trying
to predict Thrust_N, it could trivially reconstruct the exact answer
- that's leakage, not learning. Dropping the residual (but keeping
predicted_Thrust_N, which is just a helpful physics-based estimate,
not the answer) avoids this for both Thrust_N and TSFC_g_N_s.
"""

import pandas as pd
from pathlib import Path

# NOTE: this file deliberately does NOT import from config.py. config.py
# imports physics_feature_columns() from here (to build FEATURE_COLUMNS),
# so importing config.py back would create a circular import. Path/key
# constants are small enough to define locally instead.
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "datasets"
PHYSICS_DIR = DATA_DIR / "physics"
JOIN_KEYS = ["EngineID", "Cycle"]

LEAKAGE_COLUMNS_TO_DROP = [
    # From residual_dataset.csv: predicted_X + residual_X = actual X exactly
    # (verified to 11 decimal places), so keeping BOTH the residual and the
    # target would let a model trivially reconstruct the answer.
    "residual_Thrust_N", "residual_TSFC_g_N_s",

    # From overall_engine_features.csv: thrust_n is a literal, unmodified
    # copy of the measured Thrust_N column (max difference ~1e-12, i.e.
    # floating-point noise) - NOT a physics-computed prediction despite the
    # column name/location. tsfc_kg_per_n_s and specific_thrust_n_s_per_kg
    # are both deterministic functions of that same leaked value
    # (correlation 1.0 and ~1.0 with the true targets respectively). All
    # three would be exact or near-exact leakage for the Thrust_N/
    # TSFC_g_N_s targets. Flagged back to Member 2 - see
    # documentation/physics_integration.md.
    "thrust_n", "tsfc_kg_per_n_s", "specific_thrust_n_s_per_kg",
]

# From overall_engine_features.csv: mass_flow_rate_kg_s is a hardcoded
# constant (10.0 for all 300 rows, confirmed by direct inspection - not
# leakage, just contains zero information), and fuel_air_ratio is exactly
# FuelFlow_kg_s / 10, a pure rescaling of a column we already have as a raw
# sensor input. Neither adds anything a model can use; dropped as noise
# rather than as a leakage risk.
USELESS_PLACEHOLDER_COLUMNS_TO_DROP = ["mass_flow_rate_kg_s", "fuel_air_ratio"]


def load_physics_features() -> pd.DataFrame:
    """
    Load and merge all of Member 2's physics feature files into one
    DataFrame, keyed by (EngineID, Cycle) - the same join keys used
    everywhere else in this project.
    """
    efficiency = pd.read_csv(PHYSICS_DIR / "efficiency_features.csv")
    overall = pd.read_csv(PHYSICS_DIR / "overall_engine_features.csv")
    station = pd.read_csv(PHYSICS_DIR / "physics_station_features.csv")
    residuals = pd.read_csv(PHYSICS_DIR / "residual_dataset.csv")

    overall = overall.drop(columns=[
        c for c in LEAKAGE_COLUMNS_TO_DROP + USELESS_PLACEHOLDER_COLUMNS_TO_DROP
        if c in overall.columns
    ])
    residuals = residuals.drop(columns=[
        c for c in LEAKAGE_COLUMNS_TO_DROP if c in residuals.columns
    ])

    merged = (
        efficiency
        .merge(overall, on=JOIN_KEYS)
        .merge(station, on=JOIN_KEYS)
        .merge(residuals, on=JOIN_KEYS)
    )
    return merged


def physics_feature_columns() -> list:
    """
    The names of every physics-derived column (everything except the
    EngineID/Cycle join keys) - used by config.py to build the full
    feature list without hardcoding ~40 column names by hand.
    """
    df = load_physics_features()
    return [c for c in df.columns if c not in JOIN_KEYS]


if __name__ == "__main__":
    physics = load_physics_features()
    print(f"Physics feature rows: {len(physics)}")
    print(f"Physics feature columns ({len(physics_feature_columns())}):")
    for col in physics_feature_columns():
        print(f"  {col}")
