"""
predict.py
==========
Runtime inference engine for transparent, fully interpretable turbojet health and performance predictions.

Loads saved Polynomial Ridge models from trained_models/ and provides:
- Single-row (.predict_one) and batch (.predict_batch) predictions
- Mathematically principled residual uncertainty estimates
- Feature attribution / SHAP explanations
- Component health risk assessment and maintenance action recommendations
"""

import json
import warnings

warnings.filterwarnings("ignore")

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from backend.ml.config import TARGET_COLUMNS, TARGET_BOUNDS, MODELS_DIR
from backend.ml.features import engineer_features


try:
    import shap
except ImportError:
    shap = None


COMPONENT_TARGETS = [
    "CompressorHealth", "CombustorHealth", "TurbineHealth", "OverallHealth",
]


FEATURE_LABELS = {
    "RPM_rev_min": "shaft speed",
    "FuelFlow_kg_s": "fuel flow",
    "P2_Pa": "compressor inlet pressure",
    "T2_K": "compressor exit temperature",
    "P3_Pa": "combustor pressure",
    "T3_K": "turbine inlet temperature",
    "P4_Pa": "turbine exit pressure",
    "T4_K": "turbine exit temperature",
    "PR_compressor": "compressor pressure ratio",
    "PR_turbine": "turbine pressure ratio",
    "PR_overall": "overall pressure ratio",
    "TR_combustor": "combustor temperature ratio",
    "TR_turbine": "turbine temperature ratio",
    "delta_T_compressor": "compressor temperature rise",
    "delta_T_combustor": "combustor temperature rise",
    "delta_T_turbine": "turbine temperature drop",
    "RPM_corrected": "corrected shaft speed",
    "FuelFlow_per_RPM": "fuel flow per RPM",
    "EPR": "engine pressure ratio",
    "V0": "flight speed",
    "Vj": "jet velocity",
    "delta_V": "velocity delta",
    "FuelFlow_delta_V": "fuel flow velocity product",
    "mdot_proxy": "mass flow proxy",
    "thrust_proxy_physics": "physics thrust proxy",
}


def clip_to_bounds(target: str, prediction: float) -> float:
    """Clips prediction to physically valid range specified in TARGET_BOUNDS."""
    low, high = TARGET_BOUNDS.get(target, (None, None))
    if low is not None:
        prediction = max(prediction, low)
    if high is not None:
        prediction = min(prediction, high)
    return prediction


def predict_with_uncertainty(model, row: pd.DataFrame):
    """
    Returns (predictions, uncertainties) for transparent regression models.
    Uncertainty is derived from the model's cross-validated residual standard deviation.
    """
    pred = model.predict(row)
    residual_std = getattr(model, "_residual_std", None)
    if residual_std is None:
        residual_std = getattr(model, "_fallback_uncertainty", 0.01)
    
    std = np.full(len(pred), float(residual_std))
    return pred, std


def _health_severity(health: float, uncertainty: float) -> tuple[str, float, str]:
    """Convert health score into risk level and status description."""
    risk_score = min(1.0, max(0.0, (1.0 - health) + max(0.0, uncertainty) * 0.5))
    if health < 0.60 or risk_score >= 0.45:
        return "critical", risk_score, "High probability of near-term degradation."
    if health < 0.78 or risk_score >= 0.28:
        return "high", risk_score, "Likely degradation trend; service should be planned soon."
    if health < 0.90 or risk_score >= 0.16:
        return "medium", risk_score, "Early degradation indicators present."
    return "low", risk_score, "No major near-term damage indicators from this reading."


