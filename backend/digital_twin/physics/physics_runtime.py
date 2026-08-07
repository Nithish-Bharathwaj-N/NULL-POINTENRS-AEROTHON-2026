"""
AEROTWIN Ω — 10-Level Physics Runtime
======================================
Every visible behavior in the Digital Twin traces to this physics stack.
This is NOT CFD. This is NOT FEA. This is a physics-informed visualization
runtime driven by telemetry and simplified engineering models.

Architecture:
    Telemetry → PhysicsRuntime.step() → EnginePhysicsState → Renderers

Layers:
    1. Mechanical   — Shaft dynamics, torque, inertia, friction
    2. Fluid        — Approximate flow velocities, compression, expansion
    3. Thermal      — Per-component heat transfer, thermal inertia
    4. Combustion   — Flame intensity, efficiency, zones
    5. Fuel         — Spray physics, injector state
    6. Pressure     — P2/P3/P4 gradients, ratios
    7. Health       — Per-subsystem degradation effects
    8. Wear         — Accumulated structural degradation
    9. Vibration    — Multi-mode vibration model
   10. Lifecycle    — Cycle-driven ageing
"""

import math
import time


class ComponentThermalState:
    """Per-component thermal model with thermal inertia."""

    def __init__(self, name, thermal_capacity, ambient_temp=20.0):
        self.name = name
        self.temperature = ambient_temp
        self.target_temperature = ambient_temp
        self.thermal_capacity = thermal_capacity  # seconds to reach 63% of target
        self.heating_rate = 0.0  # °C/s current rate
        self.ambient = ambient_temp

    def step(self, target_temp, dt, adjacent_temps=None):
        """Update temperature with thermal inertia and conduction from neighbors."""
        self.target_temperature = target_temp

        # Primary drive: approach target with thermal inertia
        delta = target_temp - self.temperature
        rate = delta / max(self.thermal_capacity, 0.1)

        # Conductive coupling from adjacent components (simplified)
        if adjacent_temps:
            for adj_t in adjacent_temps:
                conduction = (adj_t - self.temperature) * 0.02  # weak coupling
                rate += conduction

        self.heating_rate = rate
        self.temperature += rate * dt
        return self.temperature


class MechanicalState:
    """Level 1: Single-spool shaft dynamics."""

    def __init__(self):
        self.omega = 0.0          # rad/s (angular velocity)
        self.omega_target = 0.0
        self.alpha = 0.0          # rad/s² (angular acceleration)
        self.rpm = 0.0
        self.target_rpm = 0.0
        self.moment_of_inertia = 8.5   # kg·m² (approximate for small turbojet)
        self.torque_turbine = 0.0      # N·m
        self.torque_compressor = 0.0   # N·m
        self.torque_friction = 0.0     # N·m
        self.torque_net = 0.0          # N·m
        self.bearing_friction_coeff = 0.002
        self.rotor_imbalance = 0.0     # 0 to 1

    def step(self, target_rpm, health_pct, dt):
        self.target_rpm = target_rpm
        self.omega_target = target_rpm * 2 * math.pi / 60

        # Approximate torque balance
        self.torque_turbine = self.omega_target * 0.85      # driving torque
        self.torque_compressor = self.omega * 0.75           # load torque
        self.torque_friction = self.omega * self.bearing_friction_coeff * (1 + (100 - health_pct) / 50)

        self.torque_net = self.torque_turbine - self.torque_compressor - self.torque_friction
        self.alpha = self.torque_net / self.moment_of_inertia

        # Integrate angular velocity with inertia
        self.omega += self.alpha * dt * 0.3  # damped integration
        self.omega = max(self.omega, 0)
        self.rpm = self.omega * 60 / (2 * math.pi)

        # Rotor imbalance increases with health degradation
        self.rotor_imbalance = max(0, (100 - health_pct) / 100) * 0.8

        return self.rpm


