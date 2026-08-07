# HAL Mission Control - Enterprise Optical Quality Validation & Face Alignment Service
# Enforces aerospace military standards for biometric capture quality before neural network embedding

import numpy as np
try:
    import cv2
except ImportError:
    cv2 = None
import logging

logger = logging.getLogger("hal_biometric_alignment")

class OpticalQualityValidator:
    """
    Validates optical capture parameters: blur, lighting, bounding box scale, multi-face rejection, and head rotation pose.
    """
    MIN_FACE_SIZE_PX = 30
    MAX_FRAME_RATIO = 0.98
    MIN_LUMINANCE = 5.0
    MAX_LUMINANCE = 250.0
    MIN_LAPLACIAN_VARIANCE = 5.0   # Relaxed blur threshold for webcams
    MAX_POSE_ASYMMETRY = 2.5       # Yaw/Rotation threshold

    @classmethod
    def check_face_count(cls, num_faces: int) -> tuple[bool, str]:
        if num_faces == 0:
            return False, "QUALITY_REJECTED: No operator face detected in workstation optical feed."
        if num_faces > 1:
            return False, f"QUALITY_REJECTED: Multiple faces ({num_faces}) detected. Enforce single-operator cockpit protocol."
        return True, "NOMINAL_SINGLE_FACE"

    @classmethod
    def validate_capture(
        cls, 
        frame_bgr: np.ndarray, 
        bbox: tuple[int, int, int, int], 
        landmarks: np.ndarray | None = None,
        detection_score: float = 0.90
    ) -> tuple[bool, str, dict]:
        """
        Validates a detected face against military optical standards.
        bbox format: (x1, y1, x2, y2)
        """
        metrics = {
            "blur_variance": 0.0,
            "mean_luminance": 0.0,
            "face_width_px": 0,
            "face_height_px": 0,
            "frame_area_ratio": 0.0,
            "pose_symmetry_ratio": 1.0,
            "detection_confidence": float(detection_score)
        }

        if frame_bgr is None or frame_bgr.size == 0:
            return False, "QUALITY_REJECTED: Null or unreadable camera video frame.", metrics

        frame_height, frame_width = frame_bgr.shape[:2]
        frame_area = max(1, frame_width * frame_height)

        x1, y1, x2, y2 = bbox
        face_width = max(0, x2 - x1)
        face_height = max(0, y2 - y1)
        face_area = face_width * face_height

        metrics["face_width_px"] = face_width
        metrics["face_height_px"] = face_height
        metrics["frame_area_ratio"] = round(face_area / frame_area, 4)

        # 1. Detection Confidence Check
        if detection_score < 0.75:
            return False, f"QUALITY_REJECTED: Biometric detection confidence too low ({detection_score:.2f} < 0.75). Align face properly.", metrics

        # 2. Bounding Box Scale Check
        if face_width < cls.MIN_FACE_SIZE_PX or face_height < cls.MIN_FACE_SIZE_PX:
            return False, f"QUALITY_REJECTED: Face bounding box too small ({face_width}x{face_height}px < {cls.MIN_FACE_SIZE_PX}px). Move closer to workstation scanner.", metrics

        if metrics["frame_area_ratio"] > cls.MAX_FRAME_RATIO:
            return False, f"QUALITY_REJECTED: Face too close to optical scanner ({metrics['frame_area_ratio']*100:.1f}% frame area). Maintain standard posture.", metrics

        # Crop face region for optical analysis
        cx1, cy1 = max(0, x1), max(0, y1)
        cx2, cy2 = min(frame_width, x2), min(frame_height, y2)
        face_roi = frame_bgr[cy1:cy2, cx1:cx2]

        if face_roi.size == 0:
            return False, "QUALITY_REJECTED: Facial boundary crop failed.", metrics

        # 3. Illumination / Brightness Check (cv2-optional: use numpy mean luminance)
        # Works for both BGR and RGB arrays — luminance mean is colour-order agnostic
        mean_lum = float(np.mean(face_roi))
        metrics["mean_luminance"] = round(mean_lum, 2)

        if mean_lum < cls.MIN_LUMINANCE:
            return False, f"QUALITY_REJECTED: Lighting under-exposed (Luminance {mean_lum:.1f} < {cls.MIN_LUMINANCE}). Increase ambient light.", metrics
        if mean_lum > cls.MAX_LUMINANCE:
            return False, f"QUALITY_REJECTED: Lighting over-exposed (Luminance {mean_lum:.1f} > {cls.MAX_LUMINANCE}). Reduce glare.", metrics

        # 4. Blur / Focus Check via Laplacian approximation (numpy, no cv2 required)
        gray_roi_lum = np.mean(face_roi.astype(np.float32), axis=2)
        lap = (
            np.roll(gray_roi_lum, 1, 0) + np.roll(gray_roi_lum, -1, 0) +
            np.roll(gray_roi_lum, 1, 1) + np.roll(gray_roi_lum, -1, 1) - 4 * gray_roi_lum
        )
        lap_var = float(np.var(lap))
        metrics["blur_variance"] = round(lap_var, 2)

        if lap_var < cls.MIN_LAPLACIAN_VARIANCE:
            return False, f"QUALITY_REJECTED: Motion blur detected (Laplacian var={lap_var:.1f} < {cls.MIN_LAPLACIAN_VARIANCE}). Hold still during scan.", metrics

        # 5. Extreme Head Rotation / Pose Symmetry Check (if 5-point landmarks provided by InsightFace)
        # InsightFace landmarks format: array of shape (5, 2) -> [left_eye, right_eye, nose, left_mouth, right_mouth]
        if landmarks is not None and len(landmarks) == 5:
            left_eye = landmarks[0]
            right_eye = landmarks[1]
            nose = landmarks[2]

            dist_left = np.linalg.norm(nose - left_eye)
            dist_right = np.linalg.norm(nose - right_eye)
            
            if dist_right > 0 and dist_left > 0:
                sym_ratio = max(dist_left / dist_right, dist_right / dist_left)
                metrics["pose_symmetry_ratio"] = round(float(sym_ratio), 3)

                if sym_ratio > cls.MAX_POSE_ASYMMETRY:
                    return False, f"QUALITY_REJECTED: Extreme head yaw/rotation detected (Symmetry ratio {sym_ratio:.2f} > {cls.MAX_POSE_ASYMMETRY}). Face directly toward optical scanner.", metrics

        return True, "OPTICAL_QUALITY_NOMINAL", metrics
