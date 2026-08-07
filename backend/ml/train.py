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

from backend.ml.config import (
    FEATURE_COLUMNS, TARGET_COLUMNS, MODELS_DIR, RANDOM_SEED, BEST_TRANSPARENT_MODELS,
)
from backend.ml.data import load_train_data


def make_model(target: str, model_type: str = "poly_ridge"):
    """
    Constructs a 100% transparent, interpretable regression model pipeline.

    Supported transparent architectures:
    - "poly_ridge": Degree-2 Polynomial Features -> RobustScaler -> Ridge(alpha=1e-5)
    - "ridge": RobustScaler -> Ridge(alpha=1e-5)
    - "linear": RobustScaler -> LinearRegression()
    """
    if model_type == "poly_ridge":
        return make_pipeline(
            SimpleImputer(strategy="median"),
            PolynomialFeatures(degree=2, include_bias=False),
            RobustScaler(),
            Ridge(alpha=1e-5, random_state=RANDOM_SEED),
        )
    elif model_type == "ridge":
        return make_pipeline(
            SimpleImputer(strategy="median"),
            RobustScaler(),
            Ridge(alpha=1e-5, random_state=RANDOM_SEED),
        )
    elif model_type == "linear":
        return make_pipeline(
            SimpleImputer(strategy="median"),
            RobustScaler(),
            LinearRegression(),
        )
    else:
        raise ValueError(f"Unsupported model type '{model_type}'. Must be a transparent model.")





def cross_validate(X, y, target: str, model_type: str = "poly_ridge", n_splits: int = 5) -> dict:
    """
    5-fold cross-validation to evaluate model performance and measure residual standard deviation.
    """
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
    mae_scores, r2_scores, residuals = [], [], []

    for train_idx, val_idx in kf.split(X):
        model = make_model(target, model_type=model_type)
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
    Trains transparent models for all targets and saves them to trained_models/.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    train_df = load_train_data()
    feature_cols = list(FEATURE_COLUMNS)

    cv_results = {}

    for target in TARGET_COLUMNS:
        model_type = BEST_TRANSPARENT_MODELS.get(target, "poly_ridge")
        y = train_df[target].values
        X = train_df[feature_cols]

        print(f"Training transparent model for {target} ({model_type})...")
        cv_results[target] = cross_validate(X, y, target, model_type=model_type)

        # Fit final model on all 24,000 training rows
        final_model = make_model(target, model_type=model_type)
        final_model.fit(X, y)

        # Store cross-validated residual std and MAE on the fitted pipeline for uncertainty estimation
        final_model._residual_std = cv_results[target]["residual_std"]
        final_model._fallback_uncertainty = cv_results[target]["MAE_mean"]

        model_path = MODELS_DIR / f"{target}.joblib"
        joblib.dump(final_model, model_path)
        print(f"  -> saved to {model_path} (R2={cv_results[target]['R2_mean']:.4f}, MAE={cv_results[target]['MAE_mean']:.6f})")

    # Save feature columns definition
    with open(MODELS_DIR / "feature_columns.json", "w") as f:
        json.dump(feature_cols, f, indent=2)

    return cv_results


if __name__ == "__main__":
    print("=" * 60)
    print("AEROTHON 2026 - Training Transparent Health & Twin Models")
    print("Dataset: PS_2_final_dataset (24,000 train rows)")
    print("Model Type: Degree-2 Polynomial Ridge Regression (100% Interpretable)")
    print("=" * 60)

    scores = train_all_models()

    print("\nCross-Validation Results (5-Fold CV on Training Data):")
    for target, s in scores.items():
        print(f"  {target:18s} MAE={s['MAE_mean']:.6f}   R2={s['R2_mean']:.4f}")

    print("\nTraining complete. Models saved to trained_models/")

