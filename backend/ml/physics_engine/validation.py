"""Validation utilities for physics-based turbojet predictions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _ensure_numeric(values: Any) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1:
        raise ValueError("Measurements and predictions must be one-dimensional arrays.")
    return array


def _compute_error_metrics(
    measurements: np.ndarray,
    predictions: np.ndarray,
) -> dict[str, float]:

    mask = np.isfinite(measurements) & np.isfinite(predictions)

    measurements = measurements[mask]
    predictions = predictions[mask]

    residuals = measurements - predictions
    abs_errors = np.abs(residuals)

    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((measurements - np.mean(measurements)) ** 2))

    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0

    return {
        "rmse": float(np.sqrt(np.mean(residuals ** 2))),
        "mae": float(np.mean(abs_errors)),
        "r2": float(r2),
        "mean_residual": float(np.mean(residuals)),
        "std_residual": float(np.std(residuals)),
        "max_abs_error": float(np.max(abs_errors)),
        "median_abs_error": float(np.median(abs_errors)),
    }


def _physics_consistency_checks(
    physics_df: pd.DataFrame | None,
) -> dict[str, Any]:
    """
    Run basic sanity checks on physics-derived features.

    Missing values are ignored so incomplete datasets
    do not automatically fail validation.
    """

    if physics_df is None:
        return {
            "checks": {},
            "passed": 0,
            "total": 0,
        }

    checks: dict[str, bool] = {}

    if "pressure_ratio" in physics_df.columns:
        checks["pressure_ratio_gt_one"] = bool(
            physics_df["pressure_ratio"]
            .dropna()
            .gt(1.0)
            .all()
        )

    if "temperature_ratio" in physics_df.columns:
        checks["temperature_ratio_gt_one"] = bool(
            physics_df["temperature_ratio"]
            .dropna()
            .gt(1.0)
            .all()
        )

    if "compressor_efficiency" in physics_df.columns:
        checks["compressor_efficiency_in_range"] = bool(
            physics_df["compressor_efficiency"]
            .dropna()
            .between(0.0, 1.0)
            .all()
        )

    if "combustor_efficiency" in physics_df.columns:
        checks["combustor_efficiency_in_range"] = bool(
            physics_df["combustor_efficiency"]
            .dropna()
            .between(0.0, 1.0)
            .all()
        )

    if "turbine_efficiency" in physics_df.columns:
        checks["turbine_efficiency_in_range"] = bool(
            physics_df["turbine_efficiency"]
            .dropna()
            .between(0.0, 1.0)
            .all()
        )

    if "overall_efficiency" in physics_df.columns:
        checks["overall_efficiency_in_range"] = bool(
            physics_df["overall_efficiency"]
            .dropna()
            .between(0.0, 1.0)
            .all()
        )

    if not checks:
        return {
            "checks": {},
            "passed": 0,
            "total": 0,
        }

    passed = sum(checks.values())

    return {
        "checks": checks,
        "passed": int(passed),
        "total": len(checks),
    }
    
def _save_plot(fig: plt.Figure, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _plot_prediction_vs_measurement(measurements: np.ndarray, predictions: np.ndarray, output_path: Path) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    ax.scatter(measurements, predictions, color="#1f77b4", s=45, alpha=0.8, edgecolor="k", linewidth=0.4)
    min_val = min(np.min(measurements), np.min(predictions))
    max_val = max(np.max(measurements), np.max(predictions))
    ax.plot([min_val, max_val], [min_val, max_val], color="#d62728", linestyle="--", linewidth=1.2, label="Ideal 1:1")
    ax.set_xlabel("Measurement")
    ax.set_ylabel("Prediction")
    ax.set_title("Prediction vs Measurement")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    ax.set_aspect("equal", adjustable="box")
    _save_plot(fig, output_path)


def _plot_residual_distribution(residuals: np.ndarray, output_path: Path) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    ax.hist(residuals, bins=12, color="#2ca02c", edgecolor="black", alpha=0.85)
    ax.axvline(0.0, color="#d62728", linestyle="--", linewidth=1.2)
    ax.set_xlabel("Residual")
    ax.set_ylabel("Count")
    ax.set_title("Residual Distribution")
    ax.grid(True, alpha=0.3)
    _save_plot(fig, output_path)


def _plot_error_histogram(abs_errors: np.ndarray, output_path: Path) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    ax.hist(abs_errors, bins=12, color="#ff7f0e", edgecolor="black", alpha=0.85)
    ax.set_xlabel("Absolute Error")
    ax.set_ylabel("Count")
    ax.set_title("Absolute Error Histogram")
    ax.grid(True, alpha=0.3)
    _save_plot(fig, output_path)


def validate_predictions(
    measurements: Any,
    predictions: Any,
    output_dir: str | Path | None = None,
    report_name: str = "validation_report.md",
    metadata: dict[str, Any] | None = None,
    physics_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Validate predictions, save plots, and generate a markdown report."""

    measurement_array = _ensure_numeric(measurements)
    prediction_array = _ensure_numeric(predictions)

    if measurement_array.shape[0] != prediction_array.shape[0]:
        raise ValueError("Measurements and predictions must have the same length.")

    output_path = Path(output_dir) if output_dir is not None else Path("validation_outputs")
    output_path.mkdir(parents=True, exist_ok=True)

    metrics = _compute_error_metrics(measurement_array, prediction_array)
    residuals = measurement_array - prediction_array
    abs_errors = np.abs(residuals)

    plot_paths = {
        "predicted_vs_measurement": output_path / "predicted_vs_measurement.png",
        "residual_distribution": output_path / "residual_distribution.png",
        "error_histogram": output_path / "error_histogram.png",
    }

    _plot_prediction_vs_measurement(measurement_array, prediction_array, plot_paths["predicted_vs_measurement"])
    _plot_residual_distribution(residuals, plot_paths["residual_distribution"])
    _plot_error_histogram(abs_errors, plot_paths["error_histogram"])

    physics_checks = _physics_consistency_checks(physics_df)
    summary = {
        "measurement_mean": float(np.mean(measurement_array)),
        "measurement_std": float(np.std(measurement_array, ddof=0)),
        "prediction_mean": float(np.mean(prediction_array)),
        "prediction_std": float(np.std(prediction_array, ddof=0)),
        "residual_mean": metrics["mean_residual"],
        "residual_std": metrics["std_residual"],
    }

    report_path = output_path / report_name
    report_path.write_text(
        _build_report(markdown_title="Validation Report", metrics=metrics, summary=summary, physics_checks=physics_checks, metadata=metadata, plot_paths=plot_paths),
        encoding="utf-8",
    )

    return {
        **metrics,
        "summary_statistics": summary,
        "physics_consistency_checks": physics_checks,
        "plot_paths": {path.name: str(path) for path in plot_paths.values()},
        "report_path": str(report_path),
    }


