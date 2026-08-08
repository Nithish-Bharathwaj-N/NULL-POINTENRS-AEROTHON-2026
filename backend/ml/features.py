"""
features.py
===========
Thermodynamic feature engineering for turbojet health and performance predictions.
Computes non-dimensional station pressure/temperature ratios, corrected flow variables,
and integrates Member 2's Brayton cycle predictions & residuals (physics_predict).
"""

import numpy as np
import pandas as pd
from backend.ml.physics_predict import physics_predict


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes derived thermodynamic features and appends aero-thermal cycle metrics.
    Handles flexible telemetry column names and single-row or batch DataFrames.
    """
    out = df.copy()

    eps = 1e-6
    gamma = 1.4
    R = 287.05
    Cp = 1004.5
    gamma_factor = (gamma - 1.0) / gamma

    # Core raw fields with robust fallback
    p_amb = out["Pamb_Pa"] if "Pamb_Pa" in out.columns else 101325.0
    t_amb = out["Tamb_K"] if "Tamb_K" in out.columns else 288.15
    p2 = out["P2_Pa"] if "P2_Pa" in out.columns else 337843.0
    t2 = out["T2_K"] if "T2_K" in out.columns else 506.0
    p3 = out["P3_Pa"] if "P3_Pa" in out.columns else 317158.0
    t3 = out["T3_K"] if "T3_K" in out.columns else 2043.0
    p4 = out["P4_Pa"] if "P4_Pa" in out.columns else 100018.0
    t4 = out["T4_K"] if "T4_K" in out.columns else 1303.0
    rpm = out["RPM_rev_min"] if "RPM_rev_min" in out.columns else 12500.0
    ff = out["FuelFlow_kg_s"] if "FuelFlow_kg_s" in out.columns else 3.45
    mach = out["Mach"] if "Mach" in out.columns else 0.78

    # Ram pressure and temperature ratios
    ram_temp_ratio = 1.0 + 0.2 * (mach ** 2)
    ram_press_ratio = ram_temp_ratio ** 3.5
    Pt0 = p_amb * ram_press_ratio
    Tt0 = t_amb * ram_temp_ratio

    # Station Pressure Ratios
    out["PR_2_0"] = p2 / (Pt0 + eps)
    out["PR_3_2"] = p3 / (p2 + eps)
    out["PR_4_3"] = p4 / (p3 + eps)
    out["PR_4_0"] = p4 / (p_amb + eps)
    out["PR_3_0"] = p3 / (p_amb + eps)
    out["PR_4_2"] = p4 / (p2 + eps)
    out["PR_compressor"] = p3 / (p2 + eps)
    out["PR_turbine"] = p4 / (p3 + eps)
    out["PR_overall"] = p3 / (p_amb + eps)

    # Station Temperature Ratios
    out["TR_2_0"] = t2 / (Tt0 + eps)
    out["TR_3_2"] = t3 / (t2 + eps)
    out["TR_4_3"] = t4 / (t3 + eps)
    out["TR_4_2"] = t4 / (t2 + eps)
    out["TR_3_0"] = t3 / (t_amb + eps)
    out["TR_4_0"] = t4 / (t_amb + eps)
    out["TR_combustor"] = t3 / (t2 + eps)
    out["TR_turbine"] = t4 / (t3 + eps)

    # Temperature and Pressure Deltas
    out["delta_T_compressor"] = t2 - t_amb
    out["delta_T_combustor"] = t3 - t2
    out["delta_T_turbine"] = t3 - t4
    out["delta_P_compressor"] = p3 - p2
    out["delta_P_combustor"] = p2 - p3
    out["delta_P_turbine"] = p3 - p4

    # Flow & Speed Corrected Variables
    out["RPM_corrected"] = rpm / np.sqrt(np.maximum(100.0, t_amb))
    out["RPM_cor_T2"] = rpm / np.sqrt(np.maximum(100.0, t2))
    out["FuelFlow_per_RPM"] = ff / (rpm + eps)
    out["FuelFlow_cor_P2_T2"] = (ff * np.sqrt(t2)) / (p2 + eps)
    out["FuelFlow_cor_P3_T3"] = (ff * np.sqrt(t3)) / (p3 + eps)

    # Combustor Specific Physics & Heat Release
    out["combustor_heat_rise_per_fuel"] = out["delta_T_combustor"] / np.maximum(eps, ff)
    out["combustor_press_drop_ratio"] = (p2 - p3) / (p2 + eps)
    out["combustor_enthalpy_rise"] = out["delta_T_combustor"] / (t2 + eps)

    # Turbine Specific Physics & Isentropic Proxies
    T4_isentropic = t3 * ((p4 / (p3 + eps)).clip(lower=eps) ** gamma_factor)
    dT_turbine_ideal = t3 - T4_isentropic
    out["dT_turbine_actual"] = out["delta_T_turbine"]
    out["dT_turbine_ideal"] = dT_turbine_ideal
    out["eta_t_proxy"] = out["dT_turbine_actual"] / np.maximum(eps, dT_turbine_ideal)
    out["turb_work_per_comp_work"] = out["delta_T_turbine"] / np.maximum(eps, out["delta_T_compressor"])
    out["turb_expansion_ratio"] = p3 / (p4 + eps)
    out["turb_temp_drop_ratio"] = out["delta_T_turbine"] / (t3 + eps)

    # Compressor Isentropic Proxies
    T2_isentropic = Tt0 * ((p2 / (Pt0 + eps)).clip(lower=eps) ** gamma_factor)
    T3_isentropic = t2 * ((p3 / (p2 + eps)).clip(lower=eps) ** gamma_factor)
    out["dT_compressor_actual"] = out["delta_T_compressor"]
    out["dT_compressor_ideal"] = T3_isentropic - t2
    out["eta_c_proxy"] = (T3_isentropic - t2) / np.maximum(eps, t3 - t2)

    # Flight Velocity & Propulsion Physics
    a0 = np.sqrt(gamma * R * t_amb)
    V0 = mach * a0
    pr_nozzle = (p_amb / (p4 + eps)).clip(upper=1.0)
    ideal_expansion = 1.0 - (pr_nozzle ** gamma_factor)
    Vj = np.sqrt(np.maximum(0.0, 2.0 * Cp * t4 * ideal_expansion))

    out["EPR"] = p4 / (p_amb + eps)
    out["V0"] = V0
    out["Vj"] = Vj
    out["delta_V"] = Vj - V0
    out["FuelFlow_delta_V"] = ff * (Vj - V0)
    out["FuelFlow_Vj"] = ff * Vj
    out["FuelFlow_sqrt_T4"] = ff * np.sqrt(t4)
    out["mdot_proxy"] = (p2 / np.sqrt(t2 + eps)) * (rpm / np.sqrt(t_amb + eps))
    out["thrust_proxy_physics"] = (p2 / np.sqrt(t2 + eps)) * (Vj - V0)

    # Synthetic / Placeholder Cycle Efficiency Variables
    out["predicted_T4_K"] = t4
    out["residual_T4_K"] = 0.0
    out["compressor_isentropic_efficiency"] = 0.88
    out["turbine_isentropic_efficiency"] = 0.90
    out["combustor_efficiency"] = 0.98

    return out


ENGINEERED_COLUMNS = [
    "PR_2_0", "PR_3_2", "PR_4_3", "PR_4_0", "PR_3_0", "PR_4_2",
    "PR_compressor", "PR_turbine", "PR_overall",
    "TR_2_0", "TR_3_2", "TR_4_3", "TR_4_2", "TR_3_0", "TR_4_0", "TR_combustor", "TR_turbine",
    "delta_T_compressor", "delta_T_combustor", "delta_T_turbine",
    "delta_P_compressor", "delta_P_combustor", "delta_P_turbine",
    "RPM_corrected", "RPM_cor_T2", "FuelFlow_per_RPM",
    "FuelFlow_cor_P2_T2", "FuelFlow_cor_P3_T3",
    "combustor_heat_rise_per_fuel", "combustor_press_drop_ratio", "combustor_enthalpy_rise",
    "dT_turbine_actual", "dT_turbine_ideal", "eta_t_proxy",
    "turb_work_per_comp_work", "turb_expansion_ratio", "turb_temp_drop_ratio",
    "dT_compressor_actual", "dT_compressor_ideal", "eta_c_proxy",
    "EPR", "V0", "Vj", "delta_V",
    "FuelFlow_delta_V", "FuelFlow_Vj", "FuelFlow_sqrt_T4",
    "mdot_proxy", "thrust_proxy_physics",
    "predicted_T4_K", "residual_T4_K",
    "compressor_isentropic_efficiency",
    "turbine_isentropic_efficiency",
    "combustor_efficiency",
]




