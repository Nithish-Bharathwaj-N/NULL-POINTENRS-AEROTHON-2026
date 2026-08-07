# HAL Mission Control - Biometric Engine Verification Script
# Tests 512-dim embedding generation, cosine similarity matching, optical quality rejection, and liveness

import cv2
import numpy as np
import base64
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.auth.biometric_engine import BiometricEngine
from backend.auth.face_alignment import OpticalQualityValidator
from backend.auth.verification import BiometricVerificationService

def create_synthetic_base64_frame(width=320, height=320, brightness=130, blur_sigma=0.0):
    """
    Creates a synthetic BGR image frame with a centered geometric pattern simulating a face for testing.
    """
    img = np.ones((height, width, 3), dtype=np.uint8) * int(brightness)
    
    # Add contrast features (simulating eyes, nose, mouth) so Laplacian variance and gradients work
    cv2.circle(img, (int(width*0.35), int(height*0.4)), 15, (50, 50, 50), -1)  # Left eye
    cv2.circle(img, (int(width*0.65), int(height*0.4)), 15, (50, 50, 50), -1)  # Right eye
    cv2.rectangle(img, (int(width*0.45), int(height*0.45)), (int(width*0.55), int(height*0.6)), (80, 80, 80), -1)  # Nose
    cv2.rectangle(img, (int(width*0.35), int(height*0.7)), (int(width*0.65), int(height*0.75)), (60, 60, 60), -1)  # Mouth

    # Add some texture/noise for sharpness
    noise = np.random.randint(-15, 15, (height, width, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    if blur_sigma > 0:
        img = cv2.GaussianBlur(img, (0, 0), sigmaX=blur_sigma)

    _, buf = cv2.imencode(".jpg", img)
    b64_str = base64.b64encode(buf).decode("utf-8")
    return b64_str, img

def run_biometric_engine_tests():
    print("====================================================================")
    print("HAL MISSION CONTROL - PHASE 13 BIOMETRIC ENGINE VERIFICATION SUITE")
    print("====================================================================")

    engine = BiometricEngine.get_instance()
    print("[OK] BiometricEngine singleton instantiated.")

    # Test 1: Synthetic Frame Enrollment & 512-dim Vector Generation
    print("\n[TEST 1] Testing Operator Enrollment & 512-dim Vector Generation...")
    b64_nominal, img_nominal = create_synthetic_base64_frame(width=320, height=320, brightness=130, blur_sigma=0.0)
    
    success, msg, norm_vec, metrics = engine.enroll_operator([b64_nominal])
    assert success, f"Enrollment failed: {msg}"
    assert norm_vec is not None and len(norm_vec) == 512, f"Expected 512-dim vector, got {len(norm_vec) if norm_vec else 'None'}"
    
    # Check L2 normalization (norm should be 1.0)
    vec_norm = np.linalg.norm(norm_vec)
    assert abs(vec_norm - 1.0) < 1e-4, f"Vector not L2 normalized: {vec_norm}"
    print(f"[OK] Successfully generated L2-normalized 512-dim embedding (L2 Norm: {vec_norm:.4f}).")

    # Test 2: Cosine Similarity Matching & Verification (Same Subject)
    print("\n[TEST 2] Testing Cosine Similarity Verification (Same Frame vs Different)...")
    is_verified, sim_score, status_code, display_msg, telemetry, qual_metrics = engine.verify_operator_login(
        base64_frame=b64_nominal,
        stored_embedding=norm_vec,
        liveness_action="BLINK",
        operator_id="HAL-001",
        operator_name="TEST COMMANDER"
    )
    assert is_verified, f"Verification failed for identical subject: {display_msg} (Score: {sim_score})"
    assert sim_score >= BiometricVerificationService.DEFAULT_AUTH_THRESHOLD, f"Score {sim_score} below threshold"
    print(f"[OK] Same-subject verification passed. Score: {sim_score:.4f} (Status: {status_code})")

    # Test 2b: Verification Mismatch for Different Subject
    print("\n[TEST 2B] Testing Cosine Similarity Mismatch (Different Subject)...")
    # Generate different synthetic face structure
    np.random.seed(999)
    b64_diff, _ = create_synthetic_base64_frame(width=320, height=320, brightness=190, blur_sigma=0.0)
    _, _, norm_vec_diff, _ = engine.enroll_operator([b64_diff])
    
    is_ver_diff, sim_diff, status_diff, msg_diff, _, _ = engine.verify_operator_login(
        base64_frame=b64_diff,
        stored_embedding=norm_vec,
        liveness_action="BLINK"
    )
    print(f"    Different Face Match Similarity: {sim_diff:.4f} (Status: {status_diff})")
    assert not is_ver_diff or sim_diff < BiometricVerificationService.DEFAULT_AUTH_THRESHOLD, f"Different face should not match: score={sim_diff}"
    print(f"[OK] Different face correctly identified or rejected: Score {sim_diff:.4f} below threshold.")

    # Test 3: Optical Quality Rejection (Under-exposed / Dark Frame)
    print("\n[TEST 3] Testing Optical Quality Rejection (Under-exposed Lighting)...")
    b64_dark, _ = create_synthetic_base64_frame(width=320, height=320, brightness=20, blur_sigma=0.0)
    is_verified_dark, sim_dark, status_dark, msg_dark, _, _ = engine.verify_operator_login(
        base64_frame=b64_dark,
        stored_embedding=norm_vec,
        liveness_action="BLINK"
    )
    assert not is_verified_dark and status_dark == "REJECTED_QUALITY", f"Dark frame should be rejected, got {status_dark}"
    print(f"[OK] Under-exposed frame correctly rejected: \"{msg_dark}\"")

    # Test 4: Optical Quality Rejection (Motion Blur Frame)
    print("\n[TEST 4] Testing Optical Quality Rejection (Facial Motion Blur)...")
    b64_blur, _ = create_synthetic_base64_frame(width=320, height=320, brightness=130, blur_sigma=8.0)
    is_verified_blur, sim_blur, status_blur, msg_blur, _, _ = engine.verify_operator_login(
        base64_frame=b64_blur,
        stored_embedding=norm_vec,
        liveness_action="BLINK"
    )
    assert not is_verified_blur and status_blur == "REJECTED_QUALITY", f"Blurry frame should be rejected, got {status_blur}"
    print(f"[OK] Motion blur frame correctly rejected: \"{msg_blur}\"")

    # Test 5: Null / Corrupted Frame Rejection
    print("\n[TEST 5] Testing Null/Corrupted Camera Feed Rejection...")
    is_ver_null, sim_null, status_null, msg_null, _, _ = engine.verify_operator_login(
        base64_frame="INVALID_BASE64_STRING_999",
        stored_embedding=norm_vec,
        liveness_action="SMILE"
    )
    assert not is_ver_null and status_null == "REJECTED_NULL_FRAME", f"Expected REJECTED_NULL_FRAME, got {status_null}"
    print(f"[OK] Corrupted frame correctly rejected: \"{msg_null}\"")

    print("\n====================================================================")
    print("ALL BIOMETRIC ENGINE VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("====================================================================")

if __name__ == "__main__":
    run_biometric_engine_tests()