def _component_service_action(component: str, severity: str) -> dict:
    action_map = {
        "CompressorHealth": {
            "component": "Compressor",
            "damage_mode": "fouling, blade erosion, or pressure-ratio loss",
            "critical": "Ground engine for borescope inspection; clean compressor and inspect blades/seals.",
            "high": "Schedule compressor wash and borescope inspection within the next maintenance window.",
            "medium": "Trend compressor pressure ratio and corrected RPM; prepare wash if trend continues.",
            "low": "Continue normal monitoring of pressure ratio and corrected RPM.",
        },
        "CombustorHealth": {
            "component": "Combustor",
            "damage_mode": "burner efficiency loss, hot streaks, or fuel nozzle wear",
            "critical": "Inspect combustor liner and fuel nozzles; verify temperature spread.",
            "high": "Schedule combustor inspection; check fuel nozzles and T3 excursions.",
            "medium": "Trend combustor temperature ratio and fuel flow; inspect nozzles at next service.",
            "low": "Continue normal monitoring of temperature ratio and fuel-flow stability.",
        },
        "TurbineHealth": {
            "component": "Turbine",
            "damage_mode": "blade thermal fatigue, tip clearance growth, or work-extraction loss",
            "critical": "Ground engine for turbine borescope; inspect blades, vanes, and exhaust temperature margin.",
            "high": "Schedule turbine borescope; review T3/T4 temperature drop.",
            "medium": "Trend turbine temperature drop and pressure ratio; reduce high-temperature exposure.",
            "low": "Continue normal monitoring of turbine temperature drop and pressure ratio.",
        },
        "OverallHealth": {
            "component": "Engine",
            "damage_mode": "system-level performance deterioration",
            "critical": "Run full engine health assessment and maintenance review before continued service.",
            "high": "Plan integrated engine inspection; compare thrust, TSFC, and component health trends.",
            "medium": "Increase monitoring frequency and review recent flight-cycle trend history.",
            "low": "Continue standard health monitoring.",
        },
    }
    template = action_map[component]
    priority = {"critical": 1, "high": 2, "medium": 3, "low": 4}[severity]
    return {
        "component": template["component"],
        "priority": priority,
        "severity": severity,
        "potential_damage": template["damage_mode"],
        "action": template[severity],
    }


