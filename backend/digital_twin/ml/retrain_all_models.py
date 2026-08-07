"""
retrain_all_models.py
=====================
Full Training Pipeline for Aerothon 2026 Hybrid Prognostics Platform.

Orchestrates:
  1. Load 30,000-row dataset (100 engines × 300 cycles)
  2. AerospaceDatasetPipeline.process_dataset() — sensor validation + physics normalization
  3. TemporalFeatureEngineer.fit_transform() — NO Cycle column
  4. HybridPrognosticsModel.train() — physics + interpretable ML ensemble
  5. RULPredictor.train() — sensor-based RUL estimation
  6. FleetAnalytics.fit() — cross-engine intelligence
  7. Evaluate with GroupKFold (development) and report LOEO metrics (final)
  8. Save all artifacts

Usage:
  python backend/digital_twin/ml/retrain_all_models.py
  python backend/digital_twin/ml/retrain_all_models.py --loeo  (slow, ~100x training)
"""

import os
import sys
import time
import argparse
import warnings
import json
import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# Path setup
HERE = os.path.dirname(os.path.abspath(__file__))
TWIN_DIR = os.path.dirname(HERE)
sys.path.insert(0, TWIN_DIR)

DATA_DIR   = os.path.join(TWIN_DIR, "data")
MODELS_DIR = os.path.join(HERE, "trained_models")

COMPLETE_CSV = os.path.join(DATA_DIR, "turbojet_complete_dataset.csv")
TRAIN_CSV    = os.path.join(DATA_DIR, "train.csv")
TEST_CSV     = os.path.join(DATA_DIR, "test.csv")
GT_CSV       = os.path.join(DATA_DIR, "ground_truth.csv")

TARGET_COLS = [
    "CompressorHealth", "CombustorHealth", "TurbineHealth",
    "OverallHealth", "Thrust_N", "TSFC_g_N_s"
]

HEALTH_TARGETS = ["CompressorHealth", "CombustorHealth", "TurbineHealth", "OverallHealth"]


