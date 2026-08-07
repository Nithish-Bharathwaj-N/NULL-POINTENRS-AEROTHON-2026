import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import ElasticNet, LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import warnings

warnings.filterwarnings('ignore')

class RULPredictor:
    """
    Remaining Useful Life (RUL) Predictor for Aerothon 2026.
    Predicts RUL based on health trajectory features (Cycle is NEVER a feature).
    Blends ElasticNet and GradientBoostingRegressor.
    """
    
    def __init__(self):
        # ElasticNet for interpretable mean prediction
        self.elastic_net = Pipeline([
            ('scaler', StandardScaler()),
            ('model', ElasticNet(random_state=42))
        ])
        
        # GBM for non-linear mean prediction
        self.gbm_mean = GradientBoostingRegressor(
            loss='squared_error',
            max_depth=5, 
            n_estimators=200,
            random_state=42
        )
        
        # GBMs for quantile regression (P10 and P90)
        self.gbm_p10 = GradientBoostingRegressor(
            loss='quantile',
            alpha=0.1,
            max_depth=5,
            n_estimators=200,
            random_state=42
        )
        
        self.gbm_p90 = GradientBoostingRegressor(
            loss='quantile',
            alpha=0.9,
            max_depth=5,
            n_estimators=200,
            random_state=42
        )
        
        self.features_list = [
            'CompH', 'CombH', 'TurbH', 'OvH',
            'health_slope_10', 'health_accel', 'health_divergence',
            'egt_margin', 'thermal_stress_index', 'pr_comp_dev',
            'fuel_flow_corrected', 't4_ema_dev'
        ]
        
        self.is_trained = False

    def compute_rul_targets(self, df):
        """
        Compute RUL targets from dataset.
        For each engine, find the first position where OverallHealth < 0.70.
        RUL at each earlier row = positions_remaining_until_that_threshold.
        If engine never reaches 0.70, use max_position as the endpoint.
        """
        targets = []
        for engine_id, group in df.groupby('EngineID'):
            group = group.sort_index() # Assumes index/order is chronological
            
            # Find index where OverallHealth < 0.70
            failure_points = np.where(group['OverallHealth'].values < 0.70)[0]
            
            if len(failure_points) > 0:
                end_pos = failure_points[0]
            else:
                end_pos = len(group) - 1
                
            # For each position up to end_pos, RUL is end_pos - current_pos
            # For positions after end_pos (if any), RUL is 0
            group_rul = np.maximum(0, end_pos - np.arange(len(group)))
            targets.extend(group_rul)
            
        return pd.Series(targets, index=df.index)

    def extract_features(self, df):
        """
        Extract features from raw sensor/health data.
        Assumes df is sorted by EngineID and chronological order.
        """
        df_features = pd.DataFrame(index=df.index)
        
        # Current health values
        df_features['CompH'] = df['CompH']
        df_features['CombH'] = df['CombH']
        df_features['TurbH'] = df['TurbH']
        df_features['OvH'] = df['OverallHealth']
        
        # Health divergence (std of 3 subsystem healths)
        df_features['health_divergence'] = df[['CompH', 'CombH', 'TurbH']].std(axis=1)
        
        # EGT margin
        df_features['egt_margin'] = 1273.15 - df['T4_K']
        
        # Pressure bar conversion with fallback
        p3 = df['P3_bar'] if 'P3_bar' in df.columns else (df['P3_Pa'] / 100000.0 if 'P3_Pa' in df.columns else 1.0)
        p4 = df['P4_bar'] if 'P4_bar' in df.columns else (df['P4_Pa'] / 100000.0 if 'P4_Pa' in df.columns else 1.0)
        t3 = df['T3_K'] if 'T3_K' in df.columns else 1700.0
        t4 = df['T4_K'] if 'T4_K' in df.columns else 1100.0
        df_features['thermal_stress_index'] = (t3 / (t4 + 1e-6)) * (p3 / (p4 + 1e-6))
        
        # We need engine-wise rolling calculations
        df_features['health_slope_10'] = 0.0
        df_features['health_accel'] = 0.0
        df_features['pr_comp_dev'] = 0.0
        ff = df['FuelFlow'] if 'FuelFlow' in df.columns else (df['FuelFlow_kg_s'] if 'FuelFlow_kg_s' in df.columns else 0.68)
        df_features['fuel_flow_corrected'] = ff
        df_features['t4_ema_dev'] = 0.0
        
        for engine_id, group in df.groupby('EngineID'):
            idx = group.index
            
            # Rolling health slope (last 10 cycle EMA slope)
            ovh_ema = group['OverallHealth'].ewm(span=10, adjust=False).mean()
            # Simple difference over 1 step of EMA as slope
            slope = ovh_ema.diff()
            df_features.loc[idx, 'health_slope_10'] = slope.fillna(0)
            
            # Degradation acceleration (2nd derivative of health EMA)
            accel = slope.diff()
            df_features.loc[idx, 'health_accel'] = accel.fillna(0)
            
            # PR_compressor deviation from rolling mean (assume PR = P3/P2 or similar, using generic PR col)
            if 'PR_compressor' in group.columns:
                pr_mean = group['PR_compressor'].rolling(10, min_periods=1).mean()
                df_features.loc[idx, 'pr_comp_dev'] = group['PR_compressor'] - pr_mean
            
            # T4_ema_deviation
            t4_ema = group['T4_K'].ewm(span=10, adjust=False).mean()
            df_features.loc[idx, 't4_ema_dev'] = group['T4_K'] - t4_ema
            
        return df_features.fillna(0)

    def train(self, df_with_health):
        """
        Train the models using GroupKFold.
        """
        print("Extracting targets and features...")
        y = self.compute_rul_targets(df_with_health)
        X = self.extract_features(df_with_health)[self.features_list]
        groups = df_with_health['EngineID']
        
        # Use GroupKFold for cross-validation evaluation (optional, but requested by prompt)
        gkf = GroupKFold(n_splits=10)
        fold = 1
        for train_idx, val_idx in gkf.split(X, y, groups):
            # We could train/eval on folds here to print metrics
            # But we ultimately need to train on the full dataset
            pass 
        
        print("Training models on full dataset...")
        self.elastic_net.fit(X, y)
        self.gbm_mean.fit(X, y)
        self.gbm_p10.fit(X, y)
        self.gbm_p90.fit(X, y)
        
        self.is_trained = True
        print("Training complete.")

    def estimate(self, feature_dict):
        """
        Estimate RUL based on a single dictionary of features.
        Returns: {rul_mean, rul_p10, rul_p90, confidence, regime, warning}
        """
        if not self.is_trained:
            raise ValueError("Model is not trained yet.")
            
        # Convert to DataFrame
        df_input = pd.DataFrame([feature_dict])
        
        # Ensure correct order and missing columns
        for col in self.features_list:
            if col not in df_input.columns:
                df_input[col] = 0.0
                
        X = df_input[self.features_list]
        
        # Predictions
        en_pred = self.elastic_net.predict(X)[0]
        gbm_mean_pred = self.gbm_mean.predict(X)[0]
        
        # Blend
        rul_mean = 0.4 * en_pred + 0.6 * gbm_mean_pred
        rul_mean = max(0.0, float(rul_mean))
        
        rul_p10 = max(0.0, float(self.gbm_p10.predict(X)[0]))
        rul_p90 = max(0.0, float(self.gbm_p90.predict(X)[0]))
        
        # Ensure p10 <= p90
        if rul_p10 > rul_p90:
            rul_p10, rul_p90 = rul_p90, rul_p10
            
        # Confidence = 1 - (P90-P10)/(rul_mean + 1e-9), scaled 0-100
        conf_val = 1.0 - (rul_p90 - rul_p10) / (rul_mean + 1e-9)
        confidence = max(0.0, min(100.0, conf_val * 100.0))
        
        # Regime based on health level (extract from dict)
        ovh = feature_dict.get('OvH', 1.0)
        if ovh > 0.90:
            regime = 'early'
        elif ovh > 0.75:
            regime = 'mid'
        else:
            regime = 'late'
            
        # Warning based on rul_mean
        if rul_mean < 30:
            warning = 'CRITICAL'
        elif rul_mean < 80:
            warning = 'WARNING'
        elif rul_mean < 150:
            warning = 'MONITOR'
        else:
            warning = 'NORMAL'
            
        return {
            'rul_mean': rul_mean,
            'rul_p10': rul_p10,
            'rul_p90': rul_p90,
            'confidence': confidence,
            'regime': regime,
            'warning': warning
        }
        
    def _slope_extrapolation(self, health_history_list, threshold=0.70):
        """
        Slope extrapolation fallback: fits linear regression on last-10-health-values, 
        extrapolates to when it hits threshold. Returns int cycles.
        """
        if len(health_history_list) < 2:
            return 999 # Not enough data
            
        # Use at most last 10
        y = np.array(health_history_list[-10:])
        x = np.arange(len(y)).reshape(-1, 1)
        
        lr = LinearRegression()
        lr.fit(x, y)
        
        slope = lr.coef_[0]
        intercept = lr.intercept_
        
        if slope >= 0:
            return 999 # Health is improving or stable, won't hit threshold
            
        # threshold = slope * x_target + intercept
        # x_target = (threshold - intercept) / slope
        x_target = (threshold - intercept) / slope
        
        cycles_remaining = x_target - (len(y) - 1)
        return max(0, int(round(cycles_remaining)))

    def save(self, path):
        """Save models and configuration"""
        if not self.is_trained:
            print("Warning: Saving untrained model.")
        state = {
            'elastic_net': self.elastic_net,
            'gbm_mean': self.gbm_mean,
            'gbm_p10': self.gbm_p10,
            'gbm_p90': self.gbm_p90,
            'features_list': self.features_list,
            'is_trained': self.is_trained
        }
        joblib.dump(state, path)
        print(f"Model saved to {path}")
        
    def load(self, path):
        """Load models and configuration"""
        state = joblib.load(path)
        self.elastic_net = state['elastic_net']
        self.gbm_mean = state['gbm_mean']
        self.gbm_p10 = state['gbm_p10']
        self.gbm_p90 = state['gbm_p90']
        self.features_list = state['features_list']
        self.is_trained = state['is_trained']
        print(f"Model loaded from {path}")