def _build_report(
    markdown_title: str,
    metrics: dict[str, float],
    summary: dict[str, float],
    physics_checks: dict[str, Any],
    metadata: dict[str, Any] | None,
    plot_paths: dict[str, Path],
) -> str:
    metadata_block = ""
    if metadata:
        metadata_block = "\n".join(f"- {key}: {value}" for key, value in metadata.items())
        metadata_block = f"## Metadata\n{metadata_block}\n"

    checks_block = ""
    if physics_checks["checks"]:
        checks_lines = [f"- {name}: {'pass' if value else 'fail'}" for name, value in physics_checks["checks"].items()]
        checks_block = "## Physics consistency checks\n" + "\n".join(checks_lines) + "\n"

    return f"""# {markdown_title}

## Overview
This report summarizes the agreement between measured and predicted values for the physics-based turbojet model.

## Metrics
- RMSE: {metrics['rmse']:.3f}
- MAE: {metrics['mae']:.3f}
- R²: {metrics['r2']:.3f}
- Mean residual: {metrics['mean_residual']:.3f}
- Std residual: {metrics['std_residual']:.3f}
- Max absolute error: {metrics['max_abs_error']:.3f}
- Median absolute error: {metrics['median_abs_error']:.3f}

## Summary statistics
- Measurement mean: {summary['measurement_mean']:.3f}
- Measurement std: {summary['measurement_std']:.3f}
- Prediction mean: {summary['prediction_mean']:.3f}
- Prediction std: {summary['prediction_std']:.3f}
- Residual mean: {summary['residual_mean']:.3f}
- Residual std: {summary['residual_std']:.3f}

{metadata_block}## Figures
- Prediction vs measurement: [{plot_paths['predicted_vs_measurement'].name}]({plot_paths['predicted_vs_measurement'].name})
- Residual distribution: [{plot_paths['residual_distribution'].name}]({plot_paths['residual_distribution'].name})
- Error histogram: [{plot_paths['error_histogram'].name}]({plot_paths['error_histogram'].name})

{checks_block}## Interpretation
The model quality should be judged together with the residual diagnostics and the physics-based consistency checks above.
"""