class FluidState:
    """Level 2: Approximate flow velocities (NOT CFD)."""

    def __init__(self):
        self.intake_velocity = 0.0        # m/s
        self.compressor_exit_velocity = 0.0
        self.diffuser_exit_velocity = 0.0
        self.turbine_exit_velocity = 0.0
        self.exhaust_velocity = 0.0
        self.compression_ratio = 1.0
        self.expansion_ratio = 1.0
        self.mass_flow_rate = 0.0         # kg/s

    def step(self, rpm, mach, altitude, P2, P3, P4, thrust):
        rpm_norm = min(rpm / 12500, 1.0)
        ambient_P = max(14.7 * math.exp(-altitude / 27000), 3.5)

        self.intake_velocity = mach * 340 * 0.3 + rpm_norm * 120
        self.compressor_exit_velocity = self.intake_velocity * 0.6  # velocity decreases, pressure rises
        self.diffuser_exit_velocity = self.compressor_exit_velocity * 0.4
        self.turbine_exit_velocity = self.diffuser_exit_velocity * 1.8  # expansion
        self.exhaust_velocity = max(thrust * 18, 50) * rpm_norm

        self.compression_ratio = max(P2 / ambient_P, 1.0) if ambient_P > 0 else 1.0
        self.expansion_ratio = max(P3 / max(P4, 1.0), 1.0)
        self.mass_flow_rate = rpm_norm * 28.0  # approximate kg/s for small turbojet


class CombustionState:
    """Level 4: Simplified combustion physics."""

    def __init__(self):
        self.flame_intensity = 0.0         # 0 to 1
        self.combustion_efficiency = 0.0   # 0 to 1
        self.heat_release_rate = 0.0       # MW
        self.primary_zone_intensity = 0.0
        self.secondary_zone_intensity = 0.0
        self.dilution_zone_intensity = 0.0
        self.ignition_active = False
        self.flame_stable = False

    def step(self, fuel_flow, T3, combustor_health, rpm):
        rpm_norm = min(rpm / 12500, 1.0)
        fuel_norm = min(fuel_flow / 3.5, 1.0)
        t3_norm = max(0, (T3 - 200) / 1600)
        health_factor = combustor_health / 100

        self.flame_intensity = fuel_norm * t3_norm * health_factor
        self.combustion_efficiency = 0.985 * health_factor * min(rpm_norm + 0.1, 1.0)
        self.heat_release_rate = fuel_flow * 43.0 * self.combustion_efficiency  # MJ/kg * kg/s

        self.primary_zone_intensity = self.flame_intensity * 1.0
        self.secondary_zone_intensity = self.flame_intensity * 0.7
        self.dilution_zone_intensity = self.flame_intensity * 0.3

        self.ignition_active = fuel_flow > 0.5 and T3 > 100
        self.flame_stable = fuel_flow > 1.0 and T3 > 350 and rpm > 3000


class FuelSystemState:
    """Level 5: Fuel system simulation."""

    def __init__(self):
        self.pump_pressure = 0.0        # psi
        self.manifold_pressure = 0.0
        self.injector_pressure = 0.0
        self.spray_cone_angle = 0.0     # degrees
        self.droplet_density = 0.0      # 0 to 1
        self.spray_velocity = 0.0       # m/s
        self.injector_health = 100.0    # %

    def step(self, fuel_flow, rpm, overall_health):
        rpm_norm = min(rpm / 12500, 1.0)
        fuel_norm = min(fuel_flow / 3.5, 1.0)

        self.pump_pressure = fuel_norm * 850  # psi
        self.manifold_pressure = self.pump_pressure * 0.95
        self.injector_pressure = self.manifold_pressure * 0.90
        self.spray_cone_angle = 60 + fuel_norm * 20  # 60° to 80°
        self.droplet_density = fuel_norm
        self.spray_velocity = fuel_norm * 45 + 5  # m/s
        self.injector_health = overall_health * 0.98


