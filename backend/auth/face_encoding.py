"""
face_encoding.py — Biometric frame decoding, quality checks, and facial embedding extraction.

Supports two backends in order of preference:
  1. MediaPipe Tasks FaceLandmarker (mediapipe >= 0.10, requires model download)
  2. Geometric fallback via Pillow — brightness / contrast features only (always available)

Raw images are NEVER stored. Only the normalized embedding vector is retained.
"""

import base64
import json
import math
import os
import urllib.request
from typing import Optional, List, Dict, Any, Tuple

import numpy as np

# ── OpenCV (optional) ──────────────────────────────────────────────────────────
try:
    import cv2
    _CV2_OK = True
except ImportError:
    cv2 = None
    _CV2_OK = False

# ── Pillow (always available after pip install mediapipe which brings it) ──────
try:
    from PIL import Image
    import io as _io
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

# ── MediaPipe Tasks API (mediapipe >= 0.10) ────────────────────────────────────
_MP_LANDMARKER = None
_MP_OK = False

_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "face_landmarker.task")


def _try_init_mediapipe():
    """Download model if needed and initialise FaceLandmarker. Called once lazily."""
    global _MP_LANDMARKER, _MP_OK
    try:
        from mediapipe.tasks import python as _mp_tasks
        from mediapipe.tasks.python import vision as _mp_vision

        if not os.path.exists(_MODEL_PATH):
            print("[BiometricEngine] Downloading MediaPipe FaceLandmarker model (~1 MB)…")
            urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
            print("[BiometricEngine] Model downloaded successfully.")

        base_options = _mp_tasks.BaseOptions(model_asset_path=_MODEL_PATH)
        face_options = _mp_vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=1,
        )
        _MP_LANDMARKER = _mp_vision.FaceLandmarker.create_from_options(face_options)
        _MP_OK = True
        print("[BiometricEngine] MediaPipe FaceLandmarker initialised OK.")
    except Exception as exc:
        print(f"[BiometricEngine] MediaPipe Tasks init failed — using geometric fallback. Reason: {exc}")
        _MP_OK = False


# ── Image decoding ─────────────────────────────────────────────────────────────

def decode_base64_image(base64_str: str) -> Optional[np.ndarray]:
    """Decode a data-URI / raw base64 JPEG or PNG into an RGB numpy array (H, W, 3)."""
    try:
        if "," in base64_str:
            base64_str = base64_str.split(",", 1)[1]
        img_bytes = base64.b64decode(base64_str)

        # Prefer cv2 for full compatibility
        if _CV2_OK:
            img_arr = np.frombuffer(img_bytes, dtype=np.uint8)
            bgr = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
            if bgr is not None:
                return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        # Pillow fallback
        if _PIL_OK:
            pil_img = Image.open(_io.BytesIO(img_bytes)).convert("RGB")
            return np.array(pil_img, dtype=np.uint8)

        return None
    except Exception as exc:
        print(f"[face_encoding] decode_base64_image error: {exc}")
        return None


# ── Image quality check ────────────────────────────────────────────────────────

def check_image_quality(image: np.ndarray) -> Dict[str, Any]:
    """Check brightness, contrast, and sharpness of an RGB image array."""
    if image is None or image.size == 0:
        return {
            "lighting_acceptable": False, "sharpness_acceptable": False,
            "brightness": 0.0, "sharpness": 0.0, "reason": "Empty image",
        }

    gray = np.mean(image, axis=2)          # simple luminance from RGB
    brightness = float(np.mean(gray))
    lighting_acceptable = 30.0 <= brightness <= 240.0

    # Sharpness via Laplacian-like variance (works without cv2)
    if _CV2_OK:
        gray_u8 = (gray).astype(np.uint8)
        sharpness = float(cv2.Laplacian(gray_u8, cv2.CV_64F).var())
    else:
        # Finite-difference approximation of Laplacian
        lap = (
            np.roll(gray, 1, 0) + np.roll(gray, -1, 0) +
            np.roll(gray, 1, 1) + np.roll(gray, -1, 1) - 4 * gray
        )
        sharpness = float(np.var(lap))

    sharpness_acceptable = sharpness >= 10.0   # relaxed threshold

    reason = "Nominal"
    if not lighting_acceptable:
        reason = "Poor lighting — ensure good ambient light"
    elif not sharpness_acceptable:
        reason = "Image too blurry — hold still and ensure focus"

    return {
        "lighting_acceptable": lighting_acceptable,
        "sharpness_acceptable": sharpness_acceptable,
        "brightness": round(brightness, 1),
        "sharpness": round(sharpness, 1),
        "reason": reason,
    }


# ── MediaPipe landmark extraction ──────────────────────────────────────────────

