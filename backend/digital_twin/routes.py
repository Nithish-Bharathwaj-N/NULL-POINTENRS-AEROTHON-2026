import os
import sys
import time
import pandas as pd
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, Response

twin_dir = os.path.dirname(os.path.abspath(__file__))
if twin_dir not in sys.path:
    sys.path.append(twin_dir)

from engine_state import state_manager
from ml.health_predictor import HealthPredictor
from physics_engine.physics_api import augment_with_physics
from physics.physics_validator import PhysicsValidator
from physics.physics_runtime import PhysicsRuntime
from xai.xai_engine import ExplainableAIEngine, TemporalXAIEngine
from maintenance.failure_scenarios import FailureScenarioLibrary
from maintenance.maintenance_advisor import AIMaintenanceAdvisor
from telemetry.telemetry_streamer import TelemetryStreamer
from aerospace_intelligence import run_intelligence_pipeline

# ─── New Aerothon 2026 Modules ────────────────────────────────────────────────
from ml.engine_history import get_global_store
from ml.reasoning_engine import EngineeringReasoningEngine
from ml.report_generator import EngineeringReportGenerator
from physics.gas_turbine_equations import GasTurbinePhysicsEngine

router = APIRouter(prefix="/api/v1/twin", tags=["AEROTWIN Digital Twin Service"])

# ─── Global Service Instances ─────────────────────────────────────────────────
data_path = os.path.join(twin_dir, "data", "turbojet_complete_dataset.csv")

ml_predictor     = HealthPredictor.load()
telemetry_streamer = TelemetryStreamer(dataset_path=data_path)
physics_runtime  = PhysicsRuntime()
history_store    = get_global_store()

# ─── Lazy-loaded fleet analytics (heavy, loaded once on first request) ─────────
_fleet_analytics = None
_fleet_df        = None

def _get_fleet() -> "FleetAnalytics":
    global _fleet_analytics, _fleet_df
    if _fleet_analytics is None:
        try:
            from ml.fleet_analytics import FleetAnalytics
            _fleet_df = pd.read_csv(data_path)
            _fleet_analytics = FleetAnalytics()
            _fleet_analytics.fit(_fleet_df)
            print("[Routes] FleetAnalytics fitted on full dataset.")
        except Exception as e:
            print(f"[Routes] FleetAnalytics load warning: {e}")
            _fleet_analytics = None
    return _fleet_analytics


