import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./hal_mission_control.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Operator(Base):
    __tablename__ = "operators"

    operator_id = Column(String, primary_key=True, index=True)
    employee_id = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # COMMANDER, ENGINEER, ANALYST, ADMIN
    callsign = Column(String, nullable=False)
    squadron = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    face_embedding = Column(Text, nullable=True)  # JSON-encoded string of 468/512 float embedding vector
    registration_date = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(String, index=True, nullable=True)
    event_type = Column(String, nullable=False)  # REGISTER, LOGIN_SUCCESS, LOGIN_FAIL, LIVENESS_FAIL, etc.
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
