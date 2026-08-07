import numpy as np
import pandas as pd
import joblib
import logging
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_absolute_error, r2_score

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

logger = logging.getLogger(__name__)

class HybridPrognosticsModel:
    """
    Hybrid Prognostics Model combining physics-based first principles
    with a machine learning ensemble of residuals.
    """
    def __init__(self):
        self.targets = [
            'CompressorHealth', 'CombustorHealth', 'TurbineHealth',
            'OverallHealth', 'Thrust_N', 'TSFC_g_N_s'
        ]
        self.ensemble_models = {target: [] for target in self.targets}
        self.ensemble_weights = {target: [] for target in self.targets}
        self.features = None
        self.X_train_summary = None
        self.gamma = 1.4
        self.eps = 1e-9

    def _sigmoid(self, x, k=10, x0=0.5):
        """Smooth mapping to [0, 1] for health indicators"""
        return 1 / (1 + np.exp(-k * (x - x0)))

    def physics_predict(self, df):
        """
        Layer 1: Computes physics-derived health/performance from first principles.
        NO Cycle column is ever used here.
        """
        phys_preds = pd.DataFrame(index=df.index)
        
        # Thermaldynamic variables. Fallback to typical nominals if missing to prevent failure, 
        # but in a real scenario, these columns should exist in df.
        Tamb = df.get('Tamb', df.get('T1', 288.15))
        T2 = df.get('T2', 300.0)
        T3 = df.get('T3', 1000.0)
        T4 = df.get('T4', 800.0)
        P1 = df.get('P1', 1.0)
        P2 = df.get('P2', 10.0)
        Wf = df.get('Wf', df.get('FuelFlow', 1.0))
        
        PR = df.get('PR', P2 / (P1 + self.eps))
        
        # 1. Compressor isentropic efficiency proxy: eta_c = (T2_is - Tamb)/(T2 - Tamb)
        T2_is = Tamb * (PR ** ((self.gamma - 1) / self.gamma))
        eta_c = (T2_is - Tamb) / (T2 - Tamb + self.eps)
        phys_preds['CompressorHealth_phys'] = self._sigmoid(eta_c, k=5, x0=0.85)

        # 2. Combustor: TR = T3/T2, nominal ~5.5-7.5
        TR = T3 / (T2 + self.eps)
        # Lower TR maps to higher health usually, but depends on convention. 
        phys_preds['CombustorHealth_phys'] = self._sigmoid(TR, k=-2, x0=6.5) 

        # 3. Turbine: work coefficient W = (T3-T4)/T3, nominal ~0.45
        W = (T3 - T4) / (T3 + self.eps)
        phys_preds['TurbineHealth_phys'] = self._sigmoid(W, k=10, x0=0.45)

        # 4. Overall Health: Weighted average
        phys_preds['OverallHealth_phys'] = (
            0.35 * phys_preds['CompressorHealth_phys'] + 
            0.30 * phys_preds['CombustorHealth_phys'] + 
            0.35 * phys_preds['TurbineHealth_phys']
        )
        
        # 5. Thrust/TSFC phys proxies based on state
        phys_preds['Thrust_N_phys'] = Wf * (T3 - T4) * 100 
        phys_preds['TSFC_g_N_s_phys'] = Wf / (phys_preds['Thrust_N_phys'] + self.eps)

        return phys_preds

    def train_ensemble(self, X, y_residual, groups):
        """
        Layer 2: Trains Ridge + ElasticNet + GradientBoostingRegressor ensemble.
        Uses GroupKFold for validation. Weights = 1/RMSE^2.
        """
        # Exclude Cycle if present
        self.features = [col for col in X.columns if 'cycle' not in col.lower()]
        X_train = X[self.features]
        
        # For dataset density calculations
        self.X_train_summary = {
            'mean': X_train.mean(axis=0).values,
            'cov': np.cov(X_train.values, rowvar=False) + np.eye(len(self.features))*self.eps
        }
        
        gkf = GroupKFold(n_splits=10)
        
        for target in self.targets:
            y = y_residual[target]
            
            models = [
                Ridge(alpha=1.0),
                ElasticNet(alpha=0.1, l1_ratio=0.5),
                GradientBoostingRegressor(max_depth=5, n_estimators=200)
            ]
            
            target_models = []
            target_weights = []
            
            for model in models:
                rmses = []
                for train_idx, val_idx in gkf.split(X_train, y, groups):
                    X_tr, y_tr = X_train.iloc[train_idx], y.iloc[train_idx]
                    X_val, y_val = X_train.iloc[val_idx], y.iloc[val_idx]
                    
                    model.fit(X_tr, y_tr)
                    preds = model.predict(X_val)
                    mse = np.mean((preds - y_val)**2)
                    rmses.append(np.sqrt(mse))
                
                avg_rmse = np.mean(rmses)
                weight = 1.0 / (avg_rmse**2 + self.eps)
                
                # Retrain on full data
                model.fit(X_train, y)
                target_models.append(model)
                target_weights.append(weight)
                
            # Normalize weights
            total_weight = sum(target_weights)
            target_weights = [w / total_weight for w in target_weights]
            
            self.ensemble_models[target] = target_models
            self.ensemble_weights[target] = target_weights

    def physics_constraint_validate(self, pred_dict, telemetry_dict):
        """
        Layer 3: BIDIRECTIONAL constraint checker.
        """
        constrained_preds = pred_dict.copy()
        flagged = False
        
        if telemetry_dict is not None:
            T2 = telemetry_dict.get('T2')
            T3 = telemetry_dict.get('T3')
            T4 = telemetry_dict.get('T4')
            P2 = telemetry_dict.get('P2')
            P3 = telemetry_dict.get('P3')
            EGT = telemetry_dict.get('EGT')
            
            if T2 is not None and T3 is not None and T3 <= T2:
                flagged = True
                logger.warning(f"Constraint violated: T3 ({T3}) <= T2 ({T2})")
            
            if T3 is not None and T4 is not None and T4 >= T3:
                flagged = True
                logger.warning(f"Constraint violated: T4 ({T4}) >= T3 ({T3})")
                
            if P2 is not None and P3 is not None and P3 >= P2 * 1.05:
                flagged = True
                logger.warning(f"Constraint violated: P3 ({P3}) >= P2*1.05 ({P2*1.05})")
                
            if EGT is not None and EGT >= 1273:
                flagged = True
                logger.warning(f"Constraint violated: EGT ({EGT}) >= 1273K")
                
        # Clamp health variables
        for h_var in ['CompressorHealth', 'CombustorHealth', 'TurbineHealth', 'OverallHealth']:
            if h_var in constrained_preds:
                val = constrained_preds[h_var]
                if val < 0 or val > 1:
                    flagged = True
                    constrained_preds[h_var] = np.clip(val, 0, 1)
                    
        return constrained_preds, flagged

    def predict(self, X_temporal, engine_id=None, telemetry=None):
        """
        Runs all 3 layers, returns comprehensive dict.
        """
        # Layer 1: Physics
        phys_preds = self.physics_predict(X_temporal)
        
        features_to_use = [col for col in X_temporal.columns if col in self.features]
        X_ml = X_temporal[features_to_use]
        
        final_preds = {}
        epistemic_uncertainties = {}
        physics_uncertainties = {}
        ml_residuals = {}
        
        for target in self.targets:
            phys_col = f"{target}_phys"
            base_phys = phys_preds[phys_col].values[0] if phys_col in phys_preds else 0
            
            models = self.ensemble_models[target]
            weights = self.ensemble_weights[target]
            
            # Sub-model predictions
            sub_preds = [model.predict(X_ml)[0] for model in models]
            ensemble_residual = np.average(sub_preds, weights=weights)
            ml_residuals[target] = ensemble_residual
            
            final_pred = base_phys + ensemble_residual
            final_preds[target] = final_pred
            
            epistemic_uncertainties[target] = np.std(sub_preds)
            physics_uncertainties[target] = abs(base_phys - ensemble_residual)

        # Layer 3: Constraint Validate
        telemetry_dict = telemetry if telemetry is not None else X_temporal.iloc[0].to_dict()
        constrained_preds, flagged = self.physics_constraint_validate(final_preds, telemetry_dict)
        
        # Dataset density and extrapolation flag using Mahalanobis distance heuristic
        density = 0.0
        extrapolation = True
        if self.X_train_summary:
            mean = self.X_train_summary['mean']
            cov = self.X_train_summary['cov']
            diff = X_ml.values[0] - mean
            try:
                inv_cov = np.linalg.inv(cov)
                md = np.sqrt(np.dot(np.dot(diff, inv_cov), diff.T))
                # Heuristic: fraction within 2-std ball approximation
                density = np.exp(-0.5 * (md/2.0)**2)
                extrapolation = md > 2.0
            except np.linalg.LinAlgError:
                pass

        uncertainty = {
            'sensor_uncertainty': 0.02, # Estimated base uncertainty
            'physics_uncertainty': physics_uncertainties,
            'epistemic_uncertainty': epistemic_uncertainties,
            'dataset_density': density,
            'regime_uncertainty': 0.05,
            'extrapolation_flag': extrapolation
        }
        
        # Contribution percentages
        phys_contribs = {}
        ml_contribs = {}
        for target in self.targets:
            phys_val = abs(phys_preds.get(f"{target}_phys", pd.Series([0])).values[0])
            ml_val = abs(ml_residuals[target])
            total = phys_val + ml_val + self.eps
            phys_contribs[target] = phys_val / total
            ml_contribs[target] = ml_val / total

        return {
            'predictions': constrained_preds,
            'uncertainty': uncertainty,
            'physics_contribution_pct': phys_contribs,
            'ml_residual_contribution_pct': ml_contribs,
            'physics_constrained': flagged
        }

    def explain(self, X_row):
        """
        Returns explanations including SHAP values (if available) and top features.
        """
        pred_res = self.predict(X_row)
        
        shap_values_dict = {}
        top_features_dict = {}
        
        features_to_use = [col for col in X_row.columns if col in self.features]
        X_ml = X_row[features_to_use]
        
        if SHAP_AVAILABLE:
            for target in self.targets:
                # Use GBM sub-model (index 2)
                gbm_model = self.ensemble_models[target][2]
                explainer = shap.TreeExplainer(gbm_model)
                shap_vals = explainer.shap_values(X_ml)[0]
                shap_values_dict[target] = shap_vals
                
                # Rank features
                feature_importance = np.abs(shap_vals)
                ranked_indices = np.argsort(feature_importance)[::-1]
                top_features_dict[target] = [(features_to_use[i], float(feature_importance[i])) for i in ranked_indices]
        else:
            for target in self.targets:
                gbm_model = self.ensemble_models[target][2]
                importances = gbm_model.feature_importances_
                ranked_indices = np.argsort(importances)[::-1]
                top_features_dict[target] = [(features_to_use[i], float(importances[i])) for i in ranked_indices]
                shap_values_dict[target] = None
        
        return {
            'physics_contribution': pred_res['physics_contribution_pct'],
            'ml_residual_contribution': pred_res['ml_residual_contribution_pct'],
            'shap_values': shap_values_dict,
            'top_features': top_features_dict
        }

    def save(self, path):
        """Saves the trained model to disk."""
        joblib.dump(self, path)

    @classmethod
    def load(cls, path):
        """Loads a trained model from disk."""
        return joblib.load(path)


