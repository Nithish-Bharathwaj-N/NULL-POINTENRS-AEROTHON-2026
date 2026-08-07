"""
data.py
=======
Data loading and feature engineering pipeline combining PS_2_final_dataset and PS2_dataset.
Loads 48,000 training rows and 12,000 held-out test rows across 60,000 total engine cycles.
"""

import pandas as pd
from backend.ml.config import DATA_DIR, EXTRA_DATA_DIR, JOIN_KEYS
from backend.ml.features import engineer_features


def _available_dataset_dirs():
    seen = set()
    dirs = []
    for data_dir in [DATA_DIR, EXTRA_DATA_DIR]:
        train_path = data_dir / "train.csv"
        gt_path = data_dir / "ground_truth.csv"
        if not train_path.exists() or not gt_path.exists():
            continue
        signature = (train_path.resolve().stat().st_size, gt_path.resolve().stat().st_size)
        if signature in seen:
            continue
        seen.add(signature)
        dirs.append(data_dir)
    if not dirs:
        raise FileNotFoundError("No train.csv + ground_truth.csv dataset pair found.")
    return dirs


def load_ground_truth() -> pd.DataFrame:
    """Load true health, thrust, and TSFC labels for all engine cycles."""
    return pd.concat(
        [pd.read_csv(data_dir / "ground_truth.csv") for data_dir in _available_dataset_dirs()],
        ignore_index=True,
    )


def load_train_data() -> pd.DataFrame:
    """
    Load the 48,000 combined training rows from both dataset folders,
    apply feature engineering, and attach true labels.
    """
    frames = []
    for data_dir in _available_dataset_dirs():
        frames.append(
            engineer_features(pd.read_csv(data_dir / "train.csv")).merge(
                pd.read_csv(data_dir / "ground_truth.csv"), on=JOIN_KEYS
            )
        )
    return pd.concat(frames, ignore_index=True)


def load_test_data() -> pd.DataFrame:
    """
    Load the 12,000 combined held-out test rows from both dataset folders,
    apply feature engineering, and attach true labels.
    """
    frames = []
    for data_dir in _available_dataset_dirs():
        test_path = data_dir / "test.csv"
        if not test_path.exists():
            continue
        frames.append(
            engineer_features(pd.read_csv(test_path)).merge(
                pd.read_csv(data_dir / "ground_truth.csv"), on=JOIN_KEYS
            )
        )
    if not frames:
        raise FileNotFoundError("No test.csv + ground_truth.csv dataset pair found.")
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    train = load_train_data()
    test = load_test_data()
    print(f"Combined Train rows: {len(train)} | Combined Test rows: {len(test)}")
    print(f"Total columns: {len(train.columns)}")