# ─── Core Frame Processor ──────────────────────────────────────────────────────
def process_active_frame(scenario_frame: dict, engine_id: str = "1", cycle: int = 1) -> dict:
    """
    Full Aerothon 2026 inference pipeline.
    1. Push frame to engine history store
    2. Scikit-learn RF + Hybrid ML inference
    3. Physics engine augmentation
    4. Physics validation
    5. Temporal context computation from history
    6. XAI causal chain + temporal SHAP
    7. Maintenance advisor
    8. Aerospace intelligence (9-phase pipeline)
    9. Engineering reasoning narrative
    10. Fleet context (peer comparison, root cause, cluster)
    """
    t0 = time.perf_counter()

    # 1. Store in engine history
    history_store.add_cycle(str(engine_id), {**scenario_frame, "Cycle": cycle})

    # 2. ML Predictions (RF models + optional hybrid)
    preds = ml_predictor.predict(scenario_frame)

    # 3. Member2 Analytical Physics Engine
    df_single = pd.DataFrame([scenario_frame])
    try:
        df_augmented = augment_with_physics(df_single)
        row_aug      = df_augmented.iloc[0].to_dict()
        physics_feat = row_aug.get("physics_features", {})
        residual_feat= row_aug.get("residual_features", {})
    except Exception:
        physics_feat  = {}
        residual_feat = {}

    # 4. Physics validation & First-Principles Engine Calculation
    physics_res   = PhysicsValidator.validate_telemetry_frame(scenario_frame, preds)
    physics_state = physics_runtime.step(scenario_frame, preds)
    if physics_feat:
        physics_state.update(physics_feat)
    if residual_feat:
        physics_state["residual_features"] = residual_feat

    # 4b. First-Principles 4-Stage Aerothermodynamic Model (GasTurbinePhysicsEngine)
    try:
        t2 = float(scenario_frame.get("T2_K", 233.0 + 273.15)) - 273.15 if float(scenario_frame.get("T2_K", 500)) > 150 else float(scenario_frame.get("T2_K", 20))
        t3 = float(scenario_frame.get("T3_K", 1770.0 + 273.15)) - 273.15 if float(scenario_frame.get("T3_K", 1700)) > 150 else float(scenario_frame.get("T3_K", 1200))
        p2 = float(scenario_frame.get("P2_Pa", 450000)) / 6894.76
        p3 = float(scenario_frame.get("P3_Pa", 4000000)) / 6894.76
        ff = float(scenario_frame.get("FuelFlow_kg_s", 0.68)) * 3600.0
        mach = float(scenario_frame.get("Mach", 0.78))
        alt = float(scenario_frame.get("Altitude_m", 10000)) * 3.28084
        comp_h = float(preds.get("Compressor Health", 99.0))
        comb_h = float(preds.get("Combustor Health", 99.0))
        turb_h = float(preds.get("Turbine Health", 99.0))

        tt1_k, pt1_psi = GasTurbinePhysicsEngine.calculate_inlet_conditions(alt, mach, -45.0, 3.9)
        tt2_c, eta_c = GasTurbinePhysicsEngine.calculate_compressor_exit(tt1_k, pt1_psi, p2, comp_h)
        tt3_c, eta_b = GasTurbinePhysicsEngine.calculate_combustor_exit(tt2_c, ff, comb_h)
        tt4_c, p4_psi, thrust_kn, tsfc_val = GasTurbinePhysicsEngine.calculate_turbine_and_thrust(tt3_c, tt2_c, p3, turb_h, mach)

        first_principles_physics = {
            "model_type": "First-Principles 4-Stage Aerothermodynamic Model",
            "equations_applied": [
                "Isentropic Compression Law (Stage 2)",
                "Combustor First Law Enthalpy Conservation (Stage 3)",
                "Turbine Shaft Work Matching (Stage 4)",
                "Choked Nozzle Momentum Thrust & TSFC"
            ],
            "theoretical_compressor_exit_temp_c": round(tt2_c, 1),
            "theoretical_compressor_isentropic_efficiency": round(eta_c, 4),
            "theoretical_combustor_exit_temp_c": round(tt3_c, 1),
            "theoretical_combustor_efficiency": round(eta_b, 4),
            "theoretical_turbine_exit_temp_c": round(tt4_c, 1),
            "theoretical_nozzle_pressure_psi": round(p4_psi, 1),
            "theoretical_thrust_kn": round(thrust_kn, 2),
            "theoretical_tsfc": round(tsfc_val, 4)
        }
    except Exception as ex:
        first_principles_physics = {"model_type": "First-Principles Model", "error": str(ex)}

    # 5. Temporal context from history
    temporal_ctx = history_store.compute_temporal_context(str(engine_id))
    experience   = history_store.get_experience(str(engine_id))

    # 6. XAI — Causal Chain + Temporal SHAP
    xai_causal_chain = TemporalXAIEngine.generate_causal_chain(
        scenario_frame, preds, temporal_ctx
    )
    xai_legacy = ExplainableAIEngine.generate_explanation(scenario_frame, preds)

    history_df = history_store.get_history(str(engine_id), window=20)
    temporal_shap = TemporalXAIEngine.generate_temporal_explanation(
        str(engine_id), history_df, preds
    )

    # 7. Maintenance advisor
    maint_res = AIMaintenanceAdvisor.generate_recommendations(
        preds, scenario_frame, physics_state, state_manager.active_scenario
    )

    # 8. Aerospace intelligence pipeline (Phases 1–9)
    ai_result = run_intelligence_pipeline(scenario_frame, preds, physics_res, cycle)

    # 9. Engineering reasoning narrative
    rul_est = ai_result.get("maintenance_prognosis", {})
    rul_dict = {
        "rul_mean":   rul_est.get("estimated_rul_cycles", 200),
        "rul_p10":    max(0, rul_est.get("estimated_rul_cycles", 200) - 40),
        "rul_p90":    rul_est.get("estimated_rul_cycles", 200) + 40,
        "confidence": 85.0,
        "warning":    rul_est.get("severity", "NORMAL"),
        "regime":     ("late" if (preds.get("Overall Health",100) or 100) < 85
                        else "mid" if (preds.get("Overall Health",100) or 100) < 95
                        else "early"),
    }

    fleet_ctx = {}
    fleet = _get_fleet()
    if fleet and fleet.is_fitted_:
        try:
            peer = fleet.get_peer_comparison(str(engine_id))
            cluster = fleet.get_engine_cluster(str(engine_id))
            root_cause = fleet.get_root_cause(str(engine_id))
            fleet_ctx = {**peer, **cluster, "root_cause": root_cause}
        except Exception:
            fleet_ctx = {}

    narrative_brief = EngineeringReasoningEngine.generate_brief(
        engine_id=str(engine_id),
        predictions=preds,
        rul_mean=int(rul_dict["rul_mean"]),
        rul_warning=str(rul_dict["warning"]),
        overall_trend=ai_result.get("dynamic_health", {}).get("health_trend", "STABLE"),
    )

    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    return {
        # ── Core (backward-compatible) ───────────────────────────────────────
        "engine_state":       state_manager.current_state,
        "telemetry":          scenario_frame,
        "predictions":        preds,
        "physics_validation": physics_res,
        "physics_runtime":    physics_state,
        "xai_explanation":    xai_legacy,
        "maintenance_advice": maint_res,

        # ── New Aerothon 2026 fields ─────────────────────────────────────────
        "causal_chain":            xai_causal_chain,
        "temporal_shap":           temporal_shap,
        "temporal_context":        temporal_ctx,
        "engine_experience":       experience,
        "rul_estimate":            rul_dict,
        "fleet_context":           fleet_ctx,
        "engineering_narrative":   narrative_brief,
        "aerospace_intelligence":  ai_result,
        "total_inference_ms":      elapsed_ms,
    }


