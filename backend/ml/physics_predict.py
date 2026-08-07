"""Simple, live-callable entry point for Member 3's ML pipeline.

Usage
-----
from physics_predict import physics_predict

physics_df = physics_predict(sensor_dataframe)

This is a thin wrapper around
physics_engine.physics_api.augment_with_physics()
so Member 3 does not need to know about the internal
package layout.

Works on a single row or an entire dataframe.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Allow direct execution
sys.path.insert(0, str(Path(__file__).resolve().parent))

from physics_engine.physics_api import augment_with_physics  # noqa: E402


def physics_predict(
    df: pd.DataFrame,
    target_col: str | None = "T4_K",
) -> pd.DataFrame:
    """
    Augment a dataframe with physics-derived features,
    predictions and residuals.

    Parameters
    ----------
    df : pandas.DataFrame
        Turbojet sensor dataframe.

    target_col : str | None
        Target column for residual modelling.
        Default is "T4_K".

    Returns
    -------
    pandas.DataFrame
        Physics-enriched dataframe.
    """

    return augment_with_physics(
        df,
        target_col=target_col,
    )


if __name__ == "__main__":

    example = pd.DataFrame(
        {
            "EngineID": [1],

            # Cycle intentionally removed
            # per Aerothon Finals rules.

            "Altitude_m": [5000.0],
            "Mach": [0.50],

            "Tamb_K": [255.0],
            "Pamb_Pa": [54000.0],

            "RPM_rev_min": [45000.0],
            "FuelFlow_kg_s": [0.80],

            "P2_Pa": [150000.0],
            "T2_K": [330.0],

            "P3_Pa": [145000.0],
            "T3_K": [1000.0],

            "P4_Pa": [90000.0],
            "T4_K": [850.0],
        }
    )

    result = physics_predict(example)

    print(result.to_string(index=False))