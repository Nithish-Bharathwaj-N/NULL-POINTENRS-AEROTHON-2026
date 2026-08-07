"""
evaluate.py
===========
Evaluation script for trained transparent Polynomial Ridge models on held-out PS_2_final_dataset test set (6,000 rows).

Generates:
- results/predictions_on_test.csv
- results/feature_importance.png
- results/predicted_vs_actual.png
- results/summary_report.txt
"""

import warnings

warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.inspection import permutation_importance

from backend.ml.config import TARGET_COLUMNS, RESULTS_DIR, MODELS_DIR
from backend.ml.data import load_test_data
from backend.ml.predict import HealthPredictor


def evaluate() -> dict:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    predictor = HealthPredictor.load(MODELS_DIR)
    test_df = load_test_data()

    scored = predictor.predict_batch(test_df)
    scored.to_csv(RESULTS_DIR / "predictions_on_test.csv", index=False)

    scores = {}
    for target in TARGET_COLUMNS:
        y_true = test_df[target].values
        y_pred = scored[f"{target}_predicted"].values
        scores[target] = {
            "MAE": float(mean_absolute_error(y_true, y_pred)),
            "R2": float(r2_score(y_true, y_pred)),
        }

    _plot_feature_importance(predictor, test_df, RESULTS_DIR)
    _plot_predicted_vs_actual(test_df, scored, scores, RESULTS_DIR)
    _write_report(scores, RESULTS_DIR)

    return scores


def _plot_feature_importance(predictor: HealthPredictor, test_df, output_dir):
    """Plot top feature importances using permutation importance across test set."""
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    axes = axes.flatten()

    for i, target in enumerate(TARGET_COLUMNS):
        feature_columns = predictor._feature_columns_for_target(target)
        X_test = test_df[feature_columns]
        y_test = test_df[target].values
        
        # Subsample test set for faster permutation importance plotting
        sample_idx = np.random.choice(len(X_test), min(1000, len(X_test)), replace=False)
        result = permutation_importance(
            predictor.models[target], X_test.iloc[sample_idx], y_test[sample_idx],
            n_repeats=5, random_state=42, n_jobs=-1,
        )
        importances = result.importances_mean
        order = np.argsort(importances)[::-1][:10]

        ax = axes[i]
        ax.barh(
            [feature_columns[j] for j in order][::-1],
            [importances[j] for j in order][::-1],
            color="#2E5266",
        )
        ax.set_title(target)
        ax.set_xlabel("Importance")

    plt.tight_layout()
    plt.savefig(output_dir / "feature_importance.png", dpi=150)
    plt.close()


def _plot_predicted_vs_actual(test_df, scored, scores, output_dir):
    """Plot actual vs predicted scatter plots for all 6 targets."""
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    axes = axes.flatten()

    for i, target in enumerate(TARGET_COLUMNS):
        y_true = test_df[target].values
        y_pred = scored[f"{target}_predicted"].values

        # Subsample points for clean plot display
        idx = np.random.choice(len(y_true), min(1000, len(y_true)), replace=False)
        
        ax = axes[i]
        ax.scatter(y_true[idx], y_pred[idx], alpha=0.3, color="#C1440E", s=12)
        lims = [min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())]
        ax.plot(lims, lims, "k--", linewidth=1, label="Ideal fit")
        ax.set_xlabel("Actual")
        ax.set_ylabel("Predicted")
        ax.set_title(f"{target} (R2={scores[target]['R2']:.4f})")
        ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(output_dir / "predicted_vs_actual.png", dpi=150)
    plt.close()


def _write_report(scores: dict, output_dir):
    lines = [
        "AEROTHON 2026 - Held-Out Test Set Performance Report",
        "Dataset: PS_2_final_dataset/test.csv (6,000 test rows)",
        "Model Type: Transparent Polynomial Ridge Regression",
        "=" * 60,
        "",
    ]
    for target, s in scores.items():
        lines.append(f"  {target:18s} MAE={s['MAE']:.6f}   R2={s['R2']:.4f}")
    
    with open(output_dir / "summary_report.txt", "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    print("Evaluating transparent models on held-out PS_2_final_dataset/test.csv...\n")
    scores = evaluate()
    for target, s in scores.items():
        print(f"  {target:18s} MAE={s['MAE']:.6f}   R2={s['R2']:.4f}")
    print(f"\nEvaluation artifacts generated in {RESULTS_DIR}/")