class HealthPredictor:
    """
    Unified predictor for all 6 target variables using transparent white-box models.
    """

    def __init__(self, models: dict, feature_columns):
        self.models = models
        self.feature_columns = feature_columns
        self._shap_explainers = {}

    def _feature_columns_for_target(self, target: str) -> list:
        target_map = getattr(self, "target_feature_columns", {})
        if target in target_map:
            return target_map[target]
        if isinstance(self.feature_columns, dict) and target in self.feature_columns:
            return self.feature_columns[target]
        if target in self.models and hasattr(self.models[target], "feature_names_in_"):
            return list(self.models[target].feature_names_in_)
        return self.feature_columns if isinstance(self.feature_columns, list) else []

    def _prepare_input(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
        engineered = engineer_features(df)
        if "Cycle" in df.columns and "Cycle" not in engineered.columns:
            engineered["Cycle"] = df["Cycle"]
        if "EngineID" in df.columns and "EngineID" not in engineered.columns:
            engineered["EngineID"] = df["EngineID"]

        for col in columns:
            if col not in engineered.columns:
                engineered[col] = 0.0

        return engineered[columns]

    @classmethod
    def load(cls, models_dir=None) -> "HealthPredictor":
        """Load trained models from disk."""
        models_dir = Path(models_dir) if models_dir else MODELS_DIR
        feature_path = models_dir / "feature_columns.json"
        target_feature_path = models_dir / "target_feature_columns.json"

        if not feature_path.exists():
            raise FileNotFoundError(
                f"No trained models found in {models_dir}. Run "
                "'python3 -m backend.ml.train' first."
            )

        with open(feature_path) as f:
            feature_columns = json.load(f)

        target_feature_columns = {}
        if target_feature_path.exists():
            with open(target_feature_path) as f:
                target_feature_columns = json.load(f)

        models = {}
        for target in TARGET_COLUMNS:
            model_path = models_dir / f"{target}.joblib"
            models[target] = joblib.load(model_path)

        hp = cls(models, feature_columns)
        hp.target_feature_columns = target_feature_columns
        return hp

    def _shap_impacts_for_target(self, target: str, model, row: pd.DataFrame) -> list[dict]:
        """Compute feature impacts for target prediction."""
        if shap is None:
            return []

        cache_key = target
        if cache_key not in self._shap_explainers:
            masker = shap.maskers.Independent(row)
            self._shap_explainers[cache_key] = shap.Explainer(model.predict, masker)

        try:
            values = self._shap_explainers[cache_key](row)
            shap_values = np.asarray(values.values)[0]

            impacts = []
            for feature, feature_value, impact in zip(row.columns, row.iloc[0], shap_values):
                impacts.append({
                    "feature": feature,
                    "label": FEATURE_LABELS.get(feature, feature.replace("_", " ")),
                    "value": float(feature_value),
                    "shap_value": float(impact),
                    "effect": "increases_prediction" if impact >= 0 else "decreases_prediction",
                })

            impacts.sort(key=lambda item: abs(item["shap_value"]), reverse=True)
            return impacts[:8]
        except Exception:
            return []

    def _build_shap_explanations(self, row: pd.DataFrame) -> dict:
        explanations = {}
        for target in COMPONENT_TARGETS:
            explanations[target] = {
                "top_feature_impacts": self._shap_impacts_for_target(
                    target, self.models[target], row
                )
            }
        return explanations

    def _assess_future_damage(self, results: dict, explanations: dict | None) -> tuple[list, list]:
        risks = []
        actions = []

        for target in COMPONENT_TARGETS:
            health = results[target]["prediction"]
            uncertainty = results[target]["uncertainty"]
            severity, risk_score, rationale = _health_severity(health, uncertainty)
            top_drivers = []
            if explanations and target in explanations and "top_feature_impacts" in explanations[target]:
                top_drivers = [
                    impact["label"]
                    for impact in explanations[target]["top_feature_impacts"][:3]
                ]

            action = _component_service_action(target, severity)
            risks.append({
                "component": action["component"],
                "severity": severity,
                "risk_score": round(risk_score, 4),
                "predicted_health": round(health, 4),
                "uncertainty": round(uncertainty, 4),
                "potential_damage": action["potential_damage"],
                "rationale": rationale,
                "main_drivers": top_drivers,
            })
            actions.append(action)

        severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        risks.sort(key=lambda item: (severity_rank[item["severity"]], -item["risk_score"]))
        actions.sort(key=lambda item: item["priority"])
        return risks, actions

    def predict_one(self, sensor_reading: dict, include_shap: bool = True) -> dict:
        """
        Predict all six targets for a single engine sensor reading.
        """
        row = pd.DataFrame([sensor_reading])

        results = {}
        for target, model in self.models.items():
            target_cols = self._feature_columns_for_target(target)
            target_row = self._prepare_input(row, target_cols)
            pred, std = predict_with_uncertainty(model, target_row)
            pred_val = clip_to_bounds(target, float(pred[0]))
            unc_val = float(std[0])
            unc_pct = round((unc_val / pred_val * 100.0), 2) if pred_val > 1e-6 else 0.0
            results[target] = {
                "prediction": pred_val,
                "uncertainty": unc_val,
                "uncertainty_pct": unc_pct,
            }

        explanations = None
        if include_shap and shap is not None:
            explanations = self._build_shap_explanations(
                self._prepare_input(row, self._feature_columns_for_target(COMPONENT_TARGETS[0]))
            )

        risks, actions = self._assess_future_damage(results, explanations)
        results["shap_explanations"] = explanations
        results["future_damage_risks"] = risks
        results["recommended_service_actions"] = actions

        return results

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict all six targets for a DataFrame of sensor readings.
        """
        output = df.copy()

        for target, model in self.models.items():
            target_cols = self._feature_columns_for_target(target)
            X = self._prepare_input(df, target_cols)
            pred, std = predict_with_uncertainty(model, X)
            low, high = TARGET_BOUNDS.get(target, (None, None))
            pred = np.clip(pred, low, high)
            output[f"{target}_predicted"] = pred
            output[f"{target}_uncertainty"] = std
            with np.errstate(divide="ignore", invalid="ignore"):
                unc_pct = np.where(pred > 1e-6, (std / pred) * 100.0, 0.0)
            output[f"{target}_uncertainty_pct"] = np.round(unc_pct, 2)

        return output


if __name__ == "__main__":
    predictor = HealthPredictor.load()
    example_reading = {
        "Altitude_m": 5000, "Mach": 0.6, "Tamb_K": 250, "Pamb_Pa": 50000,
        "RPM_rev_min": 40000, "FuelFlow_kg_s": 1.4,
        "P2_Pa": 100000, "T2_K": 330, "P3_Pa": 95000, "T3_K": 3300,
        "P4_Pa": 85000, "T4_K": 3200,
    }
    result = predictor.predict_one(example_reading, include_shap=False)
    for target in TARGET_COLUMNS:
        values = result[target]
        print(f"{target:18s} prediction={values['prediction']:.4f}   "
              f"uncertainty={values['uncertainty']:.4f} ({values['uncertainty_pct']}%)")

    print("\nTop future damage risks:")
    for risk in result["future_damage_risks"]:
        print(f"- {risk['component']}: {risk['severity']} "
              f"(risk={risk['risk_score']:.2f}) - {risk['potential_damage']}")