def banner(text: str):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def load_data() -> pd.DataFrame:
    """Load the complete 100-engine × 300-cycle dataset."""
    banner("STEP 1: Loading Dataset")
    if not os.path.exists(COMPLETE_CSV):
        raise FileNotFoundError(f"Dataset not found: {COMPLETE_CSV}")

    df = pd.read_csv(COMPLETE_CSV)
    print(f"  Loaded: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"  Engines:      {df['EngineID'].nunique()}")
    print(f"  Cycles range: {df['Cycle'].min()} – {df['Cycle'].max()}")
    print(f"  Health range: OverallHealth {df['OverallHealth'].min():.4f} – {df['OverallHealth'].max():.4f}")
    return df


def run_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """Run AerospaceDatasetPipeline for sensor validation and physics normalization."""
    banner("STEP 2: Aerospace Dataset Pipeline")
    from data_pipeline import AerospaceDatasetPipeline
    processed = AerospaceDatasetPipeline.process_dataset(df)
    new_cols = [c for c in processed.columns if c not in df.columns]
    print(f"  Input shape:  {df.shape}")
    print(f"  Output shape: {processed.shape}")
    print(f"  New columns:  {new_cols}")
    return processed


def run_temporal_features(df: pd.DataFrame) -> tuple:
    """
    Fit and apply temporal feature engineering.
    CRITICAL: Cycle column is NEVER passed to or used by the feature engineer.
    """
    banner("STEP 3: Temporal Feature Engineering (Cycle-free)")
    from ml.temporal_features import TemporalFeatureEngineer

    # Verify Cycle is excluded
    assert "Cycle" not in [c for c in df.columns if c == "Cycle_feature"], \
        "Cycle must never appear as a model feature"

    engineer = TemporalFeatureEngineer()
    print("  Fitting TemporalFeatureEngineer on complete dataset...")
    t0 = time.time()
    df_temporal = engineer.fit_transform(df)
    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s. Output shape: {df_temporal.shape}")

    # Drop Cycle column from feature set (keep only for grouping/ordering)
    feature_names = engineer.get_feature_names()
    feature_names = [f for f in feature_names if f not in ["Cycle", "EngineID"]]
    print(f"  Total temporal features: {len(feature_names)}")

    # Save engineer
    eng_path = os.path.join(MODELS_DIR, "temporal_feature_engineer.joblib")
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(engineer, eng_path)
    print(f"  Saved TemporalFeatureEngineer → {eng_path}")

    return df_temporal, engineer, feature_names


def train_hybrid_model(df_temporal: pd.DataFrame, feature_names: list, run_loeo: bool = False):
    """Train the 3-layer bidirectional hybrid model."""
    banner("STEP 4: Hybrid Model Training")
    from ml.hybrid_model import HybridPrognosticsModel

    model = HybridPrognosticsModel()

    # Prepare feature matrix (no Cycle, no EngineID in X)
    available_features = [f for f in feature_names if f in df_temporal.columns]
    print(f"  Using {len(available_features)} features (Cycle excluded)")

    X = df_temporal[available_features].fillna(0.0)
    groups = df_temporal["EngineID"].astype(str) if "EngineID" in df_temporal.columns else None

    # Physics predictions (Layer 1)
    print("  Layer 1: Computing physics predictions...")
    phys_preds = model.physics_predict(df_temporal)

    # Residuals (ground truth - physics)
    y_residuals = {}
    for target in TARGET_COLS:
        if target in df_temporal.columns and target in phys_preds.columns:
            y_residuals[target] = df_temporal[target] - phys_preds[target]
        elif target in df_temporal.columns:
            y_residuals[target] = df_temporal[target]

    y_res_df = pd.DataFrame(y_residuals)

    # Interpretable ML ensemble (Layer 2)
    print("  Layer 2: Training interpretable ML ensemble (Ridge + ElasticNet + GBM≤5)...")
    print("  Validation: GroupKFold(n_splits=10, groups=EngineID)")
    t0 = time.time()
    cv_scores = model.train_ensemble(X, y_res_df, groups=groups)
    elapsed = time.time() - t0
    print(f"  Training completed in {elapsed:.1f}s")

    # Print CV results
    print("\n  GroupKFold CV Metrics:")
    for target, scores in cv_scores.items():
        print(f"    {target:22s} — MAE: {scores.get('mae',0):.5f}  RMSE: {scores.get('rmse',0):.5f}  R²: {scores.get('r2',0):.4f}")

    # Save feature columns
    feat_path = os.path.join(MODELS_DIR, "feature_columns.json")
    with open(feat_path, "w") as f:
        json.dump(available_features, f)
    print(f"\n  Saved feature_columns.json ({len(available_features)} features)")

    # Save hybrid model
    model_path = os.path.join(MODELS_DIR, "hybrid_model.joblib")
    model.save(model_path)
    print(f"  Saved HybridPrognosticsModel → {model_path}")

    # LOEO evaluation (optional, slow)
    if run_loeo:
        banner("STEP 4b: Leave-One-Engine-Out Evaluation (100 iterations)")
        print("  This may take 20–60 minutes. Running...")
        model.evaluate_loeo(df_temporal, feature_names)

    return model


def train_rul_predictor(df_temporal: pd.DataFrame):
    """Train the Remaining Useful Life predictor."""
    banner("STEP 5: RUL Predictor Training")
    try:
        from ml.rul_predictor import RULPredictor
        predictor = RULPredictor()

        if "OverallHealth" not in df_temporal.columns:
            print("  WARNING: OverallHealth not in dataset — skipping RUL training")
            return None

        print("  Computing RUL targets from health trajectories...")
        df_with_rul = predictor.compute_rul_targets(df_temporal)
        n_valid = df_with_rul["RUL"].notna().sum()
        print(f"  Valid RUL targets: {n_valid} / {len(df_with_rul)}")

        print("  Training ElasticNet + QuantileGBM on sensor features (no Cycle)...")
        t0 = time.time()
        predictor.train(df_with_rul)
        elapsed = time.time() - t0
        print(f"  RUL training completed in {elapsed:.1f}s")

        rul_path = os.path.join(MODELS_DIR, "rul_predictor.joblib")
        predictor.save(rul_path)
        print(f"  Saved RULPredictor → {rul_path}")
        return predictor
    except Exception as e:
        print(f"  RUL training warning: {e}. Skipping.")
        return None


def fit_fleet_analytics(df: pd.DataFrame):
    """Fit fleet-level intelligence on the complete dataset."""
    banner("STEP 6: Fleet Analytics Fitting")
    try:
        from ml.fleet_analytics import FleetAnalytics
        fleet = FleetAnalytics()
        t0 = time.time()
        fleet.fit(df)
        elapsed = time.time() - t0
        print(f"  Fleet analytics fitted in {elapsed:.1f}s")
        print(f"  Engines clustered: {len(fleet._engine_clusters)}")
        print(f"  Root causes classified: {len(fleet._engine_root_causes)}")

        # Print cluster distribution
        from collections import Counter
        from ml.fleet_analytics import CLUSTER_ARCHETYPES
        cluster_counts = Counter(fleet._engine_clusters.values())
        print("\n  Engine Cluster Distribution:")
        for idx, count in sorted(cluster_counts.items()):
            print(f"    {CLUSTER_ARCHETYPES.get(idx,'?'):20s}: {count} engines")

        # Print top degradation orderings
        deg_order = fleet.get_sensor_degradation_ordering()
        print("\n  Sensor Degradation Ordering (by % engines showing decline):")
        for item in deg_order[:5]:
            print(f"    {item['sensor']:20s}: {item['pct_engines_degrading']:.0f}% of engines, "
                  f"consistency={item['fleet_consistency']:.3f}")

        fleet_path = os.path.join(MODELS_DIR, "fleet_analytics.joblib")
        joblib.dump(fleet, fleet_path)
        print(f"\n  Saved FleetAnalytics → {fleet_path}")
        return fleet
    except Exception as e:
        print(f"  Fleet analytics warning: {e}. Skipping.")
        return None


def evaluate_on_test(df_temporal: pd.DataFrame, feature_names: list, model):
    """Evaluate hybrid model on test split (test.csv vs ground_truth.csv)."""
    banner("STEP 7: Evaluation on Test Split")
    try:
        if not os.path.exists(TEST_CSV) or not os.path.exists(GT_CSV):
            print("  Test/ground_truth CSV not found — skipping test evaluation")
            return

        from ml.temporal_features import TemporalFeatureEngineer
        from sklearn.metrics import mean_absolute_error, r2_score

        # Load test sensors + add health from full dataset for temporal features
        df_test = pd.read_csv(TEST_CSV)
        df_gt   = pd.read_csv(GT_CSV)

        # Merge for temporal features (test engines need their history)
        complete_df = pd.read_csv(COMPLETE_CSV)
        eng_path = os.path.join(MODELS_DIR, "temporal_feature_engineer.joblib")
        if os.path.exists(eng_path):
            engineer = joblib.load(eng_path)
            test_temporal = engineer.transform(df_test.merge(
                complete_df[["EngineID","Cycle"] + [c for c in complete_df.columns if c not in df_test.columns]],
                on=["EngineID","Cycle"], how="left"
            ))
        else:
            test_temporal = df_test.copy()

        available = [f for f in feature_names if f in test_temporal.columns]
        X_test = test_temporal[available].fillna(0.0)

        # Predict
        test_preds = model.predict(X_test, telemetry=test_temporal)

        # Ground truth
        df_gt_sorted = df_gt.set_index(["EngineID","Cycle"])
        df_test_keys = df_test[["EngineID","Cycle"]].copy()

        print("\n  Test Set Metrics (Hybrid Model):")
        for target in TARGET_COLS:
            if target not in df_gt.columns:
                continue
            if target not in test_preds:
                continue
            y_pred = np.array(test_preds[target])
            y_true = df_gt[target].values[:len(y_pred)]
            if len(y_true) != len(y_pred):
                continue
            mae  = mean_absolute_error(y_true, y_pred)
            r2   = r2_score(y_true, y_pred)
            print(f"    {target:22s} — MAE: {mae:.5f}  R²: {r2:.4f}")

    except Exception as e:
        print(f"  Test evaluation warning: {e}")


def print_summary(elapsed_total: float):
    banner("TRAINING COMPLETE — Summary")
    print(f"  Total training time: {elapsed_total:.1f}s ({elapsed_total/60:.1f} minutes)")
    print()
    print("  Files saved to trained_models/:")
    for fname in os.listdir(MODELS_DIR):
        fpath = os.path.join(MODELS_DIR, fname)
        size_mb = os.path.getsize(fpath) / 1024 / 1024
        print(f"    {fname:45s} {size_mb:.2f} MB")
    print()
    print("  System ready. Start backend server to serve predictions.")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aerothon 2026 Full Training Pipeline")
    parser.add_argument("--loeo", action="store_true",
                        help="Run Leave-One-Engine-Out evaluation (slow, ~100x training)")
    parser.add_argument("--skip-fleet", action="store_true",
                        help="Skip fleet analytics fitting (faster iteration)")
    parser.add_argument("--skip-rul", action="store_true",
                        help="Skip RUL predictor training")
    args = parser.parse_args()

    t_total = time.time()

    # Run pipeline
    raw_df        = load_data()
    processed_df  = run_pipeline(raw_df)
    df_temporal, engineer, feature_names = run_temporal_features(processed_df)
    hybrid_model  = train_hybrid_model(df_temporal, feature_names, run_loeo=args.loeo)

    if not args.skip_rul:
        rul_predictor = train_rul_predictor(df_temporal)

    if not args.skip_fleet:
        fleet = fit_fleet_analytics(raw_df)

    evaluate_on_test(df_temporal, feature_names, hybrid_model)
    print_summary(time.time() - t_total)