class PressureState:
    """Level 6: Pressure physics."""

    def __init__(self):
        self.P_ambient = 14.7
        self.P2 = 14.7
        self.P3 = 14.7
        self.P4 = 14.7
        self.compressor_pressure_ratio = 1.0
        self.turbine_pressure_ratio = 1.0
        self.pressure_gradient_comp = 0.0    # psi/stage
        self.pressure_gradient_turb = 0.0

    def step(self, P2, P3, P4, altitude):
        self.P_ambient = max(14.7 * math.exp(-altitude / 27000), 3.5)
        self.P2 = P2
        self.P3 = P3
        self.P4 = P4
        self.compressor_pressure_ratio = P2 / max(self.P_ambient, 0.1)
        self.turbine_pressure_ratio = P3 / max(P4, 0.1)
        self.pressure_gradient_comp = (P2 - self.P_ambient) / 6  # across 6 compressor stages
        self.pressure_gradient_turb = (P3 - P4) / 4  # across 4 turbine stages


class VibrationState:
    """Level 9: Multi-mode vibration model."""

    def __init__(self):
        self.rotor_imbalance_amplitude = 0.0
        self.bearing_vibration_amplitude = 0.0
        self.shaft_oscillation_amplitude = 0.0
        self.housing_vibration_amplitude = 0.0
        self.total_amplitude = 0.0
        self.dominant_frequency = 0.0  # Hz

    def step(self, rpm, overall_health, compressor_health, turbine_health):
        rpm_norm = min(rpm / 12500, 1.0)
        health_degradation = (100 - overall_health) / 100
        comp_degradation = (100 - compressor_health) / 100
        turb_degradation = (100 - turbine_health) / 100

        self.rotor_imbalance_amplitude = rpm_norm * 0.0003 + health_degradation * 0.004
        self.bearing_vibration_amplitude = rpm_norm * 0.0002 + health_degradation * 0.003
        self.shaft_oscillation_amplitude = rpm_norm * 0.0001 + comp_degradation * 0.002
        self.housing_vibration_amplitude = rpm_norm * 0.00015 + turb_degradation * 0.0015

        self.total_amplitude = (
            self.rotor_imbalance_amplitude +
            self.bearing_vibration_amplitude +
            self.shaft_oscillation_amplitude +
            self.housing_vibration_amplitude
        )
        self.dominant_frequency = rpm / 60  # 1x shaft frequency


class WearState:
    """Level 8: Accumulated structural wear."""

    def __init__(self):
        self.carbon_deposit = 0.0       # 0 to 1
        self.blade_oxidation = 0.0
        self.thermal_discoloration = 0.0
        self.surface_roughness = 0.0
        self.soot_accumulation = 0.0
        self.erosion = 0.0

    def step(self, cycle, max_cycle=300):
        age = min(cycle / max_cycle, 1.0)
        self.carbon_deposit = age * 0.8
        self.blade_oxidation = age * 0.6
        self.thermal_discoloration = age * 0.7
        self.surface_roughness = 0.18 + age * 0.35
        self.soot_accumulation = age * 0.5
        self.erosion = age * 0.4


class EnginePhysicsState:
    """Complete physics state output for rendering."""

    def __init__(self):
        self.mechanical = {}
        self.fluid = {}
        self.thermal = {}
        self.combustion = {}
        self.fuel_system = {}
        self.pressure = {}
        self.health = {}
        self.wear = {}
        self.vibration = {}
        self.lifecycle = {}

    def to_dict(self):
        return {
            "mechanical": self.mechanical,
            "fluid": self.fluid,
            "thermal": self.thermal,
            "combustion": self.combustion,
            "fuel_system": self.fuel_system,
            "pressure": self.pressure,
            "health": self.health,
            "wear": self.wear,
            "vibration": self.vibration,
            "lifecycle": self.lifecycle,
        }


