import argparse
import json
import warnings

warnings.filterwarnings("ignore")

import joblib
import numpy as np
import optuna
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.base import clone
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor, VotingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor
from catboost import CatBoostRegressor

from backend.ml.advanced_pipeline import AdvancedFeatureEngineer, RAW_FEATURE_COLUMNS, make_preprocessor, nasa_phm_score, write_json
from backend.ml.config import MODELS_DIR, PROJECT_ROOT, RANDOM_SEED, TARGET_COLUMNS


DATA_DIR = PROJECT_ROOT / "public" / "dataset"
RESULTS_DIR = PROJECT_ROOT / "evaluation_results" / "ml_optimization"
INPUT_COLUMNS = ["EngineID", "Cycle"] + RAW_FEATURE_COLUMNS


def load_data():
    raw = pd.read_csv(DATA_DIR / "train.csv")
    gt = pd.read_csv(DATA_DIR / "ground_truth.csv")
    df = raw.merge(gt, on=["EngineID", "Cycle"], validate="one_to_one")
    return df.sort_values(["EngineID", "Cycle"]).reset_index(drop=True)


def metric_dict(y, pred):
    return {
        "MAE": float(mean_absolute_error(y, pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y, pred))),
        "R2": float(r2_score(y, pred)),
        "NASA_PHM": nasa_phm_score(y, pred),
    }


def candidates():
    return {
        "LightGBM": LGBMRegressor(n_estimators=180, learning_rate=0.04, num_leaves=15, max_depth=4, subsample=0.9, colsample_bytree=0.9, min_child_samples=4, random_state=RANDOM_SEED, n_jobs=-1, verbose=-1),
        "CatBoost": CatBoostRegressor(iterations=180, learning_rate=0.04, depth=4, l2_leaf_reg=4, random_seed=RANDOM_SEED, verbose=False, allow_writing_files=False, thread_count=-1),
        "XGBoost": XGBRegressor(n_estimators=180, learning_rate=0.04, max_depth=3, subsample=0.9, colsample_bytree=0.9, objective="reg:squarederror", random_state=RANDOM_SEED, n_jobs=-1),
        "ExtraTrees": ExtraTreesRegressor(n_estimators=160, random_state=RANDOM_SEED, n_jobs=-1),
        "RandomForest": RandomForestRegressor(n_estimators=160, random_state=RANDOM_SEED, n_jobs=-1),
        "HistGradientBoosting": HistGradientBoostingRegressor(max_iter=180, learning_rate=0.04, random_state=RANDOM_SEED),
        "Ridge": Ridge(alpha=2.0),
        "ElasticNet": ElasticNet(alpha=0.001, l1_ratio=0.15, max_iter=20000, random_state=RANDOM_SEED),
    }


def cv(estimator, X, y, groups, splitter):
    pred = np.zeros(len(y))
    fold_scores = []
    for tr, va in splitter.split(X, y, groups):
        model = Pipeline([("imputer", SimpleImputer(strategy="median")), ("model", clone(estimator))])
        model.fit(X.iloc[tr], y[tr])
        pred[va] = model.predict(X.iloc[va])
        fold_scores.append(metric_dict(y[va], pred[va]))
    avg = {k: float(np.mean([s[k] for s in fold_scores])) for k in fold_scores[0]}
    avg["folds"] = fold_scores
    return avg, pred


def tune_lgbm(X, y, groups, trials):
    splitter = GroupKFold(n_splits=min(5, len(np.unique(groups))))

    def objective(trial):
        model = LGBMRegressor(
            learning_rate=trial.suggest_float("learning_rate", 0.005, 0.12, log=True),
            max_depth=trial.suggest_int("max_depth", 2, 8),
            num_leaves=trial.suggest_int("num_leaves", 4, 64),
            n_estimators=trial.suggest_int("n_estimators", 50, 260),
            subsample=trial.suggest_float("subsample", 0.55, 1.0),
            feature_fraction=trial.suggest_float("feature_fraction", 0.55, 1.0),
            reg_alpha=trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            reg_lambda=trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
            min_child_samples=trial.suggest_int("min_child_samples", 2, 25),
            random_state=RANDOM_SEED,
            n_jobs=-1,
            verbose=-1,
        )
        score, _ = cv(model, X, y, groups, splitter)
        trial.report(score["MAE"], 0)
        if trial.should_prune():
            raise optuna.TrialPruned()
        return score["MAE"]

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=RANDOM_SEED), pruner=optuna.pruners.MedianPruner())
    study.optimize(objective, n_trials=trials, show_progress_bar=False)
    best = LGBMRegressor(**study.best_params, random_state=RANDOM_SEED, n_jobs=-1, verbose=-1)
    score, pred = cv(best, X, y, groups, splitter)
    return best, study.best_params, score, pred