# ─── Standard Endpoints (backward-compatible) ─────────────────────────────────

@router.get("/health")
def get_health():
    return {
        "status": "ONLINE",
        "service": "AEROTWIN Ω — Aerothon 2026 Aerospace-Grade Prognostics Platform",
        "engine_state": state_manager.current_state,
        "cycle_cursor": state_manager.cycle_cursor,
        "models_loaded": len(ml_predictor.models) == 6,
        "dataset_loaded": telemetry_streamer.df is not None,
        "dataset_engines": telemetry_streamer.df["EngineID"].nunique() if telemetry_streamer.df is not None else 0,
        "dataset_max_cycles": int(telemetry_streamer.df["Cycle"].max()) if telemetry_streamer.df is not None else 0,
        "active_scenario": state_manager.active_scenario,
        "fleet_analytics_ready": _fleet_analytics is not None and _fleet_analytics.is_fitted_,
    }

@router.get("/logs")
def get_mission_logs():
    return {"logs": state_manager.logger.get_logs()}

@router.get("/scenarios")
def get_scenarios():
    return {
        "scenarios": FailureScenarioLibrary.SCENARIOS,
        "active_scenario": state_manager.active_scenario,
        "state": state_manager.current_state,
    }

@router.get("/engines")
def get_engines():
    engines = telemetry_streamer.get_engines()
    engine_info = []
    for eng in engines:
        max_c = telemetry_streamer.get_engine_max_cycles(eng)
        cluster_info = {}
        fleet = _get_fleet()
        if fleet and fleet.is_fitted_:
            try:
                cluster_info = fleet.get_engine_cluster(str(eng))
            except Exception:
                pass
        engine_info.append({"engine_id": eng, "max_cycles": max_c, **cluster_info})
    return {"engines": engine_info}

@router.post("/engine/start")
def start_engine():
    state_manager.request_start()
    return {
        "status": "SUCCESS",
        "message": "Engine startup sequence initiated (8-12s duration)",
        "engine_state": state_manager.current_state,
    }

@router.post("/engine/stop")
def stop_engine():
    state_manager.request_stop()
    return {
        "status": "SUCCESS",
        "message": "Engine shutdown sequence initiated",
        "engine_state": state_manager.current_state,
    }

@router.post("/engine/throttle/{pct}")
def set_throttle(pct: float):
    new_pct = state_manager.set_throttle(pct)
    return {"status": "SUCCESS", "throttle_pct": new_pct, "engine_state": state_manager.current_state}