def evaluate_loeo(dataset_df, feature_engineer=None):
    """
    Leave-One-Engine-Out (LOEO) evaluation.
    Trains on 99 engines, tests on 1, rotates all 100.
    """
    if 'engine_id' not in dataset_df.columns:
        raise ValueError("dataset_df must contain 'engine_id' column for LOEO evaluation.")
        
    engine_ids = dataset_df['engine_id'].unique()
    
    if feature_engineer:
        dataset_df = feature_engineer(dataset_df)
        
    targets = [
        'CompressorHealth', 'CombustorHealth', 'TurbineHealth',
        'OverallHealth', 'Thrust_N', 'TSFC_g_N_s'
    ]
    
    mae_results = {t: [] for t in targets}
    r2_results = {t: [] for t in targets}
    
    for test_engine in engine_ids:
        train_df = dataset_df[dataset_df['engine_id'] != test_engine]
        test_df = dataset_df[dataset_df['engine_id'] == test_engine]
        
        model = HybridPrognosticsModel()
        
        y_train = train_df[targets]
        y_test = test_df[targets]
        
        # Calculate residuals for training
        phys_train = model.physics_predict(train_df)
        
        y_residual_train = pd.DataFrame(index=train_df.index)
        for t in targets:
            phys_col = f"{t}_phys"
            if phys_col in phys_train:
                y_residual_train[t] = y_train[t] - phys_train[phys_col]
            else:
                y_residual_train[t] = y_train[t]
                
        # ML features
        X_train = train_df.drop(columns=targets + ['engine_id'], errors='ignore')
        X_test = test_df.drop(columns=targets + ['engine_id'], errors='ignore')
        
        model.train_ensemble(X_train, y_residual_train, groups=train_df['engine_id'])
        
        preds = []
        for i in range(len(test_df)):
            X_row = X_test.iloc[[i]]
            telemetry = test_df.iloc[[i]].to_dict('records')[0]
            pred_dict = model.predict(X_row, telemetry=telemetry)['predictions']
            preds.append(pred_dict)
            
        preds_df = pd.DataFrame(preds)
        
        for t in targets:
            mae = mean_absolute_error(y_test[t], preds_df[t])
            r2 = r2_score(y_test[t], preds_df[t])
            mae_results[t].append(mae)
            r2_results[t].append(r2)
            
    print("LOEO Evaluation Results:")
    print(f"{'Target':<20} | {'MAE':<10} | {'R2':<10}")
    print("-" * 45)
    for t in targets:
        avg_mae = np.mean(mae_results[t])
        avg_r2 = np.mean(r2_results[t])
        print(f"{t:<20} | {avg_mae:<10.4f} | {avg_r2:<10.4f}")
        
    return mae_results, r2_results