def final_pipeline(estimator):
    return Pipeline([("prep", make_preprocessor(k="all", scale=False)), ("model", clone(estimator))])


def run(trials):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()
    raw_X = df[INPUT_COLUMNS]
    feature_engineer = AdvancedFeatureEngineer().fit(raw_X)
    X = pd.DataFrame(feature_engineer.transform(raw_X), columns=feature_engineer.feature_names_)
    groups = df["EngineID"].to_numpy()
    gkf = GroupKFold(n_splits=min(5, df["EngineID"].nunique()))
    logo = LeaveOneGroupOut()

    report = {}
    params = {}
    residual_frames = []
    importance = {}
    for target in TARGET_COLUMNS:
        y = df[target].to_numpy()
        target_results = {}
        best_name, best_est, best_score, best_pred = None, None, None, None
        for name, est in candidates().items():
            score, pred = cv(est, X, y, groups, gkf)
            target_results[name] = score
            if best_score is None or score["MAE"] < best_score["MAE"]:
                best_name, best_est, best_score, best_pred = name, est, score, pred

        ensemble = VotingRegressor(
            [("lgbm", candidates()["LightGBM"]), ("xgb", candidates()["XGBoost"]), ("extra", candidates()["ExtraTrees"])],
            weights=[0.45, 0.30, 0.25],
            n_jobs=-1,
        )
        ens_score, ens_pred = cv(ensemble, X, y, groups, gkf)
        target_results["WeightedEnsemble"] = ens_score
        target_results["StackingEnsemble"] = {"skipped": "Omitted in fast optimizer because nested CV stacking was slower than available runtime."}
        if ens_score["MAE"] < best_score["MAE"]:
            best_name, best_est, best_score, best_pred = "WeightedEnsemble", ensemble, ens_score, ens_pred

        tuned_est, best_params, tuned_score, tuned_pred = tune_lgbm(X, y, groups, trials)
        target_results["LightGBM_Optuna"] = tuned_score
        params[target] = best_params
        if tuned_score["MAE"] < best_score["MAE"]:
            best_name, best_est, best_score, best_pred = "LightGBM_Optuna", tuned_est, tuned_score, tuned_pred

        loo_score, _ = cv(best_est, X, y, groups, logo)
        pipe = final_pipeline(best_est)
        pipe.fit(raw_X, y)
        pipe._model_name = best_name
        pipe._validation_metrics = best_score
        joblib.dump(pipe, MODELS_DIR / f"{target}.joblib")

        report[target] = {"best_model": best_name, "groupkfold": best_score, "leave_one_engine_out": loo_score, "benchmark": target_results}
        residual_frames.append(pd.DataFrame({"target": target, "EngineID": df["EngineID"], "Cycle": df["Cycle"], "actual": y, "prediction": best_pred, "abs_residual": np.abs(y - best_pred)}))
        if hasattr(best_est, "feature_importances_"):
            vals = best_est.feature_importances_
        else:
            vals = np.zeros(X.shape[1])
        importance[target] = [{"feature": f, "importance": float(v)} for f, v in sorted(zip(X.columns, vals), key=lambda x: x[1], reverse=True)[:25]]

    residuals = pd.concat(residual_frames, ignore_index=True)
    residuals.to_csv(RESULTS_DIR / "residuals_oof.csv", index=False)
    write_json(MODELS_DIR / "feature_columns.json", INPUT_COLUMNS)
    write_json(RESULTS_DIR / "benchmark_results.json", report)
    write_json(RESULTS_DIR / "best_hyperparameters.json", params)
    write_json(RESULTS_DIR / "feature_importance.json", importance)
    write_json(RESULTS_DIR / "residual_analysis.json", {
        "worst_engines": residuals.groupby("EngineID")["abs_residual"].mean().sort_values(ascending=False).head(5).to_dict(),
        "worst_cycles": residuals.groupby("Cycle")["abs_residual"].mean().sort_values(ascending=False).head(5).to_dict(),
        "largest_residuals": residuals.sort_values("abs_residual", ascending=False).head(20).to_dict("records"),
    })
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=100)
    args = parser.parse_args()
    print(json.dumps(run(args.trials), indent=2))
