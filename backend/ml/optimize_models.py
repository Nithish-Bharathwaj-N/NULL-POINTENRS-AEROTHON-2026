import argparse
import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import joblib
import numpy as np
import optuna
import pandas as pd
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sklearn.base import clone
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor, StackingRegressor, VotingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

from backend.ml.advanced_pipeline import RAW_FEATURE_COLUMNS, make_preprocessor, nasa_phm_score, write_json
from backend.ml.config import MODELS_DIR, PROJECT_ROOT, RANDOM_SEED, TARGET_COLUMNS


RESULTS_DIR = PROJECT_ROOT / "evaluation_results" / "ml_optimization"
DATA_DIR = PROJECT_ROOT / "public" / "dataset"


def load_labeled_data():
    X = pd.read_csv(DATA_DIR / "train.csv")
    y = pd.read_csv(DATA_DIR / "ground_truth.csv")
    df = X.merge(y, on=["EngineID", "Cycle"], validate="one_to_one")
    return df.sort_values(["EngineID", "Cycle"]).reset_index(drop=True)


def metrics(y_true, y_pred):
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "R2": float(r2_score(y_true, y_pred)),
        "NASA_PHM": nasa_phm_score(y_true, y_pred),
    }


def model_candidates():
    tree = {
        "ExtraTrees": ExtraTreesRegressor(n_estimators=180, min_samples_leaf=1, random_state=RANDOM_SEED, n_jobs=-1),
        "RandomForest": RandomForestRegressor(n_estimators=180, min_samples_leaf=1, random_state=RANDOM_SEED, n_jobs=-1),
        "HistGradientBoosting": HistGradientBoostingRegressor(max_iter=180, learning_rate=0.04, l2_regularization=0.01, random_state=RANDOM_SEED),
        "LightGBM": LGBMRegressor(n_estimators=260, learning_rate=0.035, num_leaves=12, max_depth=4, subsample=0.85, colsample_bytree=0.85, reg_alpha=0.01, reg_lambda=0.1, min_child_samples=5, random_state=RANDOM_SEED, n_jobs=-1, verbose=-1),
        "CatBoost": CatBoostRegressor(iterations=220, learning_rate=0.035, depth=4, l2_leaf_reg=4.0, loss_function="RMSE", random_seed=RANDOM_SEED, verbose=False, allow_writing_files=False, thread_count=-1),
        "XGBoost": XGBRegressor(n_estimators=260, learning_rate=0.035, max_depth=3, subsample=0.85, colsample_bytree=0.85, reg_alpha=0.01, reg_lambda=1.0, objective="reg:squarederror", random_state=RANDOM_SEED, n_jobs=-1),
    }
    linear = {
        "Ridge": Ridge(alpha=5.0, random_state=RANDOM_SEED),
        "ElasticNet": ElasticNet(alpha=0.001, l1_ratio=0.15, random_state=RANDOM_SEED, max_iter=20000),
    }
    return {**tree, **linear}


def make_pipeline(model_name, model):
    scale = model_name in {"Ridge", "ElasticNet"}
    return Pipeline([("prep", make_preprocessor(k="all", scale=scale)), ("model", model)])


def cross_val_score_model(model, X, y, groups, splitter):
    fold_metrics = []
    preds = np.zeros(len(y))
    for tr, va in splitter.split(X, y, groups):
        fitted = clone(model)
        fitted.fit(X.iloc[tr], y[tr])
        fold_pred = fitted.predict(X.iloc[va])
        preds[va] = fold_pred
        fold_metrics.append(metrics(y[va], fold_pred))
    out = {k: float(np.mean([m[k] for m in fold_metrics])) for k in fold_metrics[0]}
    out["folds"] = fold_metrics
    return out, preds


def benchmark_models(df, target):
    X = df[["EngineID", "Cycle"] + RAW_FEATURE_COLUMNS]
    y = df[target].to_numpy()
    groups = df["EngineID"].to_numpy()
    splitter = GroupKFold(n_splits=min(5, df["EngineID"].nunique()))
    results = {}
    fitted_candidates = model_candidates()

    for name, estimator in fitted_candidates.items():
        pipe = make_pipeline(name, estimator)
        score, _ = cross_val_score_model(pipe, X, y, groups, splitter)
        results[name] = score

    base_estimators = [
        ("lgbm", clone(fitted_candidates["LightGBM"])),
        ("cat", clone(fitted_candidates["CatBoost"])),
        ("extra", clone(fitted_candidates["ExtraTrees"])),
    ]
    ensemble_models = {
        "WeightedEnsemble": VotingRegressor(base_estimators, weights=[0.45, 0.35, 0.20], n_jobs=-1),
        "StackingEnsemble": StackingRegressor(base_estimators, final_estimator=Ridge(alpha=1.0), n_jobs=-1),
    }
    for name, estimator in ensemble_models.items():
        pipe = make_pipeline(name, estimator)
        score, _ = cross_val_score_model(pipe, X, y, groups, splitter)
        results[name] = score

    best_name = min(results, key=lambda k: (results[k]["MAE"], -results[k]["R2"]))
    return best_name, results


