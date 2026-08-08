"""
train.py
========
Training pipeline for transparent, fully interpretable ML models on PS_2_final_dataset.
Trains one Polynomial Ridge model per target and saves fitted pipelines to trained_models/.

Uses 5-fold cross-validation to estimate MAE, R2 score, and residual uncertainty.
"""

import json
import warnings

warnings.filterwarnings("ignore")

import joblib
import numpy as np
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.preprocessing import PolynomialFeatures, StandardScaler, RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error, r2_score

from sklearn.model_selection import GroupKFold
from backend.ml.config import (
    FEATURE_COLUMNS, TARGET_COLUMNS, MODELS_DIR, RANDOM_SEED, BEST_TRANSPARENT_MODELS,
    TARGET_FEATURE_COLUMNS, TARGET_ALPHA
)
from backend.ml.data import load_train_data


from backend.ml.features import engineer_features

def make_model(target: str, model_type: str = "poly_ridge", alpha: float = 1.0):
    """
    Constructs a transparent, highly accurate regression model pipeline.
    Uses degree-2 Polynomial Features -> RobustScaler -> Ridge(alpha=alpha).
    """
    if model_type == "poly_ridge":
        return make_pipeline(
            SimpleImputer(strategy="median"),
            PolynomialFeatures(degree=2, include_bias=False),
            RobustScaler(),
            Ridge(alpha=alpha, random_state=RANDOM_SEED),
        )
    elif model_type == "ridge":
        return make_pipeline(
            SimpleImputer(strategy="median"),
            RobustScaler(),
            Ridge(alpha=alpha, random_state=RANDOM_SEED),
        )
    elif model_type == "linear":
        return make_pipeline(
            SimpleImputer(strategy="median"),
            RobustScaler(),
            LinearRegression(),
        )
    else:
        raise ValueError(f"Unsupported model type '{model_type}'. Must be a transparent model.")


def cross_validate(X, y, groups, target: str, model_type: str = "poly_ridge", alpha: float = 1.0, n_splits: int = 5) -> dict:
    """
    Leak-free GroupKFold cross-validation by EngineID to evaluate model performance on unseen engines.
    """
    gkf = GroupKFold(n_splits=n_splits)
    mae_scores, r2_scores, residuals = [], [], []

    for train_idx, val_idx in gkf.split(X, y, groups):
        model = make_model(target, model_type=model_type, alpha=alpha)
        model.fit(X.iloc[train_idx], y[train_idx])
        preds = model.predict(X.iloc[val_idx])
        
        mae_scores.append(mean_absolute_error(y[val_idx], preds))
        r2_scores.append(r2_score(y[val_idx], preds))
        residuals.extend(y[val_idx] - preds)

    return {
        "MAE_mean": float(np.mean(mae_scores)),
        "R2_mean": float(np.mean(r2_scores)),
        "residual_std": float(np.std(residuals)),
    }


def train_all_models() -> dict:
    """
    Trains transparent models for all targets using enriched thermodynamic features and saves them to trained_models/.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    twin_models_dir = MODELS_DIR.parent / "backend" / "digital_twin" / "ml" / "trained_models"
    twin_models_dir.mkdir(parents=True, exist_ok=True)

    raw_df = load_train_data()
    train_df = engineer_features(raw_df)

    groups = train_df["EngineID"].values if "EngineID" in train_df.columns else np.arange(len(train_df))

    cv_results = {}
    saved_feature_cols = {}
    saved_alphas = {}

    for target in TARGET_COLUMNS:
        model_type = BEST_TRANSPARENT_MODELS.get(target, "poly_ridge")
        target_cols = [c for c in TARGET_FEATURE_COLUMNS.get(target, FEATURE_COLUMNS) if c in train_df.columns]
        alpha = TARGET_ALPHA.get(target, 1.0)

        saved_feature_cols[target] = target_cols
        saved_alphas[target] = alpha

        y = train_df[target].values
        X = train_df[target_cols]

        print(f"Training high-accuracy model for {target} ({model_type}, alpha={alpha}, features={len(target_cols)})...")
        cv_results[target] = cross_validate(X, y, groups, target, model_type=model_type, alpha=alpha)

        # Fit final model on all training rows
        final_model = make_model(target, model_type=model_type, alpha=alpha)
        final_model.fit(X, y)

        # Store cross-validated residual std and MAE on the fitted pipeline for uncertainty estimation
        final_model._residual_std = cv_results[target]["residual_std"]
        final_model._fallback_uncertainty = cv_results[target]["MAE_mean"]

        model_path = MODELS_DIR / f"{target}.joblib"
        joblib.dump(final_model, model_path)

        twin_model_path = twin_models_dir / f"{target}.joblib"
        joblib.dump(final_model, twin_model_path)

        print(f"  -> saved to {model_path} (Engine-Grouped R2={cv_results[target]['R2_mean']:.4f}, MAE={cv_results[target]['MAE_mean']:.6f})")

    # Save feature columns metadata definitions to both locations
    for target_dir in [MODELS_DIR, twin_models_dir]:
        with open(target_dir / "target_feature_columns.json", "w") as f:
            json.dump(saved_feature_cols, f, indent=2)

        with open(target_dir / "chosen_alpha.json", "w") as f:
            json.dump(saved_alphas, f, indent=2)

        with open(target_dir / "feature_columns.json", "w") as f:
            json.dump(FEATURE_COLUMNS, f, indent=2)

    return cv_results


if __name__ == "__main__":
    print("=" * 60)
    print("AEROTHON 2026 - Training High-Accuracy Aerospace Digital Twin Models")
    print("Dataset: PS_2_final_dataset (24,000 train rows)")
    print("Model Type: Enriched Aero-Thermal Degree-2 Polynomial Ridge")
    print("=" * 60)

    scores = train_all_models()

    print("\nCross-Validation Results (Engine GroupKFold CV):")
    for target, s in scores.items():
        print(f"  {target:18s} MAE={s['MAE_mean']:.6f}   R2={s['R2_mean']:.4f}")

    print("\nTraining complete. Models saved to trained_models/ and backend/digital_twin/ml/trained_models/")


