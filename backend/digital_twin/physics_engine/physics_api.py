"""High-level API that exposes physics augmentation for dataset rows."""

from __future__ import annotations

import pandas as pd

from .feature_engineering import build_physics_features
from .residual_engine import fit_residual_model, predict_with_residual_model


def _physics_based_prediction(enriched: pd.DataFrame, target_col: str) -> pd.Series:
    """Create a simple thermodynamic proxy prediction for T4."""

    if target_col != "T4_K":
        return pd.Series([float("nan")] * len(enriched), index=enriched.index, name=f"predicted_{target_col}")

    base_temp = enriched["atm_temperature_k"].astype(float)
    compressor_work = enriched["compressor_work"].astype(float)
    combustor_heat = enriched["combustor_heat_release"].astype(float)
    fuel_air_ratio = enriched["fuel_air_ratio"].astype(float)
    predicted = base_temp + 0.25 * combustor_heat + 0.12 * compressor_work + 18.0 * fuel_air_ratio
    return pd.Series(predicted, index=enriched.index, name="predicted_T4_K")


def _compute_supported_physics_predictions(enriched: pd.DataFrame) -> pd.DataFrame:
    """Compute supported physics-based predicted values for each row."""

    index = enriched.index
    atm_temp = enriched["atm_temperature_k"].astype(float)
    atm_press = enriched["atm_pressure_pa"].astype(float)
    pressure_ratio = enriched["pressure_ratio"].astype(float)
    compressor_work = enriched["compressor_work"].astype(float)
    combustor_heat = enriched["combustor_heat_release"].astype(float)
    fuel_air_ratio = enriched["fuel_air_ratio"].astype(float)
    mach = enriched["Mach"].astype(float) if "Mach" in enriched.columns else pd.Series([0.0] * len(enriched), index=index)
    fuelflow = enriched["FuelFlow_kg_s"].astype(float) if "FuelFlow_kg_s" in enriched.columns else pd.Series([0.0] * len(enriched), index=index)

    predicted = pd.DataFrame(index=index)
    predicted["predicted_T4_K"] = _physics_based_prediction(enriched, "T4_K")
    predicted["predicted_P2_Pa"] = atm_press * pressure_ratio
    predicted["predicted_T2_K"] = atm_temp + 0.5 * compressor_work
    predicted["predicted_P3_Pa"] = enriched["P2_Pa"].astype(float) * pressure_ratio if "P2_Pa" in enriched.columns else pd.Series([float("nan")] * len(enriched), index=index)
    predicted["predicted_T3_K"] = atm_temp + combustor_heat / 1000.0
    predicted["predicted_RPM_rev_min"] = 1000.0 + 50.0 * mach
    predicted["predicted_FuelFlow_kg_s"] = 0.5 * fuel_air_ratio
    predicted["predicted_Thrust_N"] = 1000.0 * (fuelflow + 0.5 * mach + 1.0)
    if "TSFC_g_N_s" in enriched.columns:
        predicted["predicted_TSFC_g_N_s"] = predicted["predicted_FuelFlow_kg_s"] / predicted["predicted_Thrust_N"].replace(0.0, float("nan")) * 1000.0
    return predicted


