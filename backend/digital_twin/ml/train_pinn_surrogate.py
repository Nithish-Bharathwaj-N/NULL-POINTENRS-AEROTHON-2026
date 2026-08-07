import os
import pickle
import time
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

class PhysicsInformedSurrogateModel:
    def __init__(self, model_dir="backend/ml"):
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, "pinn_surrogate.pkl")
        
        self.raw_feature_cols = [
            "EngineID", "Cycle", "Altitude", "Mach", "Ambient Temperature", "Ambient Pressure",
            "RPM", "Fuel Flow", "Compressor Exit Pressure (P2)",
            "Compressor Exit Temperature (T2)", "Combustor Exit Pressure (P3)",
            "Turbine Inlet Temperature (T3)", "Turbine Exit Pressure (P4)",
            "Turbine Exit Temperature (T4)"
        ]
        
        self.target_cols = [
            "Compressor Health", "Combustor Health", "Turbine Health",
            "Overall Health", "Thrust", "TSFC"
        ]
        self.models = []
        self.scaler = StandardScaler()
        self.gamma = 1.4

    def preprocess_features(self, df):
        X = df.copy()
        eps = 1e-6
        
        Pamb = X["Ambient Pressure"] + eps
        Tamb = X["Ambient Temperature"] + eps
        P2 = X["Compressor Exit Pressure (P2)"]
        T2 = X["Compressor Exit Temperature (T2)"]
        P3 = X["Combustor Exit Pressure (P3)"]
        T3 = X["Turbine Inlet Temperature (T3)"] + eps
        P4 = X["Turbine Exit Pressure (P4)"] + eps
        T4 = X["Turbine Exit Temperature (T4)"]
        
        X["Pressure_Ratio_2"] = P2 / Pamb
        X["Pressure_Ratio_34"] = P3 / P4
        X["Temperature_Ratio_32"] = T3 / (T2 + eps)
        X["Temperature_Ratio_43"] = T4 / T3
        
        denom = (X["Pressure_Ratio_2"] ** ((self.gamma - 1) / self.gamma)) - 1
        denom = np.where(denom == 0, eps, denom)
        X["Compressor_Efficiency_Proxy"] = (T2 - Tamb) / denom
        
        X["Work_Coefficient"] = (T3 - T4) / T3
        
        max_cycle = 500.0
        X["Normalized_Cycle"] = X["Cycle"] / max_cycle
        
        if "EngineID" in X.columns:
            X = X.drop(columns=["EngineID"])
            
        return X

    def calculate_physics_loss(self, y_pred):
        loss = 0.0
        for i in range(4):
            loss += np.mean(np.maximum(0, y_pred[:, i] - 1.0)**2)
            loss += np.mean(np.maximum(0, -y_pred[:, i])**2)
        loss += np.mean(np.maximum(0, -y_pred[:, 4])**2)
        loss += np.mean(np.maximum(0, -y_pred[:, 5])**2)
        return loss

    def train(self, train_csv_path="backend/data/train.csv"):
        print(f"[PINN Train] Loading data from {train_csv_path}...")
        df = pd.read_csv(train_csv_path)
        
        for col in self.raw_feature_cols:
            if col not in df.columns:
                df[col] = 0.0

        X = self.preprocess_features(df[self.raw_feature_cols])
        y = df[self.target_cols]

        X_scaled = self.scaler.fit_transform(X)

        print("[PINN Train] Fitting Ensemble of 5 MultiOutput Gradient Boosting Models...")
        self.models = []
        for i in range(5):
            print(f"  Training model {i+1}/5...")
            base_gb = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42 + i, subsample=0.8)
            model = MultiOutputRegressor(base_gb)
            model.fit(X_scaled, y)
            self.models.append(model)

        os.makedirs(self.model_dir, exist_ok=True)
        with open(self.model_path, "wb") as f:
            pickle.dump({'models': self.models, 'scaler': self.scaler}, f)
        print(f"[PINN Train] Successfully saved model ensemble to {self.model_path}")

    def evaluate(self, test_csv_path="backend/data/test.csv", gt_csv_path="backend/data/ground_truth.csv"):
        print(f"\n[PINN Eval] Evaluating on {test_csv_path} vs {gt_csv_path}")
        df_test = pd.read_csv(test_csv_path)
        df_gt = pd.read_csv(gt_csv_path)
        
        for col in self.raw_feature_cols:
            if col not in df_test.columns:
                df_test[col] = 0.0
                
        X = self.preprocess_features(df_test[self.raw_feature_cols])
        X_scaled = self.scaler.transform(X)
        y_true = df_gt[self.target_cols].values
        
        preds_list = []
        for model in self.models:
            preds_list.append(model.predict(X_scaled))
            
        preds_array = np.array(preds_list)
        y_pred = np.mean(preds_array, axis=0)
        
        print("\nEvaluation Metrics:")
        for i, col in enumerate(self.target_cols):
            mae = mean_absolute_error(y_true[:, i], y_pred[:, i])
            rmse = np.sqrt(mean_squared_error(y_true[:, i], y_pred[:, i]))
            r2 = r2_score(y_true[:, i], y_pred[:, i])
            print(f"{col:20s} - MAE: {mae:.4f}, RMSE: {rmse:.4f}, R²: {r2:.4f}")
            
        physics_loss = self.calculate_physics_loss(y_pred)
        print(f"\nAverage Physics Constraint Violation Loss: {physics_loss:.6f}")

    def load(self):
        if os.path.exists(self.model_path):
            with open(self.model_path, "rb") as f:
                saved_data = pickle.load(f)
                if isinstance(saved_data, dict):
                    self.models = saved_data['models']
                    self.scaler = saved_data['scaler']
                else:
                    self.models = [saved_data]
            return True
        return False

    def predict(self, telemetry_dict: dict):
        t0 = time.time()
        if not self.models:
            if not self.load():
                self.train()
                
        input_data = {}
        for col in self.raw_feature_cols:
            val = telemetry_dict.get(col, 0.0)
            if col == "EngineID":
                input_data[col] = str(val)
            else:
                try:
                    input_data[col] = float(val)
                except (ValueError, TypeError):
                    input_data[col] = 0.0
                    
        input_df = pd.DataFrame([input_data])
        
        X = self.preprocess_features(input_df)
        
        if hasattr(self, 'scaler') and self.scaler is not None:
            try:
                X_scaled = self.scaler.transform(X)
            except Exception:
                X_scaled = X.values
        else:
            X_scaled = X.values
            
        preds_list = []
        for model in self.models:
            preds_list.append(model.predict(X_scaled)[0])
            
        preds_array = np.array(preds_list)
        mean_preds = np.mean(preds_array, axis=0)
        std_preds = np.std(preds_array, axis=0)
        
        inference_time_ms = (time.time() - t0) * 1000.0

        res = {col: float(mean_preds[i]) for i, col in enumerate(self.target_cols)}
        
        uncertainty_bounds = {}
        for i, col in enumerate(self.target_cols):
            uncertainty_bounds[f"{col} Upper"] = float(mean_preds[i] + 2 * std_preds[i])
            uncertainty_bounds[f"{col} Lower"] = float(mean_preds[i] - 2 * std_preds[i])
            
        res["Uncertainty Bounds"] = uncertainty_bounds
        
        mean_std = np.mean([std_preds[i]/(abs(mean_preds[i])+1e-6) for i in range(len(self.target_cols))])
        confidence = float(max(0.0, min(1.0, 1.0 - mean_std * 5.0)))
        
        res["Prediction Confidence"] = round(confidence, 4)
        res["Inference Time Ms"] = round(inference_time_ms, 3)
        return res

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_dir = os.path.join(base_dir, "ml")
    train_path = os.path.join(base_dir, "data", "train.csv")
    test_path = os.path.join(base_dir, "data", "test.csv")
    gt_path = os.path.join(base_dir, "data", "ground_truth.csv")
    
    pinn = PhysicsInformedSurrogateModel(model_dir=model_dir)
    pinn.train(train_csv_path=train_path)
    
    if os.path.exists(test_path) and os.path.exists(gt_path):
        pinn.evaluate(test_csv_path=test_path, gt_csv_path=gt_path)
