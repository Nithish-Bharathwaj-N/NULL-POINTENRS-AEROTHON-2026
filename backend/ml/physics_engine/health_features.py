"""Physics-derived component health indicators.

Health is expressed as a percentage of a data-driven nominal (as-new)
efficiency baseline, not against a hardcoded constant.

Baseline = 95th percentile of fleet efficiency.

Health = clip(efficiency / baseline * 100, 0, 100)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .efficiency_features import build_efficiency_features

_BASELINE_PERCENTILE = 95.0


def _health_from_efficiency(
    efficiency: pd.Series,
) -> tuple[pd.Series, float]:
    """
    Convert efficiency into health percentage using a fleet-wide baseline.
    """

    valid = efficiency.dropna()

    if len(valid) == 0:
        return pd.Series(np.nan, index=efficiency.index), float("nan")

    baseline = float(np.percentile(valid, _BASELINE_PERCENTILE))

    if not np.isfinite(baseline) or baseline <= 0:
        return pd.Series(np.nan, index=efficiency.index), baseline

    health = (
        efficiency.astype(float) / baseline * 100.0
    ).clip(lower=0.0, upper=100.0)

    return health, baseline


def build_health_features(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """
    Build component health features.

    Returns
    -------
    health_df
        Physics-derived health percentages.

    baselines
        Dictionary containing efficiency baselines.
    """

    efficiency = build_efficiency_features(df)

    compressor_health, compressor_baseline = _health_from_efficiency(
        efficiency["compressor_efficiency"]
    )

    combustor_health, combustor_baseline = _health_from_efficiency(
        efficiency["combustor_efficiency"]
    )

    turbine_health, turbine_baseline = _health_from_efficiency(
        efficiency["turbine_efficiency"]
    )

    out = pd.DataFrame(index=efficiency.index)

    # Keep EngineID only for traceability
    if "EngineID" in efficiency.columns:
        out["EngineID"] = efficiency["EngineID"]

    # IMPORTANT:
    # Cycle is intentionally omitted as per Aerothon Finals instructions.

    out["CompressorHealth_pct"] = compressor_health
    out["CombustorHealth_pct"] = combustor_health
    out["TurbineHealth_pct"] = turbine_health

    out["OverallHealth_pct"] = out[
        [
            "CompressorHealth_pct",
            "CombustorHealth_pct",
            "TurbineHealth_pct",
        ]
    ].mean(axis=1, skipna=True)

    baselines = {
        "compressor_efficiency_baseline": compressor_baseline,
        "combustor_efficiency_baseline": combustor_baseline,
        "turbine_efficiency_baseline": turbine_baseline,
        "baseline_percentile": _BASELINE_PERCENTILE,
    }

    return out, baselines