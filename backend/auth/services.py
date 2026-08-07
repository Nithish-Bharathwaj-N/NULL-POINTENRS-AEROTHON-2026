import datetime
import random
import uuid
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.auth.models import Operator, AuditLog
from backend.auth.password_service import hash_password, verify_password
from backend.auth.jwt_service import create_access_token
from backend.auth.face_encoding import serialize_embedding, deserialize_embedding, decode_base64_image
from backend.auth.biometric_engine import BiometricEngine

SIMILARITY_THRESHOLD = 0.70

# In-memory session challenge store for two-step authentication
# Mapping challenge_id -> { operator_id, liveness_action, expires }
ACTIVE_CHALLENGES: Dict[str, Dict[str, Any]] = {}

LIVENESS_ACTIONS = ["BLINK", "TURN_LEFT", "TURN_RIGHT", "SMILE"]

def log_audit_event(db: Session, operator_id: Optional[str], event_type: str, details: str, ip_address: str = "127.0.0.1"):
    """Record security and authentication events in the audit log."""
    try:
        log_entry = AuditLog(
            operator_id=operator_id,
            event_type=event_type,
            details=details,
            ip_address=ip_address
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Error writing audit log: {e}")

def register_new_operator(db: Session, data: Dict[str, Any], ip_address: str = "127.0.0.1") -> Operator:
    """Register a new military operator with password hashing and face embedding enrollment."""
    operator_id = data.get("operator_id")
    employee_id = data.get("employee_id")
    full_name = data.get("full_name")
    role = data.get("role", "ENGINEER")
    callsign = data.get("callsign", f"HAL-{operator_id[-4:] if operator_id else 'OPS'}")
    squadron = data.get("squadron", "HAL Propulsion Command")
    password = data.get("password")
    base64_frame = data.get("base64_frame")

    if not operator_id or not employee_id or not full_name or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required registration fields.")

    existing_op = db.query(Operator).filter((Operator.operator_id == operator_id) | (Operator.employee_id == employee_id)).first()
    if existing_op:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Operator ID or Employee ID already registered in database.")

    # Process face frame to extract 512-dim numerical embedding via BiometricEngine
    embedding_str = None
    if base64_frame:
        engine = BiometricEngine.get_instance()
        success, msg, norm_vec_list, quality = engine.enroll_operator([base64_frame])
        if not success or not norm_vec_list:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Face Enrollment Failed: {msg}")
            
        embedding_str = serialize_embedding(norm_vec_list)
    else:
        # If no frame provided in demo/seed registration, generate dummy normalized 512-dim vector
        dummy_vec = [round(random.uniform(-0.5, 0.5), 4) for _ in range(512)]
        embedding_str = serialize_embedding(dummy_vec)

    hashed_pw = hash_password(password)

    new_op = Operator(
        operator_id=operator_id,
        employee_id=employee_id,
        full_name=full_name,
        role=role.upper(),
        callsign=callsign.upper(),
        squadron=squadron,
        password_hash=hashed_pw,
        face_embedding=embedding_str,
        is_active=True
    )

    db.add(new_op)
    db.commit()
    db.refresh(new_op)

    log_audit_event(db, operator_id, "REGISTER_SUCCESS", f"Enrolled operator {full_name} ({role})", ip_address)
    return new_op

def initiate_login(db: Session, operator_id: str, password: str, auth_mode: str = "REAL", ip_address: str = "127.0.0.1") -> Dict[str, Any]:
    """Step 1 of login: Validate credentials and generate a liveness challenge."""
    operator = db.query(Operator).filter(Operator.operator_id == operator_id).first()
    
    if not operator or not operator.is_active:
        log_audit_event(db, operator_id, "LOGIN_INITIATE_FAIL", "Operator not found or inactive", ip_address)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Operator ID or credentials.")

    # In DEMO mode, we allow password bypass or check if valid
    is_valid_pw = verify_password(password, operator.password_hash)
    if not is_valid_pw and auth_mode != "DEMO":
        log_audit_event(db, operator_id, "LOGIN_INITIATE_FAIL", "Invalid PKI/password provided", ip_address)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Operator ID or password.")

    challenge_id = uuid.uuid4().hex
    liveness_action = random.choice(LIVENESS_ACTIONS)
    
    ACTIVE_CHALLENGES[challenge_id] = {
        "operator_id": operator.operator_id,
        "liveness_action": liveness_action,
        "expires": datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
        "attempts": 0
    }

    log_audit_event(db, operator_id, "LOGIN_INITIATE_SUCCESS", f"Credentials validated. Assigned challenge: {liveness_action}", ip_address)

    return {
        "success": True,
        "challenge_id": challenge_id,
        "liveness_action": liveness_action,
        "operator": {
            "id": operator.operator_id,
            "name": operator.full_name,
            "role": operator.role,
            "callsign": operator.callsign,
            "squadron": operator.squadron
        },
        "similarity_threshold": SIMILARITY_THRESHOLD
    }

def verify_login_face(db: Session, challenge_id: str, base64_frame: str, auth_mode: str = "REAL", ip_address: str = "127.0.0.1") -> Dict[str, Any]:
    """Step 2 of login: Verify face quality, liveness challenge, and cosine similarity against database embedding."""
    challenge = ACTIVE_CHALLENGES.get(challenge_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session challenge expired or invalid. Please re-enter credentials.")
        
    if datetime.datetime.utcnow() > challenge["expires"]:
        ACTIVE_CHALLENGES.pop(challenge_id, None)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Biometric challenge verification window expired (300s max).")

    operator_id = challenge["operator_id"]
    liveness_action = challenge["liveness_action"]
    operator = db.query(Operator).filter(Operator.operator_id == operator_id).first()
    
    if not operator:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Operator profile no longer exists in database.")

    # Decode live webcam frame
    image = decode_base64_image(base64_frame)
    if image is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to decode live webcam video frame.")

    # If DEMO mode is enabled, simulate successful biometric matching for seamless presentation
    if auth_mode == "DEMO":
        similarity_score = round(random.uniform(0.92, 0.98), 3)
        quality_metrics = {
            "face_detected": True,
            "face_centered": True,
            "eyes_visible": True,
            "lighting_acceptable": True,
            "sharpness_acceptable": True,
            "brightness": 128.5,
            "reason": "Nominal • Demo Mode Override Active"
        }
    else:
        engine = BiometricEngine.get_instance()
        stored_embedding = deserialize_embedding(operator.face_embedding) if operator.face_embedding else []
        
        # Reject if the operator has not properly enrolled a biometric profile
        if not stored_embedding or len(stored_embedding) != 512:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="No valid biometric profile found for this operator. Please use the ENROLL terminal."
            )

        is_verified, similarity_score, status_code, display_msg, telemetry, quality_metrics = engine.verify_operator_login(
            base64_frame=base64_frame,
            stored_embedding=stored_embedding if len(stored_embedding) == 512 else [],
            liveness_action=liveness_action,
            operator_id=operator.operator_id,
            operator_name=operator.full_name
        )

        # Enforce strict facial identity verification against registered biometric profile
        if not is_verified:
            challenge["attempts"] += 1
            if challenge["attempts"] >= 3:
                ACTIVE_CHALLENGES.pop(challenge_id, None)
            log_audit_event(db, operator_id, f"FACE_VERIFY_FAIL_{status_code}", f"Biometric verification denied: {display_msg}", ip_address)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"BIOMETRIC ACCESS DENIED: Identity Mismatch. Match score ({similarity_score*100:.1f}%) is below security threshold (70.0%). Access denied for unauthorized face."
            )

    # Success: Generate JWT access token
    ACTIVE_CHALLENGES.pop(challenge_id, None)
    operator.last_login = datetime.datetime.utcnow()
    db.commit()

    token_payload = {
        "sub": operator.operator_id,
        "name": operator.full_name,
        "role": operator.role,
        "callsign": operator.callsign,
        "squadron": operator.squadron
    }
    access_token = create_access_token(token_payload)

    log_audit_event(db, operator_id, "LOGIN_SUCCESS", f"Biometric verification successful (Score: {similarity_score})", ip_address)

    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "operator": {
            "id": operator.operator_id,
            "name": operator.full_name,
            "role": operator.role,
            "callsign": operator.callsign,
            "squadron": operator.squadron
        },
        "similarity_score": similarity_score,
        "quality_metrics": quality_metrics,
        "liveness_verified": True
    }
