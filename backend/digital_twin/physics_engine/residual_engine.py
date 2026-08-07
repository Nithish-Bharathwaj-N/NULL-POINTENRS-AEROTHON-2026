"""Residual-style surrogate model built with SciPy and scikit-learn conventions."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sklearn.linear_model import LinearRegression


def fit_residual_model(df: pd.DataFrame, target_col: str) -> dict[str, float]:
    """Fit a linear surrogate using SciPy and scikit-learn-compatible features."""

    features = ["temperature_ratio", "fuel_air_ratio", "pressure_drop_ratio", "temperature_drop_ratio"]
    X = df[features].astype(float).to_numpy()
    y = df[target_col].astype(float).to_numpy()

    model = LinearRegression()
    model.fit(X, y)
    return {
        "intercept": float(model.intercept_),
        "temperature_ratio": float(model.coef_[0]),
        "fuel_air_ratio": float(model.coef_[1]),
        "pressure_drop_ratio": float(model.coef_[2]),
        "temperature_drop_ratio": float(model.coef_[3]),
    }


def predict_with_residual_model(df: pd.DataFrame, params: dict[str, float], target_col: str | None = None) -> pd.Series:
    """Predict the target using the fitted linear surrogate."""

    features = ["temperature_ratio", "fuel_air_ratio", "pressure_drop_ratio", "temperature_drop_ratio"]
    X = df[features].astype(float).to_numpy()
    base = params["intercept"]
    preds = base + X[:, 0] * params["temperature_ratio"] + X[:, 1] * params["fuel_air_ratio"] + X[:, 2] * params["pressure_drop_ratio"] + X[:, 3] * params["temperature_drop_ratio"]
    return pd.Series(preds, index=df.index, name=f"predicted_{target_col or 'target'}")
