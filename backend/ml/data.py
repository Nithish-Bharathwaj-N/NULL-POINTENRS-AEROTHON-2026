"""
data.py
=======
Data loading and feature engineering pipeline combining PS_2_final_dataset and PS2_dataset.
Loads 48,000 training rows and 12,000 held-out test rows across 60,000 total engine cycles.
"""

import pandas as pd
from backend.ml.config import (
    DATA_DIR, EXTRA_DATA_DIR, JOIN_KEYS,
)
from backend.ml.features import engineer_features


def load_ground_truth() -> pd.DataFrame:
    """Load true health, thrust, and TSFC labels for all engine cycles."""
    gt1 = pd.read_csv(DATA_DIR / "ground_truth.csv")
    gt2 = pd.read_csv(EXTRA_DATA_DIR / "ground_truth.csv")
    return pd.concat([gt1, gt2], ignore_index=True)


def load_train_data() -> pd.DataFrame:
    """
    Load the 48,000 combined training rows from both dataset folders,
    apply feature engineering, and attach true labels.
    """
    s1 = engineer_features(pd.read_csv(DATA_DIR / "train.csv")).merge(
        pd.read_csv(DATA_DIR / "ground_truth.csv"), on=JOIN_KEYS
    )
    s2 = engineer_features(pd.read_csv(EXTRA_DATA_DIR / "train.csv")).merge(
        pd.read_csv(EXTRA_DATA_DIR / "ground_truth.csv"), on=JOIN_KEYS
    )
    return pd.concat([s1, s2], ignore_index=True)


def load_test_data() -> pd.DataFrame:
    """
    Load the 12,000 combined held-out test rows from both dataset folders,
    apply feature engineering, and attach true labels.
    """
    s1 = engineer_features(pd.read_csv(DATA_DIR / "test.csv")).merge(
        pd.read_csv(DATA_DIR / "ground_truth.csv"), on=JOIN_KEYS
    )
    s2 = engineer_features(pd.read_csv(EXTRA_DATA_DIR / "test.csv")).merge(
        pd.read_csv(EXTRA_DATA_DIR / "ground_truth.csv"), on=JOIN_KEYS
    )
    return pd.concat([s1, s2], ignore_index=True)


if __name__ == "__main__":
    train = load_train_data()
    test = load_test_data()
    print(f"Combined Train rows: {len(train)} | Combined Test rows: {len(test)}")
    print(f"Total columns: {len(train.columns)}")


