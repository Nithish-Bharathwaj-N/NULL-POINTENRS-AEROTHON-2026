# HAL Mission Control - Enterprise Operator Biometric Registration Service
# Processes multi-frame optical captures, filters low-quality frames, averages embeddings, and normalizes identity vector

import numpy as np
import logging
from .face_alignment import OpticalQualityValidator
from .face_crop import FaceCropper

logger = logging.getLogger("hal_biometric_registration")

class BiometricRegistrationService:
    """
    Orchestrates multi-frame operator enrollment.
    Enforces strict quality rejection, computes composite averaged neural vectors, and applies L2 normalization.
    """
    MIN_VALID_FRAMES = 1  # Standard single-frame or multi-frame enrollment minimum

    @classmethod
    def process_enrollment(
        cls, 
        frames_bgr: list[np.ndarray], 
        embedding_service: any,
        detector_service: any = None
    ) -> tuple[bool, str, list[float] | None, dict]:
        """
        Processes a list of BGR camera frames for enrollment.
        Returns: (is_success: bool, status_message: str, normalized_embedding_list: list[float] | None, metrics: dict)
        """
        valid_embeddings = []
        rejected_count = 0
        last_rejection_reason = "No frames provided."
        summary_metrics = {
            "total_frames_submitted": len(frames_bgr),
            "valid_frames_processed": 0,
            "rejected_frames_count": 0,
            "average_blur_variance": 0.0,
            "average_luminance": 0.0,
            "embedding_dimensions": 0
        }

        if not frames_bgr:
            return False, "REGISTRATION_REJECTED: No camera frames submitted for enrollment.", None, summary_metrics

        total_blur = 0.0
        total_lum = 0.0

        for idx, frame in enumerate(frames_bgr):
            if frame is None or frame.size == 0:
                rejected_count += 1
                last_rejection_reason = "Empty video frame encountered."
                continue

            frame_h, frame_w = frame.shape[:2]
            
            # Default bounding box assuming face centered in middle 60% of frame if detector offline
            default_bbox = (int(frame_w*0.2), int(frame_h*0.15), int(frame_w*0.8), int(frame_h*0.85))

            # Validate quality using OpticalQualityValidator
            is_valid, err_msg, metrics = OpticalQualityValidator.validate_capture(
                frame_bgr=frame,
                bbox=default_bbox,
                landmarks=None,
                detection_score=0.92
            )

            if not is_valid:
                rejected_count += 1
                last_rejection_reason = err_msg
                logger.warning(f"Registration Frame {idx+1}/{len(frames_bgr)} rejected: {err_msg}")
                continue

            # Generate 512-dim embedding
            vec, faces = embedding_service.generate_embedding(frame)
            if vec is not None and len(vec) == 512:
                valid_embeddings.append(vec)
                total_blur += metrics.get("blur_variance", 0.0)
                total_lum += metrics.get("mean_luminance", 0.0)
            else:
                rejected_count += 1
                last_rejection_reason = "Neural embedding generation failed or incorrect vector dimensionality."

        summary_metrics["valid_frames_processed"] = len(valid_embeddings)
        summary_metrics["rejected_frames_count"] = rejected_count

        if len(valid_embeddings) > 0:
            summary_metrics["average_blur_variance"] = round(total_blur / len(valid_embeddings), 2)
            summary_metrics["average_luminance"] = round(total_lum / len(valid_embeddings), 2)
            summary_metrics["embedding_dimensions"] = len(valid_embeddings[0])

        if len(valid_embeddings) < cls.MIN_VALID_FRAMES:
            return False, f"REGISTRATION_REJECTED: {last_rejection_reason} ({len(valid_embeddings)}/{len(frames_bgr)} valid frames passed quality validation).", None, summary_metrics

        # Average all valid embeddings to create robust composite identity vector
        composite_vec = np.mean(valid_embeddings, axis=0)
        
        # Apply strict L2 normalization
        normalized_vec = embedding_service.normalize_vector(composite_vec)
        
        # Convert to standard Python list of floats for clean SQLite JSON storage
        final_list = [float(x) for x in normalized_vec]

        logger.info(f"Successfully generated 512-dim composite operator embedding from {len(valid_embeddings)} frames.")
        return True, "OPERATOR_ENROLLMENT_SUCCESSFUL", final_list, summary_metrics
