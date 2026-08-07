import numpy as np

class ResidualCalculator:
    """Calculates model prediction error metrics (RMSE, MAE, R2, residual vector)."""

    @staticmethod
    def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray):
        mae = float(np.mean(np.abs(y_true - y_pred)))
        rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = float(1.0 - (ss_res / (ss_tot + 1e-8)))

        return {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2_score": round(max(0.0, min(1.0, r2)), 4)
        }
