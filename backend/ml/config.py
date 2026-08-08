"""
config.py
=========
Central configuration for data paths, column definitions, and model target bounds.
Points to PS_2_final_dataset and PS2_dataset (60,000 total engine rows).
"""

from pathlib import Path
from backend.ml.features import ENGINEERED_COLUMNS

# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_DIR = PROJECT_ROOT / "public" / "dataset"
EXTRA_DATA_DIR = PROJECT_ROOT / "backend" / "digital_twin" / "data"
MODELS_DIR = PROJECT_ROOT / "trained_models"
RESULTS_DIR = PROJECT_ROOT / "results"

TRAIN_CSV = DATA_DIR / "train.csv"
TEST_CSV = DATA_DIR / "test.csv"
GROUND_TRUTH_CSV = DATA_DIR / "ground_truth.csv"
FULL_DATASET_CSV = DATA_DIR / "turbojet_complete_dataset.csv"

# ---------------------------------------------------------------------
# COLUMNS
# ---------------------------------------------------------------------
# The raw sensor readings, straight from the CSV.
RAW_FEATURE_COLUMNS = [
    "Altitude_m", "Mach", "Tamb_K", "Pamb_Pa",
    "RPM_rev_min", "FuelFlow_kg_s",
    "P2_Pa", "T2_K", "P3_Pa", "T3_K", "P4_Pa", "T4_K",
]

# Health targets correlate with raw sensors, thermodynamic station features, and engine usage (Cycle)
HEALTH_FEATURE_COLUMNS = RAW_FEATURE_COLUMNS + ENGINEERED_COLUMNS + ["Cycle"]

# Performance targets depend on flight conditions and aero-thermal station features
PERFORMANCE_FEATURE_COLUMNS = RAW_FEATURE_COLUMNS + ENGINEERED_COLUMNS

# Target-specific feature maps
TARGET_FEATURE_COLUMNS = {
    "CompressorHealth": HEALTH_FEATURE_COLUMNS,
    "CombustorHealth": HEALTH_FEATURE_COLUMNS,
    "TurbineHealth": HEALTH_FEATURE_COLUMNS,
    "OverallHealth": HEALTH_FEATURE_COLUMNS,
    "Thrust_N": PERFORMANCE_FEATURE_COLUMNS,
    "TSFC_g_N_s": PERFORMANCE_FEATURE_COLUMNS,
}

# Total fallback feature set
FEATURE_COLUMNS = RAW_FEATURE_COLUMNS + ENGINEERED_COLUMNS + ["Cycle"]

# Per-target tuned Ridge regularization strength (alpha)
TARGET_ALPHA = {
    "CompressorHealth": 1.0,
    "CombustorHealth": 1.0,
    "TurbineHealth": 1.0,
    "OverallHealth": 1.0,
    "Thrust_N": 0.1,
    "TSFC_g_N_s": 0.1,
}

# The target variables predicted by our transparent ML models
TARGET_COLUMNS = [
    "CompressorHealth", "CombustorHealth", "TurbineHealth",
    "OverallHealth", "Thrust_N", "TSFC_g_N_s",
]

# Physically valid output ranges per target.
TARGET_BOUNDS = {
    "CompressorHealth": (0.0, 1.0),
    "CombustorHealth": (0.0, 1.0),
    "TurbineHealth": (0.0, 1.0),
    "OverallHealth": (0.0, 1.0),
    "Thrust_N": (0.0, None),
    "TSFC_g_N_s": (0.0, None),
}

# Model architecture specification: 100% white-box interpretable models
BEST_TRANSPARENT_MODELS = {
    "CompressorHealth": "poly_ridge",
    "CombustorHealth": "poly_ridge",
    "TurbineHealth": "poly_ridge",
    "OverallHealth": "poly_ridge",
    "Thrust_N": "poly_ridge",
    "TSFC_g_N_s": "poly_ridge",
}


# The columns used to match sensor rows to their true labels.
JOIN_KEYS = ["EngineID", "Cycle"]

RANDOM_SEED = 42

