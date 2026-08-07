# HAL Mission Control - Enterprise Biometric Verification & Audit Telemetry Service
# Calculates Cosine Similarity on 512-dim neural identity vectors and logs audit telemetry

import numpy as np
from datetime import datetime, timezone
import logging

logger = logging.getLogger("hal_biometric_verification")

class BiometricVerificationService:
    """
    Performs cosine similarity comparison between normalized 512-dimensional deep-learning embeddings.
    Enforces configurable aerospace security thresholds and audit telemetry formatting.
    """
    DEFAULT_AUTH_THRESHOLD = 0.80
    DEFAULT_WARNING_THRESHOLD = 0.70
    SYSTEM_VERSION = "HAL-MIL-STD-498 // INSIGHTFACE-V2.5"

    @classmethod
    def compute_cosine_similarity(cls, vec1: np.ndarray | list, vec2: np.ndarray | list) -> float:
        """
        Computes cosine similarity between two 1D embedding vectors.
        Returns score clamped between -1.0 and 1.0.
        """
        try:
            v1 = np.array(vec1, dtype=np.float32)
            v2 = np.array(vec2, dtype=np.float32)

            if v1.shape != v2.shape or len(v1) == 0:
                logger.warning(f"Embedding shape mismatch or empty: {v1.shape} vs {v2.shape}")
                return 0.0

            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            dot_prod = np.dot(v1, v2)
            similarity = float(dot_prod / (norm1 * norm2))
            return max(-1.0, min(1.0, similarity))
        except Exception as e:
            logger.error(f"Error computing cosine similarity: {e}")
            return 0.0

    @classmethod
    def verify_operator_identity(
        cls, 
        live_embedding: np.ndarray | list, 
        stored_embedding: np.ndarray | list, 
        auth_threshold: float = DEFAULT_AUTH_THRESHOLD,
        warning_threshold: float = DEFAULT_WARNING_THRESHOLD
    ) -> tuple[bool, float, str, str]:
        """
        Verifies live camera embedding against stored database embedding.
        Returns: (is_verified: bool, similarity_score: float, status_code: str, display_message: str)
        """
        sim_score = cls.compute_cosine_similarity(live_embedding, stored_embedding)
        rounded_score = round(sim_score, 4)

        if sim_score >= auth_threshold:
            return True, rounded_score, "VERIFIED", f"OPERATOR VERIFIED (Match Confidence: {sim_score*100:.1f}%)"
        elif sim_score >= warning_threshold:
            msg = f"CLEARANCE DENIED: Match similarity ({rounded_score:.3f}) below authentication threshold ({auth_threshold}) but above margin warning."
            return False, rounded_score, "REJECTED_WARNING", msg
        else:
            msg = f"CLEARANCE DENIED: Identity mismatch. Match similarity ({rounded_score:.3f}) below operational threshold ({auth_threshold})."
            return False, rounded_score, "REJECTED_MISMATCH", msg

    @classmethod
    def format_audit_telemetry(
        cls,
        operator_id: str,
        operator_name: str,
        result_status: str,
        similarity_score: float,
        liveness_passed: bool,
        liveness_action: str,
        duration_ms: float,
        camera_quality_metrics: dict,
        ip_address: str = "127.0.0.1"
    ) -> dict:
        """
        Formats secure audit log telemetry without ever exposing or storing raw facial images.
        """
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operator_id": operator_id,
            "operator_name": operator_name,
            "authentication_result": result_status,
            "similarity_score": round(float(similarity_score), 4),
            "liveness_verification": {
                "action_challenged": liveness_action,
                "passed": bool(liveness_passed)
            },
            "duration_ms": round(float(duration_ms), 2),
            "optical_quality": camera_quality_metrics,
            "system_version": cls.SYSTEM_VERSION,
            "workstation_ip": ip_address,
            "security_protocol": "MIL-STD-498 // AIR-GAPPED"
        }