class PhysicsRuntime:
    """
    10-Level Physics Runtime for the AEROTWIN Ω Digital Twin.

    Called every telemetry frame. Computes all physics layers in order.
    Output is a complete EnginePhysicsState consumed by all renderers.

    This is a physics-INFORMED visualization runtime, NOT a full CFD/FEA solver.
    """

    def __init__(self):
        self.mechanical = MechanicalState()
        self.fluid = FluidState()
        self.combustion = CombustionState()
        self.fuel_system = FuelSystemState()
        self.pressure = PressureState()
        self.vibration = VibrationState()
        self.wear = WearState()

        # Per-component thermal states (Level 3)
        self.thermal_components = {
            "intake":    ComponentThermalState("Intake",    15.0),
            "fan":       ComponentThermalState("Fan",       12.0),
            "lpc_1":     ComponentThermalState("LPC_1",     10.0),
            "lpc_2":     ComponentThermalState("LPC_2",     10.0),
            "lpc_3":     ComponentThermalState("LPC_3",     10.0),
            "hpc_1":     ComponentThermalState("HPC_1",     8.0),
            "hpc_2":     ComponentThermalState("HPC_2",     8.0),
            "hpc_3":     ComponentThermalState("HPC_3",     8.0),
            "diffuser":  ComponentThermalState("Diffuser",  9.0),
            "combustor": ComponentThermalState("Combustor", 5.0),
            "hpt_1":     ComponentThermalState("HPT_1",     6.0),
            "hpt_2":     ComponentThermalState("HPT_2",     6.0),
            "lpt_1":     ComponentThermalState("LPT_1",     7.0),
            "lpt_2":     ComponentThermalState("LPT_2",     7.0),
            "exhaust":   ComponentThermalState("Exhaust",   10.0),
            "nozzle":    ComponentThermalState("Nozzle",    11.0),
            "shaft":     ComponentThermalState("Shaft",     14.0),
            "bearings":  ComponentThermalState("Bearings",  12.0),
        }

        self._last_time = time.time()

    def step(self, telemetry: dict, predictions: dict) -> dict:
        """
        Execute one full physics frame across all 10 layers.

        Args:
            telemetry: Raw telemetry dict from dataset
            predictions: PINN health predictions

        Returns:
            Complete physics state dict for rendering
        """
        now = time.time()
        dt = min(now - self._last_time, 0.5)  # cap dt
        self._last_time = now

        rpm = telemetry.get("RPM", 0)
        fuel_flow = telemetry.get("Fuel Flow", 0)
        P2 = telemetry.get("Compressor Exit Pressure (P2)", 14.7)
        T2 = telemetry.get("Compressor Exit Temperature (T2)", 20)
        P3 = telemetry.get("Combustor Exit Pressure (P3)", 14.7)
        T3 = telemetry.get("Turbine Inlet Temperature (T3)", 20)
        P4 = telemetry.get("Turbine Exit Pressure (P4)", 14.7)
        T4 = telemetry.get("Turbine Exit Temperature (T4)", 20)
        cycle = telemetry.get("Cycle", 1)
        altitude = telemetry.get("Altitude", 30000)
        mach = telemetry.get("Mach", 0.78)

        comp_h = predictions.get("Compressor Health", 99.5)
        comb_h = predictions.get("Combustor Health", 99.5)
        turb_h = predictions.get("Turbine Health", 99.5)
        overall_h = predictions.get("Overall Health", 99.5)
        thrust = predictions.get("Thrust", 54)

        # ── Level 1: Mechanical ───────────────────────────────────────
        actual_rpm = self.mechanical.step(rpm, overall_h, dt)

        # ── Level 2: Fluid ────────────────────────────────────────────
        self.fluid.step(actual_rpm, mach, altitude, P2, P3, P4, thrust)

        # ── Level 3: Thermal ──────────────────────────────────────────
        ambient = -45 + (1 - altitude / 40000) * 65  # approximate ambient temp at altitude
        t_intake = ambient + (T2 - ambient) * 0.05
        t_fan = ambient + (T2 - ambient) * 0.12
        t_lpc = ambient + (T2 - ambient) * 0.5
        t_hpc = T2
        t_diff = T2 * 1.05
        t_comb = T3
        t_hpt = T3 * 0.85
        t_lpt = (T3 + T4) * 0.5
        t_exh = T4
        t_noz = T4 * 0.85
        t_shaft = (T2 + T4) * 0.3
        t_bear = t_shaft * 0.8

        # Adjacent-component conduction chains
        self.thermal_components["intake"].step(t_intake, dt, [ambient])
        self.thermal_components["fan"].step(t_fan, dt, [self.thermal_components["intake"].temperature])
        self.thermal_components["lpc_1"].step(t_lpc * 0.7, dt, [self.thermal_components["fan"].temperature])
        self.thermal_components["lpc_2"].step(t_lpc * 0.85, dt, [self.thermal_components["lpc_1"].temperature])
        self.thermal_components["lpc_3"].step(t_lpc, dt, [self.thermal_components["lpc_2"].temperature])
        self.thermal_components["hpc_1"].step(t_hpc * 0.85, dt, [self.thermal_components["lpc_3"].temperature])
        self.thermal_components["hpc_2"].step(t_hpc * 0.93, dt, [self.thermal_components["hpc_1"].temperature])
        self.thermal_components["hpc_3"].step(t_hpc, dt, [self.thermal_components["hpc_2"].temperature])
        self.thermal_components["diffuser"].step(t_diff, dt, [self.thermal_components["hpc_3"].temperature])
        self.thermal_components["combustor"].step(t_comb, dt, [self.thermal_components["diffuser"].temperature])
        self.thermal_components["hpt_1"].step(t_hpt, dt, [self.thermal_components["combustor"].temperature])
        self.thermal_components["hpt_2"].step(t_hpt * 0.92, dt, [self.thermal_components["hpt_1"].temperature])
        self.thermal_components["lpt_1"].step(t_lpt, dt, [self.thermal_components["hpt_2"].temperature])
        self.thermal_components["lpt_2"].step(t_lpt * 0.9, dt, [self.thermal_components["lpt_1"].temperature])
        self.thermal_components["exhaust"].step(t_exh, dt, [self.thermal_components["lpt_2"].temperature])
        self.thermal_components["nozzle"].step(t_noz, dt, [self.thermal_components["exhaust"].temperature])
        self.thermal_components["shaft"].step(t_shaft, dt)
        self.thermal_components["bearings"].step(t_bear, dt, [self.thermal_components["shaft"].temperature])

        # ── Level 4: Combustion ───────────────────────────────────────
        self.combustion.step(fuel_flow, T3, comb_h, actual_rpm)

        # ── Level 5: Fuel System ──────────────────────────────────────
        self.fuel_system.step(fuel_flow, actual_rpm, overall_h)

        # ── Level 6: Pressure ─────────────────────────────────────────
        self.pressure.step(P2, P3, P4, altitude)

        # ── Level 9: Vibration ────────────────────────────────────────
        self.vibration.step(actual_rpm, overall_h, comp_h, turb_h)

        # ── Level 8: Wear ─────────────────────────────────────────────
        self.wear.step(cycle)

        # ── Assemble output ───────────────────────────────────────────
        state = {
            "mechanical": {
                "rpm": round(self.mechanical.rpm, 1),
                "omega": round(self.mechanical.omega, 3),
                "alpha": round(self.mechanical.alpha, 3),
                "torque_net": round(self.mechanical.torque_net, 2),
                "torque_turbine": round(self.mechanical.torque_turbine, 2),
                "torque_compressor": round(self.mechanical.torque_compressor, 2),
                "torque_friction": round(self.mechanical.torque_friction, 4),
                "moment_of_inertia": self.mechanical.moment_of_inertia,
                "rotor_imbalance": round(self.mechanical.rotor_imbalance, 4),
            },
            "fluid": {
                "intake_velocity_ms": round(self.fluid.intake_velocity, 1),
                "compressor_exit_velocity_ms": round(self.fluid.compressor_exit_velocity, 1),
                "diffuser_exit_velocity_ms": round(self.fluid.diffuser_exit_velocity, 1),
                "turbine_exit_velocity_ms": round(self.fluid.turbine_exit_velocity, 1),
                "exhaust_velocity_ms": round(self.fluid.exhaust_velocity, 1),
                "compression_ratio": round(self.fluid.compression_ratio, 2),
                "expansion_ratio": round(self.fluid.expansion_ratio, 2),
                "mass_flow_rate_kgs": round(self.fluid.mass_flow_rate, 1),
            },
            "thermal": {
                comp: {
                    "temperature": round(st.temperature, 1),
                    "target": round(st.target_temperature, 1),
                    "heating_rate": round(st.heating_rate, 2),
                }
                for comp, st in self.thermal_components.items()
            },
            "combustion": {
                "flame_intensity": round(self.combustion.flame_intensity, 4),
                "combustion_efficiency": round(self.combustion.combustion_efficiency, 4),
                "heat_release_MW": round(self.combustion.heat_release_rate, 2),
                "primary_zone": round(self.combustion.primary_zone_intensity, 4),
                "secondary_zone": round(self.combustion.secondary_zone_intensity, 4),
                "dilution_zone": round(self.combustion.dilution_zone_intensity, 4),
                "ignition_active": self.combustion.ignition_active,
                "flame_stable": self.combustion.flame_stable,
            },
            "fuel_system": {
                "pump_pressure_psi": round(self.fuel_system.pump_pressure, 1),
                "manifold_pressure_psi": round(self.fuel_system.manifold_pressure, 1),
                "injector_pressure_psi": round(self.fuel_system.injector_pressure, 1),
                "spray_cone_angle_deg": round(self.fuel_system.spray_cone_angle, 1),
                "droplet_density": round(self.fuel_system.droplet_density, 3),
                "spray_velocity_ms": round(self.fuel_system.spray_velocity, 1),
                "injector_health_pct": round(self.fuel_system.injector_health, 1),
            },
            "pressure": {
                "P_ambient_psi": round(self.pressure.P_ambient, 2),
                "P2_psi": round(self.pressure.P2, 1),
                "P3_psi": round(self.pressure.P3, 1),
                "P4_psi": round(self.pressure.P4, 1),
                "compressor_pressure_ratio": round(self.pressure.compressor_pressure_ratio, 2),
                "turbine_pressure_ratio": round(self.pressure.turbine_pressure_ratio, 2),
                "pressure_gradient_comp_psi_per_stage": round(self.pressure.pressure_gradient_comp, 2),
                "pressure_gradient_turb_psi_per_stage": round(self.pressure.pressure_gradient_turb, 2),
            },
            "health": {
                "compressor": round(comp_h, 1),
                "combustor": round(comb_h, 1),
                "turbine": round(turb_h, 1),
                "overall": round(overall_h, 1),
            },
            "wear": {
                "carbon_deposit": round(self.wear.carbon_deposit, 3),
                "blade_oxidation": round(self.wear.blade_oxidation, 3),
                "thermal_discoloration": round(self.wear.thermal_discoloration, 3),
                "surface_roughness": round(self.wear.surface_roughness, 3),
                "soot_accumulation": round(self.wear.soot_accumulation, 3),
                "erosion": round(self.wear.erosion, 3),
            },
            "vibration": {
                "rotor_imbalance": round(self.vibration.rotor_imbalance_amplitude, 6),
                "bearing": round(self.vibration.bearing_vibration_amplitude, 6),
                "shaft_oscillation": round(self.vibration.shaft_oscillation_amplitude, 6),
                "housing": round(self.vibration.housing_vibration_amplitude, 6),
                "total_amplitude": round(self.vibration.total_amplitude, 6),
                "dominant_frequency_hz": round(self.vibration.dominant_frequency, 1),
            },
            "lifecycle": {
                "cycle": cycle,
                "age_factor": round(min(cycle / 300, 1.0), 3),
            },
        }

        return state


# Singleton for the FastAPI application
physics_runtime = PhysicsRuntime()
