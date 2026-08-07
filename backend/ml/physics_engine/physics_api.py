"""High-level API exposing physics feature augmentation."""

from __future__ import annotations

import pandas as pd

from .feature_engineering import build_physics_features
from .residual_engine import (
    fit_residual_model,
    predict_with_residual_model,
)


def predict_physics(
    df: pd.DataFrame,
    target_col: str | None = None,
) -> pd.DataFrame:
    """
    Compute physics-derived features and optional residual-model prediction.
    """

    enriched = build_physics_features(df)

    if target_col is None:
        return enriched

    if target_col in enriched.columns:
        params = fit_residual_model(enriched, target_col)

        enriched[f"predicted_{target_col}"] = (
            predict_with_residual_model(
                enriched,
                params,
                target_col=target_col,
            ).astype(float)
        )

    return enriched


def augment_with_physics(
    df: pd.DataFrame,
    target_col: str | None = None,
) -> pd.DataFrame:
    """
    Add physics-derived features together with predictions and residuals.
    """

    enriched = predict_physics(
        df,
        target_col=target_col,
    )

    if target_col is None:
        return enriched

    pred_col = f"predicted_{target_col}"

    if (
        target_col in enriched.columns
        and pred_col in enriched.columns
    ):
        enriched[f"residual_{target_col}"] = (
            enriched[target_col].astype(float)
            - enriched[pred_col].astype(float)
        )

    return enriched