# ─── Telemetry Endpoints (cycle cap fixed: 30 → 300) ─────────────────────────

@router.get("/telemetry/live")
def get_live_telemetry(engine_id: Optional[str] = "1", cycle: Optional[int] = None):
    st = state_manager.current_state

    if cycle is not None and cycle > 0:
        target_cycle = min(cycle, 300)
    else:
        target_cycle = state_manager.cycle_cursor if state_manager.cycle_cursor > 0 else 1
        # Advance cycle in ALL active states (RUNNING, IDLE, FAULT) — not just RUNNING
        if st in ["RUNNING", "IDLE", "FAULT"]:
            state_manager.cycle_cursor += 1
            if state_manager.cycle_cursor > 300:
                state_manager.cycle_cursor = 1

    raw_frame = telemetry_streamer.get_playback_frame(str(engine_id), target_cycle)

    if st == "OFF":
        raw_frame["RPM_rev_min"] = 0.0
        raw_frame["RPM"] = 0.0
    elif st == "STARTING":
        prog = state_manager.startup_progress_pct / 100.0
        raw_frame["RPM_rev_min"] = round(prog * 2800.0, 1)
        raw_frame["RPM"] = round(prog * 2800.0, 1)
    elif st == "SHUTDOWN":
        prog = 1.0 - (state_manager.shutdown_progress_pct / 100.0)
        raw_frame["RPM_rev_min"] = round(prog * 2800.0, 1)
        raw_frame["RPM"] = round(prog * 2800.0, 1)
    else:
        base_rpm = 2800.0 + state_manager.throttle_pct * (12500.0 - 2800.0)
        raw_frame["RPM_rev_min"] = round(base_rpm, 1)
        raw_frame["RPM"] = round(base_rpm, 1)

    scenario_frame = FailureScenarioLibrary.apply_scenario(state_manager.active_scenario, raw_frame)
    return process_active_frame(scenario_frame, engine_id=str(engine_id), cycle=target_cycle)


@router.get("/telemetry/history/{engine_id}")
def get_engine_history(engine_id: str):
    """
    Returns all precomputed health predictions for every cycle of a given engine.
    Used by the frontend to pre-populate the interactive health chart on load.
    Each cycle's sensor readings are fed through the trained ML model to produce predictions.
    Cycle number is NOT a model feature — it is used only as the X-axis ordering label.
    """
    if telemetry_streamer.df is None:
        return {"engine_id": engine_id, "history": []}

    # Get all rows for this engine, sorted by cycle
    eng_df = telemetry_streamer.df[telemetry_streamer.df["EngineID"].astype(str) == str(engine_id)]
    if len(eng_df) == 0:
        # Try numeric engine_id
        try:
            eng_df = telemetry_streamer.df[telemetry_streamer.df["EngineID"] == float(engine_id)]
        except Exception:
            pass
    if len(eng_df) == 0:
        return {"engine_id": engine_id, "history": [], "error": "Engine not found"}

    eng_df = eng_df.sort_values("Cycle").reset_index(drop=True)
    history_points = []

    for _, row in eng_df.iterrows():
        cycle_num = int(row["Cycle"])
        raw_frame = telemetry_streamer._clean_row(row.to_dict())
        # Apply current active scenario for consistency
        scenario_frame = FailureScenarioLibrary.apply_scenario(state_manager.active_scenario, raw_frame)
        try:
            preds = ml_predictor.predict(scenario_frame)
            history_points.append({
                "cycle": cycle_num,
                "overall":    round(float(preds.get("Overall Health",    row.get("OverallHealth",    90))), 2),
                "compressor": round(float(preds.get("Compressor Health", row.get("CompressorHealth", 90))), 2),
                "combustor":  round(float(preds.get("Combustor Health",  row.get("CombustorHealth",  90))), 2),
                "turbine":    round(float(preds.get("Turbine Health",    row.get("TurbineHealth",    90))), 2),
                "thrust_kn":  round(float(row.get("Thrust_N", 48000)) / 1000, 2),
                "t4_c":       round(float(row.get("T4_K", 1100)) - 273.15, 1),
                "fuel_kg_h":  round(float(row.get("FuelFlow_kg_s", 0.68)) * 3600, 1),
            })
        except Exception as e:
            # Fallback: use raw dataset health columns
            history_points.append({
                "cycle": cycle_num,
                "overall":    round(float(row.get("OverallHealth",    90)), 2),
                "compressor": round(float(row.get("CompressorHealth", 90)), 2),
                "combustor":  round(float(row.get("CombustorHealth",  90)), 2),
                "turbine":    round(float(row.get("TurbineHealth",    90)), 2),
                "thrust_kn":  round(float(row.get("Thrust_N", 48000)) / 1000, 2),
                "t4_c":       round(float(row.get("T4_K", 1100)) - 273.15, 1),
                "fuel_kg_h":  round(float(row.get("FuelFlow_kg_s", 0.68)) * 3600, 1),
            })

    return {
        "engine_id": engine_id,
        "total_cycles": len(history_points),
        "history": history_points,
        "note": "Cycle is X-axis ordering only — NOT a model feature. Predictions are from sensor readings."
    }


