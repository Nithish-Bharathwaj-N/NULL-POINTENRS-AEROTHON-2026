from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a plaintext password using pbkdf2_sha256."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)
