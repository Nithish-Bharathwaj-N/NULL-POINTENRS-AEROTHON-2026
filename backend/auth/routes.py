from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.models import get_db, Operator
from backend.auth.services import register_new_operator, initiate_login, verify_login_face, SIMILARITY_THRESHOLD

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Security Gateway"])

# Global Configuration Flag: REAL vs DEMO
# Can be mutated via /config endpoint or environment variable
GLOBAL_AUTH_CONFIG = {
    "auth_mode": "REAL",  # Values: "REAL" | "DEMO"
    "similarity_threshold": SIMILARITY_THRESHOLD,
    "system_status": "MIL-STD-498 COMPLIANT • AIR-GAPPED GATEWAY ONLINE"
}

class RegisterRequest(BaseModel):
    operator_id: str
    employee_id: str
    full_name: str
    role: str = "ENGINEER"
    callsign: Optional[str] = None
    squadron: Optional[str] = None
    password: str
    base64_frame: Optional[str] = None

class LoginInitiateRequest(BaseModel):
    operator_id: str
    password: str
    auth_mode: Optional[str] = None

class LoginVerifyFaceRequest(BaseModel):
    challenge_id: str
    base64_frame: str
    auth_mode: Optional[str] = None

class ConfigUpdateRequest(BaseModel):
    auth_mode: str

@router.get("/config")
def get_auth_config():
    """Retrieve current authentication mode and military threshold configuration."""
    return GLOBAL_AUTH_CONFIG

@router.post("/config")
def update_auth_config(request: ConfigUpdateRequest):
    """Toggle between REAL (live webcam verification) and DEMO (seeded override) mode."""
    if request.auth_mode.upper() not in ["REAL", "DEMO"]:
        raise HTTPException(status_code=400, detail="Invalid AUTH_MODE. Must be REAL or DEMO.")
    GLOBAL_AUTH_CONFIG["auth_mode"] = request.auth_mode.upper()
    return GLOBAL_AUTH_CONFIG

@router.get("/operators")
def list_registered_operators(db: Session = Depends(get_db)):
    """List all enrolled military operators for workstation selection."""
    operators = db.query(Operator).filter(Operator.is_active == True).all()
    return [
        {
            "id": op.operator_id,
            "employee_id": op.employee_id,
            "name": op.full_name,
            "role": op.role,
            "callsign": op.callsign,
            "squadron": op.squadron,
            "has_embedding": bool(op.face_embedding)
        }
        for op in operators
    ]

@router.post("/register")
def register_operator(request: RegisterRequest, http_req: Request, db: Session = Depends(get_db)):
    """Enroll a new operator with password hashing and multi-frame webcam face embedding."""
    ip_addr = http_req.client.host if http_req.client else "127.0.0.1"
    new_op = register_new_operator(db, request.dict(), ip_address=ip_addr)
    return {
        "success": True,
        "message": f"Operator {new_op.full_name} successfully enrolled in IAF PKI & Biometric Database.",
        "operator": {
            "id": new_op.operator_id,
            "name": new_op.full_name,
            "role": new_op.role
        }
    }

@router.post("/login/initiate")
def login_initiate(request: LoginInitiateRequest, http_req: Request, db: Session = Depends(get_db)):
    """Step 1: Validate Operator ID and password, returning session challenge and liveness instruction."""
    ip_addr = http_req.client.host if http_req.client else "127.0.0.1"
    mode = request.auth_mode or GLOBAL_AUTH_CONFIG["auth_mode"]
    return initiate_login(db, request.operator_id, request.password, auth_mode=mode.upper(), ip_address=ip_addr)

@router.post("/login/verify-face")
def login_verify_face(request: LoginVerifyFaceRequest, http_req: Request, db: Session = Depends(get_db)):
    """Step 2: Verify live webcam frame against registered embedding and liveness action. Returns JWT."""
    ip_addr = http_req.client.host if http_req.client else "127.0.0.1"
    mode = request.auth_mode or GLOBAL_AUTH_CONFIG["auth_mode"]
    return verify_login_face(db, request.challenge_id, request.base64_frame, auth_mode=mode.upper(), ip_address=ip_addr)
