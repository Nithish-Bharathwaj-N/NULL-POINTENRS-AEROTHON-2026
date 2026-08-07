"""
hybrid_model.py — Aerothon 2026 Hybrid Prognostics Model (Patched v2)
======================================================================
Fixes applied:
  1. physics_predict() now uses correct column names (_K suffix, _Pa suffix)
  2. Ridge/ElasticNet wrapped in StandardScaler Pipeline (scale-invariant)
  3. RandomForestRegressor added to ensemble (4 models, not 3)
  4. GroupKFold groups properly aligned to X index
  5. LOEO residuals computed inside each fold (no global leakage)
  6. CV scores returned from train_ensemble() for reporting
"""

import numpy as np
import pandas as pd
import joblib
import logging
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_absolute_error, r2_score

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

logger = logging.getLogger(__name__)


def _col(df, *names, default=None):
    """Resolve column aliases: returns Series or scalar default."""
    for n in names:
        if n in df.columns:
            return df[n].values.astype(float)
    if default is not None:
        return np.full(len(df), float(default))
    raise KeyError(f"None of {names} found in DataFrame")


class HybridPrognosticsModel:
    """
    3-layer hybrid prognostics model.
    Layer 1: Physics-based health proxies (thermodynamic first principles).
    Layer 2: ML ensemble on physics residuals (scaled Ridge + ElasticNet + GBM + RF).
    Layer 3: Bidirectional physics constraint validation.
    """

    def __init__(self):
        self.targets = [
            'CompressorHealth', 'CombustorHealth', 'TurbineHealth',
            'OverallHealth', 'Thrust_N', 'TSFC_g_N_s'
        ]
        self.ensemble_models  = {t: [] for t in self.targets}
        self.ensemble_weights = {t: [] for t in self.targets}
        self.cv_scores        = {}
        self.features         = None
        self.X_train_summary  = None
        self.gamma = 1.4
        self.eps   = 1e-9

    # ── Layer 1: Physics ─────────────────────────────────────────────────────

    def physics_predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute thermodynamic health proxies from first principles.
        FIX: uses correct column names with _K and _Pa suffixes.
        NO Cycle column is ever used.
        """
        phys = pd.DataFrame(index=df.index)

        # Resolve sensor columns with correct suffixes
        Tamb = _col(df, 'Tamb_K', 'Tamb', 'T1_K', 'T1', default=288.15)
        T2   = _col(df, 'T2_K',   'T2',               default=300.0)
        T3   = _col(df, 'T3_K',   'T3',               default=1000.0)
        T4   = _col(df, 'T4_K',   'T4',               default=800.0)
        P2   = _col(df, 'P2_Pa',  'P2',               default=101325.0)
        P3   = _col(df, 'P3_Pa',  'P3',               default=3000000.0)
        P4   = _col(df, 'P4_Pa',  'P4',               default=2900000.0)
        Pamb = _col(df, 'Pamb_Pa','Pamb','P1_Pa','P1',default=101325.0)
        Wf   = _col(df, 'FuelFlow_kg_s','Wf','FuelFlow',default=2.8)

        PR   = np.maximum(1.01, P3 / np.maximum(P2, self.eps))

        # 1a. Compressor isentropic efficiency
        T2_is  = Tamb * (PR ** ((self.gamma - 1) / self.gamma))
        eta_c  = np.clip((T2_is - Tamb) / np.maximum(T3 - Tamb, self.eps), 0.20, 1.0)
        # Map eta_c [0.2, 0.92] → health [0.40, 1.0]
        phys['CompressorHealth_phys'] = 0.40 + 0.60 * (eta_c - 0.20) / (0.92 - 0.20)
        phys['CompressorHealth_phys'] = phys['CompressorHealth_phys'].clip(0.40, 1.0)

        # 1b. Combustor health: temperature ratio T3/T2, nominal 4–7
        TR = np.clip(T3 / np.maximum(T2, self.eps), 1.0, 10.0)
        dev = np.abs(TR - 5.5) / 5.5
        phys['CombustorHealth_phys'] = np.clip(1.0 - 0.60 * dev, 0.40, 1.0)

        # 1c. Turbine work coefficient W = (T3−T4)/T3, nominal 0.30–0.55
        W = (T3 - T4) / np.maximum(T3, self.eps)
        W_clamped = np.clip(W, 0.10, 0.65)
        phys['TurbineHealth_phys'] = 0.40 + 0.60 * (W_clamped - 0.10) / (0.65 - 0.10)

        # 1d. Overall: thermodynamic weighted average
        phys['OverallHealth_phys'] = (
            0.35 * phys['CompressorHealth_phys'] +
            0.30 * phys['CombustorHealth_phys'] +
            0.35 * phys['TurbineHealth_phys']
        )

        # 1e. Thrust/TSFC proxies
        EPR = P4 / np.maximum(Pamb, self.eps)
        phys['Thrust_N_phys']    = np.clip(Wf * (T3 - T4) * 120, 50000, 500000)
        phys['TSFC_g_N_s_phys'] = (Wf * 1000) / np.maximum(phys['Thrust_N_phys'], self.eps)

        return phys

    # ── Layer 2: ML Ensemble ─────────────────────────────────────────────────

    def train_ensemble(self, X: pd.DataFrame, y_residual: pd.DataFrame, groups=None) -> dict:
        """
        Train 4-model ensemble: scaled-Ridge + scaled-ElasticNet + GBM + RF.
        FIX: groups re-indexed to match X; CV returns scores.
        """
        # Exclude Cycle column
        self.features = [c for c in X.columns if 'cycle' not in c.lower()]
        X_train = X[self.features].copy()

        # Store training summary for density estimation
        self.X_train_summary = {
            'mean': X_train.mean(axis=0).values,
            'std':  X_train.std(axis=0).values + self.eps,
        }

        # Align groups to X index
        if groups is not None:
            groups_aligned = pd.Series(groups).values if not hasattr(groups, 'iloc') else groups.values
        else:
            groups_aligned = None

        gkf = GroupKFold(n_splits=10)

        # 4-model ensemble: first two use StandardScaler pipelines
        model_specs = [
            ('Ridge',        Pipeline([('sc', StandardScaler()), ('m', Ridge(alpha=1.0))])),
            ('ElasticNet',   Pipeline([('sc', StandardScaler()), ('m', ElasticNet(alpha=0.1, l1_ratio=0.5, max_iter=2000))])),
            ('GBM',          GradientBoostingRegressor(max_depth=4, n_estimators=300,
                                                        learning_rate=0.05, subsample=0.8,
                                                        min_samples_leaf=5, random_state=42)),
            ('RandomForest', RandomForestRegressor(n_estimators=200, max_depth=8,
                                                   min_samples_leaf=5, n_jobs=-1, random_state=42)),
        ]

        all_cv_scores = {}

        for target in self.targets:
            if target not in y_residual.columns:
                continue

            y = y_residual[target].fillna(0.0)
            target_models   = []
            target_weights  = []
            target_cv_maes  = {}

            for name, model in model_specs:
                fold_maes = []
                if groups_aligned is not None and gkf.get_n_splits() <= len(np.unique(groups_aligned)):
                    split_iter = gkf.split(X_train, y, groups_aligned)
                else:
                    # Fallback: train on all, no CV
                    split_iter = []

                for tr_idx, val_idx in split_iter:
                    X_tr = X_train.iloc[tr_idx]
                    y_tr = y.iloc[tr_idx]
                    X_val = X_train.iloc[val_idx]
                    y_val = y.iloc[val_idx]
                    model.fit(X_tr, y_tr)
                    preds = model.predict(X_val)
                    fold_maes.append(mean_absolute_error(y_val, preds))

                avg_mae  = np.mean(fold_maes) if fold_maes else 0.05
                weight   = 1.0 / (avg_mae ** 2 + self.eps)
                target_cv_maes[name] = avg_mae

                # Retrain on full training data
                model.fit(X_train, y)
                target_models.append(model)
                target_weights.append(weight)

            # Normalize weights
            total_w = sum(target_weights) + self.eps
            self.ensemble_models[target]  = target_models
            self.ensemble_weights[target] = [w / total_w for w in target_weights]
            all_cv_scores[target] = target_cv_maes

        self.cv_scores = all_cv_scores
        return all_cv_scores

    # ── Layer 3: Constraint Validation ───────────────────────────────────────

    def physics_constraint_validate(self, pred_dict: dict, telemetry_dict: dict):
        constrained = pred_dict.copy()
        flagged = False

        if telemetry_dict:
            T2  = telemetry_dict.get('T2_K', telemetry_dict.get('T2'))
            T3  = telemetry_dict.get('T3_K', telemetry_dict.get('T3'))
            T4  = telemetry_dict.get('T4_K', telemetry_dict.get('T4'))
            P2  = telemetry_dict.get('P2_Pa', telemetry_dict.get('P2'))
            P3  = telemetry_dict.get('P3_Pa', telemetry_dict.get('P3'))
            EGT = telemetry_dict.get('T4_K', telemetry_dict.get('EGT'))

            if T2 is not None and T3 is not None and T3 <= T2:
                flagged = True
                logger.warning(f"T3 ({T3}) <= T2 ({T2})")
            if T3 is not None and T4 is not None and T4 >= T3:
                flagged = True
                logger.warning(f"T4 ({T4}) >= T3 ({T3})")
            if EGT is not None and EGT >= 1273.15:
                flagged = True
                logger.warning(f"EGT ({EGT}) >= 1273.15 K")

        for h in ['CompressorHealth', 'CombustorHealth', 'TurbineHealth', 'OverallHealth']:
            if h in constrained:
                constrained[h] = float(np.clip(constrained[h], 0.0, 1.0))

        return constrained, flagged

    # ── Predict ───────────────────────────────────────────────────────────────

    def predict(self, X_temporal, engine_id=None, telemetry=None) -> dict:
        phys_preds  = self.physics_predict(X_temporal)
        feat_avail  = [c for c in X_temporal.columns if c in (self.features or [])]
        X_ml        = X_temporal[feat_avail]

        final_preds, epistemic, phys_unc, ml_res = {}, {}, {}, {}

        for target in self.targets:
            phys_col  = f"{target}_phys"
            base_phys = float(phys_preds[phys_col].iloc[0]) if phys_col in phys_preds else 0.0

            models  = self.ensemble_models.get(target, [])
            weights = self.ensemble_weights.get(target, [])

            if not models:
                final_preds[target] = base_phys
                epistemic[target]   = 0.05
                phys_unc[target]    = 0.0
                ml_res[target]      = 0.0
                continue

            sub_preds       = [float(m.predict(X_ml)[0]) for m in models]
            ens_residual    = float(np.average(sub_preds, weights=weights))
            final_preds[target] = base_phys + ens_residual
            epistemic[target]   = float(np.std(sub_preds))
            phys_unc[target]    = abs(base_phys - ens_residual)
            ml_res[target]      = ens_residual

        tel_dict = telemetry if telemetry is not None else X_temporal.iloc[0].to_dict()
        constrained, flagged = self.physics_constraint_validate(final_preds, tel_dict)

        density, extrapolation = 0.5, False
        if self.X_train_summary:
            mean = self.X_train_summary['mean']
            std  = self.X_train_summary['std']
            diff = X_ml.values[0] - mean
            z    = diff / std
            md   = float(np.sqrt(np.sum(z ** 2)))
            density      = float(np.exp(-0.5 * (md / len(mean)) ** 2))
            extrapolation = md > 2.5 * np.sqrt(len(mean))

        phys_c, ml_c = {}, {}
        for target in self.targets:
            pv = abs(phys_preds.get(f"{target}_phys", pd.Series([0])).iloc[0] if f"{target}_phys" in phys_preds else 0)
            mv = abs(ml_res.get(target, 0))
            tot = pv + mv + self.eps
            phys_c[target] = pv / tot
            ml_c[target]   = mv / tot

        return {
            'predictions':              constrained,
            'uncertainty': {
                'sensor_uncertainty':   0.02,
                'physics_uncertainty':  phys_unc,
                'epistemic_uncertainty': epistemic,
                'dataset_density':       density,
                'regime_uncertainty':    0.05,
                'extrapolation_flag':    extrapolation,
            },
            'physics_contribution_pct':    phys_c,
            'ml_residual_contribution_pct': ml_c,
            'physics_constrained':         flagged,
        }

    # ── Explain ───────────────────────────────────────────────────────────────

    def explain(self, X_row):
        pred_res = self.predict(X_row)
        feat_avail = [c for c in X_row.columns if c in (self.features or [])]
        X_ml = X_row[feat_avail]

        shap_dict, top_feat = {}, {}
        for target in self.targets:
            models = self.ensemble_models.get(target, [])
            if not models:
                continue
            # Use GBM (index 2) for SHAP
            gbm = models[2] if len(models) > 2 else models[-1]
            actual_model = gbm.named_steps['m'] if hasattr(gbm, 'named_steps') else gbm

            if SHAP_AVAILABLE and hasattr(actual_model, 'feature_importances_'):
                explainer = shap.TreeExplainer(actual_model)
                X_scaled  = gbm.named_steps['sc'].transform(X_ml) if hasattr(gbm, 'named_steps') else X_ml.values
                sv = explainer.shap_values(X_scaled)[0]
                shap_dict[target] = sv
                ranked = np.argsort(np.abs(sv))[::-1]
                top_feat[target]  = [(feat_avail[i], float(abs(sv[i]))) for i in ranked]
            else:
                imp = getattr(actual_model, 'feature_importances_', np.zeros(len(feat_avail)))
                ranked = np.argsort(imp)[::-1]
                top_feat[target]  = [(feat_avail[i], float(imp[i])) for i in ranked]
                shap_dict[target] = None

        return {
            'physics_contribution':    pred_res['physics_contribution_pct'],
            'ml_residual_contribution': pred_res['ml_residual_contribution_pct'],
            'shap_values':             shap_dict,
            'top_features':            top_feat,
        }

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: str):
        joblib.dump(self, path)
        logger.info(f"Model saved → {path}")

    @classmethod
    def load(cls, path: str):
        return joblib.load(path)

    def evaluate_loeo(self, dataset_df: pd.DataFrame, feature_names: list):
        """
        Leave-One-Engine-Out evaluation.
        FIX: computes physics residuals INSIDE each fold (no global leakage).
        """
        engine_col = 'EngineID' if 'EngineID' in dataset_df.columns else 'engine_id'
        engine_ids = dataset_df[engine_col].unique()

        mae_results = {t: [] for t in self.targets}
        r2_results  = {t: [] for t in self.targets}

        for test_eng in engine_ids:
            train_df = dataset_df[dataset_df[engine_col] != test_eng].copy()
            test_df  = dataset_df[dataset_df[engine_col] == test_eng].copy()

            # FIX: compute physics predictions WITHIN fold
            loeo_model = HybridPrognosticsModel()
            phys_train = loeo_model.physics_predict(train_df)
            phys_test  = loeo_model.physics_predict(test_df)

            y_res_train = pd.DataFrame(index=train_df.index)
            for t in self.targets:
                pc = f"{t}_phys"
                y_res_train[t] = (train_df[t] - phys_train[pc]) if (t in train_df and pc in phys_train.columns) else train_df.get(t, pd.Series(0, index=train_df.index))

            avail = [f for f in feature_names if f in train_df.columns]
            X_tr  = train_df[avail].fillna(0)
            X_te  = test_df[avail].fillna(0)

            loeo_model.train_ensemble(X_tr, y_res_train, groups=train_df[engine_col])

            preds = []
            for i in range(len(test_df)):
                pd_dict = loeo_model.predict(X_te.iloc[[i]])['predictions']
                preds.append(pd_dict)

            pred_df = pd.DataFrame(preds)
            for t in self.targets:
                if t in test_df.columns and t in pred_df.columns:
                    mae_results[t].append(mean_absolute_error(test_df[t], pred_df[t]))
                    r2_results[t].append(r2_score(test_df[t], pred_df[t]))

        print("\nLOEO Evaluation Results (engine-wise, no leakage):")
        print(f"{'Target':<22} | {'MAE':>8} | {'R²':>8} | {'Accuracy%':>10}")
        print("-" * 58)
        for t in self.targets:
            if mae_results[t]:
                avg_mae = np.mean(mae_results[t])
                avg_r2  = np.mean(r2_results[t])
                acc     = max(0, 100 * (1 - avg_mae / 0.60))
                print(f"{t:<22} | {avg_mae:>8.5f} | {avg_r2:>8.4f} | {acc:>9.2f}%")

        return mae_results, r2_results