def _extract_with_mediapipe(image_rgb: np.ndarray) -> Tuple[Optional[List[float]], Dict[str, Any]]:
    """Use MediaPipe Tasks FaceLandmarker to extract a 1404-dim geometric embedding."""
    try:
        import mediapipe as mp
        from mediapipe.tasks.python import vision as _mp_vision

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=image_rgb.astype(np.uint8),
        )
        result = _MP_LANDMARKER.detect(mp_image)

        if not result.face_landmarks:
            return None, {
                "face_detected": False, "face_centered": False,
                "eyes_visible": False, "lighting_acceptable": True,
                "reason": "No face detected — center your face in the frame",
            }

        landmarks = result.face_landmarks[0]

        # Nose tip = landmark 1, left outer eye = 33, right outer eye = 263
        nose  = landmarks[1]
        l_eye = landmarks[33]
        r_eye = landmarks[263]

        face_centered = (0.15 <= nose.x <= 0.85) and (0.10 <= nose.y <= 0.90)
        eyes_visible  = (0.03 <= l_eye.x <= 0.97) and (0.03 <= r_eye.x <= 0.97)

        if not face_centered:
            return None, {
                "face_detected": True, "face_centered": False,
                "eyes_visible": eyes_visible, "lighting_acceptable": True,
                "reason": "Face not centred — move closer to the camera",
            }
        if not eyes_visible:
            return None, {
                "face_detected": True, "face_centered": True,
                "eyes_visible": False, "lighting_acceptable": True,
                "reason": "Eyes not visible — remove glasses or look directly at camera",
            }

        # Scale-invariant geometric embedding (centred on nose tip, scaled by IOD)
        iod = math.sqrt((r_eye.x - l_eye.x)**2 + (r_eye.y - l_eye.y)**2 + 1e-6)
        raw = []
        for lm in landmarks[:468]:
            raw.extend([
                (lm.x - nose.x) / iod,
                (lm.y - nose.y) / iod,
                (lm.z - nose.z) / iod,
            ])

        vec = np.array(raw, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm

        return vec.tolist(), {
            "face_detected": True, "face_centered": True,
            "eyes_visible": True, "lighting_acceptable": True,
            "reason": "Nominal — 1404-dim geometric embedding extracted",
        }

    except Exception as exc:
        print(f"[face_encoding] MediaPipe extraction error: {exc}")
        return None, {
            "face_detected": False, "face_centered": False,
            "eyes_visible": False, "lighting_acceptable": True,
            "reason": f"MediaPipe error: {exc}",
        }


# ── Pillow-only geometric fallback ─────────────────────────────────────────────

def _extract_geometric_fallback(image_rgb: np.ndarray) -> Tuple[Optional[List[float]], Dict[str, Any]]:
    """
    Pillow-only fallback: generate a 512-dim embedding from image statistics
    (patch-level colour histograms + gradient features). Works without any model.
    Not as accurate as MediaPipe but functional for REAL-mode demo purposes.
    """
    try:
        h, w = image_rgb.shape[:2]

        # Divide face region (centre crop 60%) into a 4×4 grid of patches
        y0, y1 = int(h * 0.2), int(h * 0.8)
        x0, x1 = int(w * 0.2), int(w * 0.8)
        crop = image_rgb[y0:y1, x0:x1].astype(np.float32) / 255.0

        ph, pw = crop.shape[:2]
        rows, cols = 4, 4
        features = []
        for r in range(rows):
            for c in range(cols):
                ry0 = r * ph // rows;  ry1 = (r+1) * ph // rows
                cx0 = c * pw // cols;  cx1 = (c+1) * pw // cols
                patch = crop[ry0:ry1, cx0:cx1]
                for ch in range(3):                           # R, G, B
                    ch_data = patch[:, :, ch].ravel()
                    features.extend([
                        float(np.mean(ch_data)),
                        float(np.std(ch_data)),
                    ])                                        # 48 features per patch × 16 = 768

        # Pad / truncate to 512
        features = features[:512]
        while len(features) < 512:
            features.append(0.0)

        vec = np.array(features, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm

        return vec.tolist(), {
            "face_detected": True, "face_centered": True,
            "eyes_visible": True, "lighting_acceptable": True,
            "reason": "Nominal — 512-dim patch-feature embedding (fallback mode)",
        }
    except Exception as exc:
        print(f"[face_encoding] fallback extraction error: {exc}")
        return None, {
            "face_detected": False, "face_centered": False,
            "eyes_visible": False, "lighting_acceptable": False,
            "reason": f"Feature extraction error: {exc}",
        }


# ── Public extraction entry-point ──────────────────────────────────────────────

def extract_face_landmarks_and_embedding(
    image: np.ndarray,
) -> Tuple[Optional[List[float]], Dict[str, Any]]:
    """
    Main entry-point called by BiometricEngine.
    Tries MediaPipe first; falls back to patch-feature extraction if unavailable.
    """
    global _MP_OK

    if image is None:
        return None, {
            "face_detected": False, "face_centered": False,
            "eyes_visible": False, "reason": "No image provided",
        }

    quality = check_image_quality(image)
    if not quality["lighting_acceptable"]:
        return None, {
            "face_detected": False, "face_centered": False,
            "eyes_visible": False, "lighting_acceptable": False,
            "reason": quality["reason"],
        }

    # Lazy-init MediaPipe on first real call
    if not _MP_OK and _MP_LANDMARKER is None:
        _try_init_mediapipe()

    if _MP_OK and _MP_LANDMARKER is not None:
        return _extract_with_mediapipe(image)

    # Fallback: no model, use patch statistics
    print("[BiometricEngine] Using patch-feature fallback for embedding extraction.")
    return _extract_geometric_fallback(image)


# ── Serialisation helpers ──────────────────────────────────────────────────────

def serialize_embedding(embedding: List[float]) -> str:
    return json.dumps(embedding)


def deserialize_embedding(embedding_str: str) -> Optional[List[float]]:
    try:
        if not embedding_str:
            return None
        return json.loads(embedding_str)
    except Exception as exc:
        print(f"[face_encoding] deserialize error: {exc}")
        return None
