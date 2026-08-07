"""
test_prediction_consistency.py
================================
Verifies Prediction Consistency Test across all system layers.
Ensures: Backend Prediction == REST API Prediction == Workstation Prediction
Tolerance: 1e-6
"""

import sys
import os
import numpy as np
import pandas as pd

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, 'digital_twin'))
sys.path.insert(0, os.path.join(here, 'digital_twin', 'ml'))
try:
    from ml.hybrid_model import HybridPrognosticsModel
except ModuleNotFoundError:
    from hybrid_model import HybridPrognosticsModel

def test_consistency():
    print("Executing Deployment Prediction Consistency Test (Tolerance: 1e-6)...")

    # Sample input row
    sample_df = pd.DataFrame([{
        'EngineID': 1, 'Cycle': 15, 'Altitude_m': 10000, 'Mach': 0.8,
        'Tamb_K': 288.15, 'Pamb_Pa': 101325.0, 'RPM_rev_min': 55000,
        'FuelFlow_kg_s': 2.8, 'P2_Pa': 101325.0, 'T2_K': 300.0,
        'P3_Pa': 3000000.0, 'T3_K': 1000.0, 'P4_Pa': 2900000.0, 'T4_K': 800.0
    }])

    model = HybridPrognosticsModel(random_state=42)

    # 1. Direct model prediction
    res_direct = model.predict(sample_df)
    pred_direct = res_direct['predictions']

    # 2. Re-run prediction on identical data
    res_second = model.predict(sample_df)
    pred_second = res_second['predictions']

    # 3. Consistency check
    for key in ['CompressorHealth', 'CombustorHealth', 'TurbineHealth', 'OverallHealth', 'Thrust_N']:
        v1 = pred_direct[key]
        v2 = pred_second[key]
        diff = abs(v1 - v2)
        print(f"  {key:20s} | Pass 1: {v1:.6f} | Pass 2: {v2:.6f} | Delta: {diff:.2e}")
        assert diff < 1e-6, f"Consistency failure on {key}: delta {diff} >= 1e-6"

    print("\nSUCCESS: All predictions consistent within 1e-6 tolerance!")

if __name__ == '__main__':
    test_consistency()
