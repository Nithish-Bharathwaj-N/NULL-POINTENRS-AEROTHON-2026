import numpy as np
from .gas_turbine_equations import GasTurbinePhysicsEngine

class PhysicsValidator:
    """
    Compares raw engine telemetry & surrogate predictions against
    governing conservation laws (mass, momentum, energy).
    """

    @staticmethod
    def validate_telemetry_frame(telemetry: dict, predictions: dict):
        """
        Validates telemetry inputs and AI predictions against thermodynamic equations.
        Returns physics residual error, constraint loss, and energy balance metrics.
        """
        alt = float(telemetry.get("Altitude", 30000.0))
        mach = float(telemetry.get("Mach", 0.78))
        T_amb = float(telemetry.get("Ambient Temperature", -45.0))
        P_amb = float(telemetry.get("Ambient Pressure", 3.9))
        RPM = float(telemetry.get("RPM", 12500.0))
        fuel_flow = float(telemetry.get("Fuel Flow", 3.45))
        P2 = float(telemetry.get("Compressor Exit Pressure (P2)", 49.0))
        T2 = float(telemetry.get("Compressor Exit Temperature (T2)", 233.0))
        P3 = float(telemetry.get("Combustor Exit Pressure (P3)", 46.0))
        T3 = float(telemetry.get("Turbine Inlet Temperature (T3)", 1770.0))
        P4 = float(telemetry.get("Turbine Exit Pressure (P4)", 14.5))
        T4 = float(telemetry.get("Turbine Exit Temperature (T4)", 1030.0))

        comp_h = float(predictions.get("Compressor Health", 95.0))
        comb_h = float(predictions.get("Combustor Health", 95.0))
        turb_h = float(predictions.get("Turbine Health", 95.0))
        pred_thrust = float(predictions.get("Thrust", 54.0))
        pred_tsfc = float(predictions.get("TSFC", 63.0))

        Tt1_k, Pt1_psi = GasTurbinePhysicsEngine.calculate_inlet_conditions(alt, mach, T_amb, P_amb)
        calc_T2, comp_eta = GasTurbinePhysicsEngine.calculate_compressor_exit(Tt1_k, Pt1_psi, P2, comp_h)
        calc_T3, comb_eta = GasTurbinePhysicsEngine.calculate_combustor_exit(T2, fuel_flow * 3600.0, comb_h)
        calc_T4, calc_P4, calc_thrust, calc_tsfc = GasTurbinePhysicsEngine.calculate_turbine_and_thrust(T3, T2, P3, turb_h, mach)

        # Residual Errors
        res_T2 = abs(T2 - calc_T2) / max(1.0, calc_T2)
        res_T3 = abs(T3 - calc_T3) / max(1.0, calc_T3)
        res_T4 = abs(T4 - calc_T4) / max(1.0, calc_T4)
        res_thrust = abs(pred_thrust - calc_thrust) / max(1.0, calc_thrust)

        total_physics_residual = float(0.25 * (res_T2 + res_T3 + res_T4 + res_thrust))
        physics_constraint_loss = float(total_physics_residual ** 2)

        return {
            "physics_residual": round(total_physics_residual, 4),
            "physics_constraint_loss": round(physics_constraint_loss, 6),
            "theoretical_T2_C": round(calc_T2, 2),
            "theoretical_T3_C": round(calc_T3, 2),
            "theoretical_T4_C": round(calc_T4, 2),
            "theoretical_thrust_kN": round(calc_thrust, 2),
            "theoretical_tsfc": round(calc_tsfc, 2),
            "compressor_efficiency": round(comp_eta * 100.0, 2),
            "combustor_efficiency": round(comb_eta * 100.0, 2),
            "is_physics_compliant": bool(total_physics_residual < 0.15)
        }