@router.get("/telemetry/playback/{engine_id}/{cycle}")
def get_playback_telemetry(engine_id: str, cycle: int):
    st = state_manager.current_state
    if st == "OFF":
        return {"engine_state": "OFF", "telemetry": None}
    raw_frame = telemetry_streamer.get_playback_frame(engine_id, cycle)
    scenario_frame = FailureScenarioLibrary.apply_scenario(state_manager.active_scenario, raw_frame)
    return process_active_frame(scenario_frame, engine_id=engine_id, cycle=cycle)


@router.post("/telemetry/scenario/{scenario_key}")
def set_failure_scenario(scenario_key: str):
    state_manager.set_scenario(scenario_key)
    return {
        "status": "SUCCESS",
        "active_scenario": state_manager.active_scenario,
        "engine_state": state_manager.current_state,
        "details": FailureScenarioLibrary.SCENARIOS.get(state_manager.active_scenario, {}),
    }

@router.post("/predict")
def predict_surrogate(payload: Dict[str, Any]):
    if state_manager.current_state == "OFF":
        return {"engine_state": "OFF", "predictions": None}
    return process_active_frame(payload)


# ─── Fleet Analytics Endpoints ─────────────────────────────────────────────────

@router.get("/fleet/health-distribution")
def get_fleet_health_distribution():
    """Fleet-wide health distribution by early/mid/late life phase."""
    fleet = _get_fleet()
    if not fleet or not fleet.is_fitted_:
        raise HTTPException(status_code=503, detail="Fleet analytics not ready")
    return fleet.get_fleet_health_distribution()

@router.get("/fleet/engine-clusters")
def get_engine_clusters():
    """Engine clustering by degradation archetype."""
    fleet = _get_fleet()
    if not fleet or not fleet.is_fitted_:
        raise HTTPException(status_code=503, detail="Fleet analytics not ready")
    clusters = {}
    for eng_id, idx in fleet._engine_clusters.items():
        from ml.fleet_analytics import CLUSTER_ARCHETYPES
        clusters[eng_id] = {
            "cluster_index": idx,
            "archetype": CLUSTER_ARCHETYPES.get(idx, "Normal Degrader"),
        }
    return {"engine_clusters": clusters, "n_engines": len(clusters)}

@router.get("/fleet/degradation-ordering")
def get_degradation_ordering():
    """Which sensors degrade first and most consistently across the fleet."""
    fleet = _get_fleet()
    if not fleet or not fleet.is_fitted_:
        raise HTTPException(status_code=503, detail="Fleet analytics not ready")
    return {
        "sensor_degradation_order": fleet.get_sensor_degradation_ordering(),
        "interpretation": "Ranked by percentage of engines showing degradation in this sensor",
    }

@router.get("/fleet/peer-comparison/{engine_id}")
def get_peer_comparison(engine_id: str):
    """Fleet percentile comparison for a specific engine."""
    fleet = _get_fleet()
    if not fleet or not fleet.is_fitted_:
        raise HTTPException(status_code=503, detail="Fleet analytics not ready")
    return fleet.get_peer_comparison(engine_id)

@router.get("/fleet/root-cause/{engine_id}")
def get_root_cause(engine_id: str):
    """Automatic root cause failure mechanism classification for an engine."""
    fleet = _get_fleet()
    if not fleet or not fleet.is_fitted_:
        raise HTTPException(status_code=503, detail="Fleet analytics not ready")
    return fleet.get_root_cause(engine_id)

