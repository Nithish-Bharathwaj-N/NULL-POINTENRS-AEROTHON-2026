import datetime
from typing import Optional, Dict, Any
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.auth.models import get_db, Operator

SECRET_KEY = "HAL_IAF_MIL_STD_498_TOP_SECRET_JWT_KEY_2026_ENTERPRISE_SECURED"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/credentials", auto_error=False)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Generate a secure JWT access token with operator identity and clearance role."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iss": "HAL-AEROSPACE-COMMAND-GATEWAY"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def get_current_operator(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Operator:
    """FastAPI dependency to retrieve the authenticated operator from JWT bearer token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate military operator credentials or session expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    operator_id: str = payload.get("sub")
    if operator_id is None:
        raise credentials_exception
        
    operator = db.query(Operator).filter(Operator.operator_id == operator_id).first()
    if operator is None or not operator.is_active:
        raise credentials_exception
        
    return operator
