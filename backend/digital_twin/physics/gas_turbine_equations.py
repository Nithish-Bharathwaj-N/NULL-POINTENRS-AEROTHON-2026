import math
import numpy as np

class GasTurbinePhysicsEngine:
    """
    First-principles 4-stage turbojet aerothermodynamic model.
    Models inlet ram compression, 4-stage compressor, combustor energy balance,
    turbine work extraction, nozzle expansion, thrust, and TSFC.
    """

    GAMMA_AIR = 1.4
    GAMMA_GAS = 1.33
    CP_AIR = 1.005  # kJ/kg*K
    CP_GAS = 1.150  # kJ/kg*K
    LHV_FUEL = 43000.0  # kJ/kg (Jet-A)

    @classmethod
    def calculate_inlet_conditions(cls, alt_ft: float, mach: float, T_amb_c: float, P_amb_psi: float):
        """Calculates total ambient temperature (K) and total pressure (psi) after ram compression."""
        T_amb_k = T_amb_c + 273.15
        tau_r = 1.0 + 0.5 * (cls.GAMMA_AIR - 1.0) * (mach ** 2)
        pi_r = tau_r ** (cls.GAMMA_AIR / (cls.GAMMA_AIR - 1.0))
        
        Tt1_k = T_amb_k * tau_r
        Pt1_psi = P_amb_psi * pi_r
        return Tt1_k, Pt1_psi

    @classmethod
    def calculate_compressor_exit(cls, Tt1_k: float, Pt1_psi: float, P2_psi: float, compressor_health: float):
        """
        Calculates theoretical T2 and compressor efficiency based on health score.
        compressor_health: 0.0 to 100.0
        """
        base_eta_c = 0.88 * (compressor_health / 100.0)
        base_eta_c = max(0.60, min(0.92, base_eta_c))
        
        pi_c = max(1.0, P2_psi / max(0.1, Pt1_psi))
        tau_c_ideal = pi_c ** ((cls.GAMMA_AIR - 1.0) / cls.GAMMA_AIR)
        Tt2_k_ideal = Tt1_k * tau_c_ideal
        
        # Real temperature rise with efficiency
        Tt2_k_actual = Tt1_k + (Tt2_k_ideal - Tt1_k) / base_eta_c
        Tt2_c_actual = Tt2_k_actual - 273.15
        return Tt2_c_actual, base_eta_c

    @classmethod
    def calculate_combustor_exit(cls, Tt2_c: float, fuel_flow_kgh: float, combustor_health: float, air_flow_kgs: float = 25.0):
        """
        Calculates combustor exit temperature T3 (°C) and P3 (psi) based on fuel energy balance.
        """
        Tt2_k = Tt2_c + 273.15
        fuel_flow_kgs = (fuel_flow_kgh / 3600.0)
        
        combustor_eta = 0.99 * (combustor_health / 100.0)
        combustor_eta = max(0.70, min(0.995, combustor_eta))
        
        heat_added_kw = fuel_flow_kgs * cls.LHV_FUEL * combustor_eta
        gas_mass_flow = air_flow_kgs + fuel_flow_kgs
        
        delta_T = heat_added_kw / (gas_mass_flow * cls.CP_GAS)
        Tt3_k = Tt2_k + delta_T
        Tt3_c = Tt3_k - 273.15
        return Tt3_c, combustor_eta

    @classmethod
    def calculate_turbine_and_thrust(cls, Tt3_c: float, Tt2_c: float, P3_psi: float, turbine_health: float, mach: float, air_flow_kgs: float = 25.0):
        """
        Calculates T4, P4, Thrust (kN), and TSFC (g/kN*s).
        Work matching: Turbine work = Compressor work / mechanical_eta
        """
        Tt3_k = Tt3_c + 273.15
        Tt2_k = Tt2_c + 273.15
        
        turbine_eta = 0.90 * (turbine_health / 100.0)
        turbine_eta = max(0.65, min(0.94, turbine_eta))
        
        # Compressor power requirement (kW)
        W_comp = air_flow_kgs * cls.CP_AIR * (Tt2_k - 288.15)
        
        # Work balance to find T4
        W_turb_req = W_comp / 0.98  # mechanical efficiency
        delta_T_turb = W_turb_req / (air_flow_kgs * cls.CP_GAS * turbine_eta)
        
        Tt4_k = Tt3_k - delta_T_turb
        Tt4_c = Tt4_k - 273.15
        
        # Expansion pressure P4
        pi_t = (1.0 - (delta_T_turb / (Tt3_k * turbine_eta))) ** (cls.GAMMA_GAS / (cls.GAMMA_GAS - 1.0))
        P4_psi = P3_psi * pi_t
        
        # Choked Nozzle Exhaust Velocity (m/s)
        V_jet = math.sqrt(max(100.0, 2.0 * cls.CP_GAS * 1000.0 * Tt4_k * turbine_eta * (1.0 - (1.0 / max(1.1, P4_psi / 14.7)) ** ((cls.GAMMA_GAS - 1.0) / cls.GAMMA_GAS))))
        V_flight = mach * 340.3  # speed of sound approx
        
        net_thrust_n = max(500.0, air_flow_kgs * (V_jet - V_flight))
        thrust_kn = net_thrust_n / 1000.0
        
        # TSFC (g / kN * s)
        tsfc = (air_flow_kgs * 0.05 * 1000.0) / thrust_kn if thrust_kn > 0 else 65.0
        return Tt4_c, P4_psi, thrust_kn, tsfc
