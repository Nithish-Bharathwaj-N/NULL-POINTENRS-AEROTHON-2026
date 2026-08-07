"""Residual-style surrogate model."""

from __future__ import annotations

import pandas as pd
from sklearn.linear_model import LinearRegression


FEATURES = [
    "temperature_ratio",
    "fuel_air_ratio",
    "pressure_drop_ratio",
    "temperature_drop_ratio",
]


def fit_residual_model(
    df: pd.DataFrame,
    target_col: str,
) -> dict[str, float]:
    """
    Fit a linear residual model using physics-derived features.
    """

    required = FEATURES + [target_col]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    train = df[required].dropna()

    X = train[FEATURES]
    y = train[target_col]

    model = LinearRegression()
    model.fit(X, y)

    return {
        "intercept": float(model.intercept_),
        **{
            feature: float(coef)
            for feature, coef in zip(FEATURES, model.coef_)
        },
    }


def predict_with_residual_model(
    df: pd.DataFrame,
    params: dict[str, float],
    target_col: str | None = None,
) -> pd.Series:
    """
    Predict using the fitted residual model.
    """

    X = (
        df[FEATURES]
        .fillna(0.0)
        .astype(float)
    )

    prediction = params["intercept"]

    for feature in FEATURES:
        prediction += X[feature] * params[feature]

    return pd.Series(
        prediction,
        index=df.index,
        name=f"predicted_{target_col or 'target'}",
    )