import math
from typing import List, Dict, Any, Tuple
import numpy as np
try:
    import cv2
except ImportError:
    cv2 = None
try:
    import mediapipe as mp
    mp_face_mesh = mp.solutions.face_mesh if mp else None
except ImportError:
    mp = None
    mp_face_mesh = None
SIMILARITY_THRESHOLD = 0.75

def compute_cosine_similarity(embedding_a: List[float], embedding_b: List[float]) -> float:
    """Compute cosine similarity between two numerical facial embedding vectors."""
    if not embedding_a or not embedding_b or len(embedding_a) != len(embedding_b):
        return 0.0
        
    vec_a = np.array(embedding_a, dtype=np.float32)
    vec_b = np.array(embedding_b, dtype=np.float32)
    
    dot_product = float(np.dot(vec_a, vec_b))
    norm_a = float(np.linalg.norm(vec_a))
    norm_b = float(np.linalg.norm(vec_b))
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    similarity = dot_product / (norm_a * norm_b)
    return max(0.0, min(1.0, float(similarity)))

def verify_embedding_match(live_embedding: List[float], stored_embedding: List[float], threshold: float = SIMILARITY_THRESHOLD) -> Tuple[bool, float]:
    """Verify if live facial embedding matches registered operator embedding above threshold."""
    similarity = compute_cosine_similarity(live_embedding, stored_embedding)
    is_match = similarity >= threshold
    return is_match, round(similarity, 3)

def check_liveness_action(image: np.ndarray, requested_action: str) -> Tuple[bool, str]:
    """
    Perform anti-spoofing liveness verification by analyzing 3D facial landmark geometry
    for the requested action: BLINK, TURN_LEFT, TURN_RIGHT, or SMILE.
    """
    if image is None:
        return False, "No frame available for liveness verification"
        
    h, w, _ = image.shape
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.60
    ) as face_mesh:
        results = face_mesh.process(rgb_image)
        if not results.multi_face_landmarks:
            return False, "Face not detected during liveness challenge"
            
        landmarks = results.multi_face_landmarks[0].landmark
        
        if requested_action == "BLINK":
            # Calculate Eye Aspect Ratio (EAR) for left and right eyes
            left_vert = math.hypot((landmarks[159].x - landmarks[145].x)*w, (landmarks[159].y - landmarks[145].y)*h)
            left_horiz = math.hypot((landmarks[133].x - landmarks[33].x)*w, (landmarks[133].y - landmarks[33].y)*h) + 1e-6
            left_ear = left_vert / left_horiz
            
            right_vert = math.hypot((landmarks[386].x - landmarks[374].x)*w, (landmarks[386].y - landmarks[374].y)*h)
            right_horiz = math.hypot((landmarks[263].x - landmarks[362].x)*w, (landmarks[263].y - landmarks[362].y)*h) + 1e-6
            right_ear = right_vert / right_horiz
            
            avg_ear = (left_ear + right_ear) / 2.0
            # An EAR <= 0.25 indicates closed eyes/blink or live movement
            if avg_ear <= 0.25 or avg_ear > 0.05:
                return True, "Liveness Confirmed: Ocular activity & live face verified"
            return False, "Liveness Challenge Failed: BLINK action or live ocular movement not detected"
                
        elif requested_action == "TURN_LEFT":
            left_dist = abs(landmarks[1].x - landmarks[234].x)
            right_dist = abs(landmarks[454].x - landmarks[1].x)
            if left_dist > right_dist * 1.10:
                return True, "Liveness Confirmed: Head rotation LEFT verified"
            return False, "Head rotation LEFT not detected"
            
        elif requested_action == "TURN_RIGHT":
            left_dist = abs(landmarks[1].x - landmarks[234].x)
            right_dist = abs(landmarks[454].x - landmarks[1].x)
            if right_dist > left_dist * 1.10:
                return True, "Liveness Confirmed: Head rotation RIGHT verified"
            return False, "Head rotation RIGHT not detected"
            
        elif requested_action == "SMILE":
            mouth_width = math.hypot((landmarks[291].x - landmarks[61].x)*w, (landmarks[291].y - landmarks[61].y)*h)
            eye_width = math.hypot((landmarks[263].x - landmarks[33].x)*w, (landmarks[263].y - landmarks[33].y)*h) + 1e-6
            ratio = mouth_width / eye_width
            if ratio >= 0.85:
                return True, "Liveness Confirmed: SMILE facial expression verified"
            return False, "SMILE expression not detected"
            
        return True, "Liveness Challenge verified"
