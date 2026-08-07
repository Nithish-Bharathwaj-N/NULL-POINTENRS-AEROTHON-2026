import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
twin_dir = os.path.join(backend_dir, "digital_twin")
sys.path.append(twin_dir)

print("Testing Digital Twin backend imports...")

try:
    from ml.train_pinn_surrogate import PhysicsInformedSurrogateModel
    from physics.physics_validator import PhysicsValidator
    from physics.physics_runtime import PhysicsRuntime
    from xai.xai_engine import ExplainableAIEngine
    from maintenance.failure_scenarios import FailureScenarioLibrary
    from maintenance.maintenance_advisor import AIMaintenanceAdvisor
    from telemetry.telemetry_streamer import TelemetryStreamer

    data_csv = os.path.join(twin_dir, "data", "turbojet_complete_dataset.csv")
    ml_dir = os.path.join(twin_dir, "ml")

    streamer = TelemetryStreamer(dataset_path=data_csv)
    pinn = PhysicsInformedSurrogateModel(model_dir=ml_dir)
    pinn.load()
    runtime = PhysicsRuntime()

    frame = streamer.get_next_live_frame()
    preds = pinn.predict(frame)
    valid = PhysicsValidator.validate_telemetry_frame(frame, preds)
    p_state = runtime.step(frame, preds)

    print("[OK] Telemetry frame:", frame.get("Cycle"), frame.get("RPM"))
    print("[OK] Predictions:", list(preds.keys()) if isinstance(preds, dict) else "Loaded")
    print("[OK] Physics Validation:", valid.get("status") if isinstance(valid, dict) else "Valid")
    print("[OK] Physics Runtime state:", p_state.get("health_index") if isinstance(p_state, dict) else "Active")
    print("ALL DIGITAL TWIN BACKEND MODULES INITIALIZED SUCCESSFULLY!")
except Exception as exc:
    print("[ERROR] Digital Twin test failed:", exc)
    import traceback
    traceback.print_exc()