@router.get("/fleet/similarity/{engine_id}")
def get_engine_similarity(engine_id: str, top_k: int = 5):
    """Find most similar engines in the fleet by degradation trajectory."""
    fleet = _get_fleet()
    if not fleet or not fleet.is_fitted_:
        raise HTTPException(status_code=503, detail="Fleet analytics not ready")
    return fleet.find_similar_engines(engine_id, top_k=top_k)

@router.get("/fleet/failure-precursors")
def get_failure_precursors():
    """Sensor patterns consistently detected before health threshold crossing."""
    fleet = _get_fleet()
    if not fleet or not fleet.is_fitted_:
        raise HTTPException(status_code=503, detail="Fleet analytics not ready")
    return {
        "failure_precursors": fleet.get_failure_precursors(),
        "threshold": "OverallHealth < 0.85",
        "lookahead_cycles": 20,
    }

@router.get("/fleet/critical-envelope")
def get_critical_envelope():
    """Operating conditions most strongly correlated with fastest degradation."""
    fleet = _get_fleet()
    if not fleet or not fleet.is_fitted_:
        raise HTTPException(status_code=503, detail="Fleet analytics not ready")
    return fleet.get_critical_operating_envelope()


# ─── Engineering Report Endpoint ───────────────────────────────────────────────

@router.get("/report/{engine_id}/{cycle}")
def get_engineering_report(engine_id: str, cycle: int, format: str = "json"):
    """
    Generate a full engineering report for a specific engine and cycle.
    format: json (default) | csv | txt | pdf
    """
    st = state_manager.current_state
    if st == "OFF":
        raise HTTPException(status_code=400, detail="Engine is OFF. Start engine first.")

    raw_frame = telemetry_streamer.get_playback_frame(engine_id, cycle)
    scenario_frame = FailureScenarioLibrary.apply_scenario(state_manager.active_scenario, raw_frame)
    frame_result = process_active_frame(scenario_frame, engine_id=engine_id, cycle=cycle)

    preds    = frame_result.get("predictions", {})
    rul_est  = frame_result.get("rul_estimate", {})
    causal   = frame_result.get("causal_chain", [])
    fleet_ctx= frame_result.get("fleet_context", {})
    phys_val = frame_result.get("physics_validation", {})
    maint    = frame_result.get("maintenance_advice", {})
    temp_ctx = frame_result.get("temporal_context", {})

    narrative = EngineeringReasoningEngine.generate_narrative(
        engine_id=engine_id,
        health_tree={},
        rul_estimate=rul_est,
        causal_chain=causal,
        fleet_context=fleet_ctx,
        predictions=preds,
        temporal_context=temp_ctx,
        root_cause=fleet_ctx.get("root_cause"),
    )

    report = EngineeringReportGenerator.generate_report(
        engine_id=engine_id,
        cycle=cycle,
        predictions=preds,
        health_tree={},
        rul_estimate=rul_est,
        causal_chain=causal,
        fleet_context=fleet_ctx,
        maintenance_prognosis=maint if isinstance(maint, dict) else {},
        engineering_narrative=narrative,
        physics_validation=phys_val,
        uncertainty_breakdown=preds.get("Uncertainty Bounds", {}),
        inference_time_ms=frame_result.get("total_inference_ms", 0.0),
    )

    if format == "csv":
        csv_content = EngineeringReportGenerator.to_csv(report)
        return Response(content=csv_content, media_type="text/csv",
                         headers={"Content-Disposition": f'attachment; filename="report_{engine_id}_{cycle}.csv"'})
    elif format == "txt":
        txt_content = EngineeringReportGenerator.to_text(report)
        return PlainTextResponse(content=txt_content)
    elif format == "pdf":
        pdf_bytes = EngineeringReportGenerator.to_pdf_bytes(report)
        if pdf_bytes is None:
            raise HTTPException(status_code=501, detail="PDF export requires 'reportlab' package. Install it or use format=txt.")
        return Response(content=pdf_bytes, media_type="application/pdf",
                         headers={"Content-Disposition": f'attachment; filename="report_{engine_id}_{cycle}.pdf"'})
    else:
        return report