def tune_lightgbm(df, target, trials):
    X = df[["EngineID", "Cycle"] + RAW_FEATURE_COLUMNS]
    y = df[target].to_numpy()
    groups = df["EngineID"].to_numpy()
    splitter = GroupKFold(n_splits=min(5, df["EngineID"].nunique()))

    def objective(trial):
        params = {
            "learning_rate": trial.suggest_float("learning_rate", 0.005, 0.12, log=True),
            "max_depth": trial.suggest_int("max_depth", 2, 8),
            "num_leaves": trial.suggest_int("num_leaves", 4, 64),
            "n_estimators": trial.suggest_int("n_estimators", 80, 420),
            "subsample": trial.suggest_float("subsample", 0.55, 1.0),
            "feature_fraction": trial.suggest_float("feature_fraction", 0.55, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
            "min_child_samples": trial.suggest_int("min_child_samples", 2, 25),
        }
        model = LGBMRegressor(**params, random_state=RANDOM_SEED, n_jobs=-1, verbose=-1)
        pipe = make_pipeline("LightGBM", model)
        score, _ = cross_val_score_model(pipe, X, y, groups, splitter)
        trial.report(score["MAE"], step=0)
        if trial.should_prune():
            raise optuna.TrialPruned()
        return score["MAE"]

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=RANDOM_SEED), pruner=optuna.pruners.MedianPruner())
    study.optimize(objective, n_trials=trials, show_progress_bar=False)
    best = LGBMRegressor(**study.best_params, random_state=RANDOM_SEED, n_jobs=-1, verbose=-1)
    pipe = make_pipeline("LightGBM", best)
    score, oof = cross_val_score_model(pipe, X, y, groups, splitter)
    return pipe, study.best_params, score, oof


def residual_analysis(df, oof_predictions):
    rows = []
    for target, pred in oof_predictions.items():
        tmp = df[["EngineID", "Cycle", "Altitude_m", "Mach"]].copy()
        tmp["target"] = target
        tmp["actual"] = df[target]
        tmp["prediction"] = pred
        tmp["abs_residual"] = np.abs(tmp["actual"] - tmp["prediction"])
        rows.append(tmp)
    residuals = pd.concat(rows, ignore_index=True)
    residuals.to_csv(RESULTS_DIR / "residuals_oof.csv", index=False)
    return {
        "worst_engines": residuals.groupby("EngineID")["abs_residual"].mean().sort_values(ascending=False).head(5).to_dict(),
        "worst_cycles": residuals.groupby("Cycle")["abs_residual"].mean().sort_values(ascending=False).head(5).to_dict(),
        "largest_residuals": residuals.sort_values("abs_residual", ascending=False).head(20).to_dict("records"),
    }


def train_and_save(trials):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_labeled_data()
    all_results = {}
    best_params = {}
    oof_predictions = {}
    feature_importance = {}

    for target in TARGET_COLUMNS:
        best_name, benchmark = benchmark_models(df, target)
        tuned_model, params, tuned_score, oof = tune_lightgbm(df, target, trials)
        benchmark["LightGBM_Optuna"] = tuned_score
        if tuned_score["MAE"] <= benchmark[best_name]["MAE"]:
            final_model = tuned_model
            best_name = "LightGBM_Optuna"
            best_params[target] = params
        else:
            final_model = make_pipeline(best_name, model_candidates()[best_name])
            best_params[target] = {}
            _, oof = cross_val_score_model(final_model, df[["EngineID", "Cycle"] + RAW_FEATURE_COLUMNS], df[target].to_numpy(), df["EngineID"].to_numpy(), GroupKFold(n_splits=5))

        final_model.fit(df[["EngineID", "Cycle"] + RAW_FEATURE_COLUMNS], df[target])
        final_model._validation_metrics = benchmark[best_name]
        final_model._model_name = best_name
        joblib.dump(final_model, MODELS_DIR / f"{target}.joblib")
        all_results[target] = {"best_model": best_name, "benchmark": benchmark}
        oof_predictions[target] = oof

        perm = permutation_importance(
            final_model, df[["EngineID", "Cycle"] + RAW_FEATURE_COLUMNS], df[target],
            n_repeats=8, random_state=RANDOM_SEED, n_jobs=-1,
        )
        feature_importance[target] = [
            {"feature": col, "importance": float(imp)}
            for col, imp in sorted(zip(["EngineID", "Cycle"] + RAW_FEATURE_COLUMNS, perm.importances_mean), key=lambda x: x[1], reverse=True)
        ]

    write_json(MODELS_DIR / "feature_columns.json", ["EngineID", "Cycle"] + RAW_FEATURE_COLUMNS)
    write_json(RESULTS_DIR / "benchmark_results.json", all_results)
    write_json(RESULTS_DIR / "best_hyperparameters.json", best_params)
    write_json(RESULTS_DIR / "feature_importance.json", feature_importance)
    write_json(RESULTS_DIR / "residual_analysis.json", residual_analysis(df, oof_predictions))
    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=100)
    args = parser.parse_args()
    print(json.dumps(train_and_save(args.trials), indent=2))