def augment_with_physics(df: pd.DataFrame, target_col: str | None = None) -> pd.DataFrame:
    """Augment a dataframe with engineered physics features and meaningful predictions."""

    enriched = build_physics_features(df)
    if target_col is None:
        target_col = "T4_K"

    predictions = _compute_supported_physics_predictions(enriched)
    enriched = pd.concat([enriched, predictions], axis=1)

    if target_col in enriched.columns and target_col != "T4_K":
        params = fit_residual_model(enriched, target_col)
        preds = predict_with_residual_model(enriched, params, target_col=target_col)
        enriched[f"predicted_{target_col}"] = preds.astype(float)

    if "T4_K" not in enriched.columns and "Turbine_Exit_Temperature_T4" in enriched.columns:
        enriched["T4_K"] = enriched["Turbine_Exit_Temperature_T4"].apply(lambda t: t + 273.15 if t < 150 else t)

    if target_col in enriched.columns and f"predicted_{target_col}" in enriched.columns:
        enriched[f"residual_{target_col}"] = enriched[target_col] - enriched[f"predicted_{target_col}"]
    else:
        enriched[f"residual_{target_col}"] = 0.0

    for pred_col in predictions.columns:
        actual_col = pred_col.replace("predicted_", "")
        residual_col = f"residual_{actual_col}"
        if actual_col in enriched.columns and pred_col in enriched.columns:
            enriched[residual_col] = enriched[actual_col].astype(float) - enriched[pred_col].astype(float)

    physics_features = {
        "pressure_ratio": enriched["pressure_ratio"].to_list(),
        "temperature_ratio": enriched["temperature_ratio"].to_list(),
        "compressor_efficiency": enriched["compressor_efficiency"].to_list(),
        "combustor_efficiency": enriched["combustor_efficiency"].to_list(),
        "turbine_efficiency": enriched["turbine_efficiency"].to_list(),
        "compressor_work": enriched["compressor_work"].to_list(),
        "turbine_work": enriched["turbine_work"].to_list(),
        "thermal_efficiency": enriched["thermal_efficiency"].to_list(),
        "thrust": enriched["thrust"].to_list(),
        "tsfc": enriched["tsfc"].to_list(),
    }

    residual_features = {
        "P2_residual": (enriched["P2_Pa"] - (enriched["atm_pressure_pa"] * enriched["pressure_ratio"])).to_list() if "P2_Pa" in enriched.columns else [],
        "T2_residual": (enriched["T2_K"] - (enriched["atm_temperature_k"] + 0.5 * enriched["compressor_work"])).to_list() if "T2_K" in enriched.columns else [],
        "P3_residual": (enriched["P3_Pa"] - (enriched["P2_Pa"] * enriched["pressure_ratio"])).to_list() if "P3_Pa" in enriched.columns else [],
        "T3_residual": (enriched["T3_K"] - (enriched["atm_temperature_k"] + enriched["combustor_heat_release"] / 1000.0)).to_list() if "T3_K" in enriched.columns and "combustor_heat_release" in enriched.columns else [],
        "RPM_residual": (enriched["RPM_rev_min"] - (1000.0 + 50.0 * enriched["Mach"])).to_list() if "RPM_rev_min" in enriched.columns and "Mach" in enriched.columns else [],
        "Fuel_residual": (enriched["FuelFlow_kg_s"] - (0.5 * enriched["fuel_air_ratio"])).to_list() if "FuelFlow_kg_s" in enriched.columns and "fuel_air_ratio" in enriched.columns else [],
        "Thrust_residual": (enriched["thrust"] - (1000.0 * (enriched["FuelFlow_kg_s"] + 0.5 * enriched["Mach"] + 1.0))).to_list() if "FuelFlow_kg_s" in enriched.columns and "Mach" in enriched.columns else [],
    }

    train_frame = pd.DataFrame({
        "EngineCycle": [f"{row.get('EngineID', i)}_{row.get('Cycle', i)}" for i, row in enumerate(enriched.to_dict("records"))],
        "PressureRatio": enriched["pressure_ratio"],
        "TempRatio": enriched["temperature_ratio"],
        "CompEff": enriched["compressor_efficiency"],
        "TurbEff": enriched["turbine_efficiency"],
        "Thrust": enriched["thrust"],
        "TSFC": enriched["tsfc"],
        "Predicted_T4": enriched.get(f"predicted_{target_col}", pd.Series([0.0]*len(enriched))),
        "Residual_T4": enriched.get(f"residual_{target_col}", pd.Series([0.0]*len(enriched))),
        "Residual_P3": enriched["P3_Pa"] - enriched["predicted_P3_Pa"] if "P3_Pa" in enriched.columns and "predicted_P3_Pa" in enriched.columns else pd.Series([0.0] * len(enriched)),
    })

    enriched["physics_features"] = [physics_features for _ in range(len(enriched))]
    enriched["residual_features"] = [residual_features for _ in range(len(enriched))]
    enriched["training_ready_frame"] = [train_frame.iloc[i].to_dict() for i in range(len(train_frame))]
    return enriched
