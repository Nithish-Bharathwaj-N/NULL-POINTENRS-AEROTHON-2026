"""
model_comparison.py
===================
Empirical comparison of transparent, fully interpretable model candidates on PS_2_final_dataset.
Compares Linear Regression, Ridge, Lasso, Polynomial Ridge (Degree 2), and Shallow Decision Trees across all 6 targets.
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error, r2_score

from backend.ml.config import FEATURE_COLUMNS, TARGET_COLUMNS, RANDOM_SEED
from backend.ml.data import load_train_data


def build_candidate_models() -> dict:
    """
    Returns candidate 100% white-box, interpretable regression models.
    """
    return {
        "Linear Regression": make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LinearRegression(),
        ),
        "Ridge (alpha=10)": make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            Ridge(alpha=10.0, random_state=RANDOM_SEED),
        ),
        "Lasso (alpha=0.01)": make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            Lasso(alpha=0.01, random_state=RANDOM_SEED),
        ),
        "Poly2 Ridge (alpha=10)": make_pipeline(
            SimpleImputer(strategy="median"),
            PolynomialFeatures(degree=2, include_bias=False),
            StandardScaler(),
            Ridge(alpha=10.0, random_state=RANDOM_SEED),
        ),
        "Poly2 Ridge (alpha=50)": make_pipeline(
            SimpleImputer(strategy="median"),
            PolynomialFeatures(degree=2, include_bias=False),
            StandardScaler(),
            Ridge(alpha=50.0, random_state=RANDOM_SEED),
        ),
        "Decision Tree (depth=3)": make_pipeline(
            SimpleImputer(strategy="median"),
            DecisionTreeRegressor(max_depth=3, random_state=RANDOM_SEED),
        ),
    }


def cross_validate_model(model, X, y, n_splits: int = 5) -> dict:
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
    mae_scores, r2_scores = [], []

    for train_idx, val_idx in kf.split(X):
        from sklearn.base import clone
        fold_model = clone(model)
        fold_model.fit(X.iloc[train_idx], y[train_idx])
        preds = fold_model.predict(X.iloc[val_idx])
        mae_scores.append(mean_absolute_error(y[val_idx], preds))
        r2_scores.append(r2_score(y[val_idx], preds))

    return {"MAE": float(np.mean(mae_scores)), "R2": float(np.mean(r2_scores))}


def run_comparison():
    train_df = load_train_data()
    X = train_df[FEATURE_COLUMNS]

    print(f"\nComparing Transparent Model Candidates across {len(TARGET_COLUMNS)} Targets")
    print(f"(5-fold cross-validation, {len(X)} training rows, {len(FEATURE_COLUMNS)} features)\n")

    results = {}
    for target in TARGET_COLUMNS:
        y = train_df[target].values
        print(f"=== {target} ===")
        results[target] = {}
        models = build_candidate_models()
        for name, model in models.items():
            scores = cross_validate_model(model, X, y)
            results[target][name] = scores
            print(f"  {name:25s} MAE={scores['MAE']:.6f}   R2={scores['R2']:.4f}")

        best_model = max(results[target], key=lambda m: results[target][m]["R2"])
        print(f"  --> BEST: {best_model} (R2={results[target][best_model]['R2']:.4f})\n")

    print("=" * 60)
    print("SUMMARY - Best Transparent Model Per Target:")
    for target in TARGET_COLUMNS:
        best_model = max(results[target], key=lambda m: results[target][m]["R2"])
        print(f"  {target:18s} -> {best_model}")

    return results


if __name__ == "__main__":
    run_comparison()

