# HAL Mission Control - Enterprise Face Cropping & Alignment Margin Service
# Prepares optical face bounding boxes with aerospace margin tolerances for neural embedding

import numpy as np
try:
    import cv2
except ImportError:
    cv2 = None

class FaceCropper:
    """
    Extracts face bounding box regions with margin padding and standardized resizing for neural embedding.
    """
    DEFAULT_TARGET_SIZE = (112, 112)  # Standard ArcFace input resolution
    DEFAULT_MARGIN_RATIO = 0.15       # 15% padding around facial perimeter

    @classmethod
    def crop_and_pad(
        cls, 
        frame_bgr: np.ndarray, 
        bbox: tuple[int, int, int, int], 
        margin_ratio: float = DEFAULT_MARGIN_RATIO, 
        target_size: tuple[int, int] | None = None
    ) -> np.ndarray:
        """
        Crops face region with proportional padding and optional resizing.
        bbox format: (x1, y1, x2, y2)
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return np.zeros((112, 112, 3), dtype=np.uint8)

        frame_h, frame_w = frame_bgr.shape[:2]
        x1, y1, x2, y2 = bbox

        w = max(0, x2 - x1)
        h = max(0, y2 - y1)

        pad_w = int(w * margin_ratio)
        pad_h = int(h * margin_ratio)

        # Apply padding within frame boundaries
        nx1 = max(0, x1 - pad_w)
        ny1 = max(0, y1 - pad_h)
        nx2 = min(frame_w, x2 + pad_w)
        ny2 = min(frame_h, y2 + pad_h)

        crop_roi = frame_bgr[ny1:ny2, nx1:nx2]

        if crop_roi.size == 0:
            # Fallback to unpadded bbox if padding failed
            crop_roi = frame_bgr[max(0, y1):min(frame_h, y2), max(0, x1):min(frame_w, x2)]
            if crop_roi.size == 0:
                return np.zeros((112, 112, 3), dtype=np.uint8)

        if target_size is not None:
            crop_roi = cv2.resize(crop_roi, target_size, interpolation=cv2.INTER_LINEAR)

        return crop_roi

    @classmethod
    def extract_bbox_from_insightface(cls, face_obj: any) -> tuple[int, int, int, int]:
        """
        Safely extracts integer bounding box (x1, y1, x2, y2) from an InsightFace face object or dict.
        """
        try:
            if hasattr(face_obj, "bbox"):
                bbox = face_obj.bbox
            elif isinstance(face_obj, dict) and "bbox" in face_obj:
                bbox = face_obj["bbox"]
            else:
                return (0, 0, 0, 0)

            x1, y1, x2, y2 = map(int, bbox[:4])
            return (x1, y1, x2, y2)
        except Exception:
            return (0, 0, 0, 0)
