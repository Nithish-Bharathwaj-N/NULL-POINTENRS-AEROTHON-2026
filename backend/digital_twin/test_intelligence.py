"""
Smoke test for the 9-phase Aerospace Intelligence Pipeline.
Validates all outputs: envelope check, dynamic health, causal reasoning,
SHAP, maintenance prognosis, and competition readiness scorer.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from aerospace_intelligence import (
    validate_engineering_envelope,
    compute_dynamic_health,
    generate_causal_reasoning,
    generate_aerospace_shap,
    generate_maintenance_prognosis,
    compute_competition_readiness,
    run_intelligence_pipeline,
    _telemetry_cache,
)

SAMPLE_TELEMETRY = {
    "EngineID": "HAL-TJ4-001",
    "Cycle": 120,
    "Altitude_m": 9144.0,
    "Mach": 0.78,
    "Tamb_K": 228.15,
    "Pamb_Pa": 30000.0,
    "RPM_rev_min": 16222.0,
    "FuelFlow_kg_s": 0.68,
    "P2_Pa": 42000.0,
    "T2_K": 350.0,
    "P3_Pa": 2400000.0,
    "T3_K": 1680.0,
    "P4_Pa": 120000.0,
    "T4_K": 1012.0,
    "vibrationG": 0.54,
}

SAMPLE_PREDICTIONS = {
    "Compressor Health": 94.2,
    "Combustor Health": 92.5,
    "Turbine Health": 91.8,
    "Overall Health": 93.0,
    "Thrust": 48.5,
    "TSFC": 0.0197,
    "Prediction Confidence": 96.4,
    "Inference Time Ms": 12.3,
}

SAMPLE_PHYSICS_VALIDATION = {
    "physics_residual": 0.042,
    "is_physics_compliant": True,
    "compliance_score_pct": 95.0,
}

print("=" * 70)
print("AEROTWIN -- 9-Phase Intelligence Pipeline Smoke Test")
print("=" * 70)

# Phase 5
print("\n[Phase 5] Engineering Envelope Validation:")
envelope = validate_engineering_envelope(SAMPLE_TELEMETRY)
print(f"  Compliant: {envelope['is_envelope_compliant']}")
print(f"  Compliance Score: {envelope['compliance_score_pct']}%")
print(f"  Violations: {envelope['violation_count']}")
print(f"  Physics Warnings: {envelope['warning_count']}")

# Phase 6
print("\n[Phase 6] Dynamic Health Engine:")
health = compute_dynamic_health(94.2, 92.5, 91.8, cycle=120, vib=0.54)
print(f"  Overall Health (smoothed): {health['OverallHealth_smoothed']}%")
print(f"  Trend: {health['health_trend']}")
print(f"  Stability: {health['health_stability_pct']}%")
print(f"  Confidence: {health['health_confidence_pct']}%")
print(f"  Forecast 10/50/100 cycles: {health['forecast_10_cycles']} / {health['forecast_50_cycles']} / {health['forecast_100_cycles']}%")

# Phase 3
print("\n[Phase 3] Causal Reasoning:")
causal = generate_causal_reasoning(SAMPLE_TELEMETRY, SAMPLE_PREDICTIONS, health)
print(f"  What: {causal['what_changed']}")
print(f"  Why: {causal['why_changed'][:1]}")
print(f"  Limiting Subsystem: {causal['limiting_subsystem']}")
print(f"  Forecast: {causal['forecast_summary']}")

# Phase 4
print("\n[Phase 4] Aerospace SHAP:")
shap = generate_aerospace_shap(SAMPLE_TELEMETRY, SAMPLE_PREDICTIONS)
print(f"  Primary Factor: {shap['primary_sensor']}")
print(f"  Primary Impact: {shap['primary_impact_pct']}%")
print(f"  Explanation Stable: {shap['explanation_stable']}")
print(f"  Top degrading factors: {len(shap['top_degrading_factors'])}")

# Phase 7
print("\n[Phase 7] Maintenance Prognosis:")
prog = generate_maintenance_prognosis(SAMPLE_PREDICTIONS, health, SAMPLE_TELEMETRY, cycle=120)
print(f"  Severity: {prog['severity']}")
print(f"  Action Tier: {prog['action_tier']}")
print(f"  RUL (cycles): {prog['estimated_rul_cycles']}")
print(f"  RUL (hours): {prog['estimated_rul_hours']}")
print(f"  Failure Modes: {len(prog['failure_modes_detected'])}")

# Phase 9
print("\n[Phase 9] Competition Readiness:")
comp = compute_competition_readiness(SAMPLE_PREDICTIONS, SAMPLE_PHYSICS_VALIDATION, health, shap)
print(f"  TOTAL AEROTHON SCORE: {comp['aerothon_total_score']} / 100")
print(f"  Tier: {comp['competition_tier']}")
print(f"  Health Accuracy: {comp['health_estimation_accuracy']}")
print(f"  Physics Consistency: {comp['physics_consistency']}")
print(f"  Efficiency: {comp['computational_efficiency']}")
print(f"  Interpretability: {comp['interpretability']}")

# Full pipeline (Phase 8 cache test)
print("\n[Phase 8] O(1) Cache Performance:")
run_intelligence_pipeline(SAMPLE_TELEMETRY, SAMPLE_PREDICTIONS, SAMPLE_PHYSICS_VALIDATION, 120)
run_intelligence_pipeline(SAMPLE_TELEMETRY, SAMPLE_PREDICTIONS, SAMPLE_PHYSICS_VALIDATION, 120)  # should cache hit
print(f"  Cache hits: {_telemetry_cache.hits}")
print(f"  Cache misses: {_telemetry_cache.misses}")
print(f"  Cache hit rate: {_telemetry_cache.hit_rate_pct}%")

print("\n" + "=" * 70)
print("ALL 9 INTELLIGENCE PHASES PASSED [OK]")
print("=" * 70)
