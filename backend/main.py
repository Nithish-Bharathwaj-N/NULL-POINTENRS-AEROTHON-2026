import sys
import os
import random
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Ensure parent directory is in Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.auth.models import Base, engine, SessionLocal, Operator
from backend.auth.password_service import hash_password
from backend.auth.routes import router as auth_router
from backend.digital_twin.routes import router as twin_router
from backend.auth.face_encoding import serialize_embedding

app = FastAPI(
    title="HAL Aerospace Mission Control - Security & Operational Gateway",
    description="Enterprise Biometric Authentication, Liveness Detection, PKI & AEROTWIN Ω Digital Twin Service",
    version="2026.2.0-PROD"
)

# Configure CORS for Vite React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow local dev ports 5173, 3000, 8080
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(twin_router)

static_models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "digital_twin", "static")
if os.path.exists(static_models_dir):
    app.mount("/static", StaticFiles(directory=static_models_dir), name="static")

@app.on_event("startup")
def on_startup():
    print("Initializing SQLite Database Tables...")
    Base.metadata.create_all(bind=engine)
    print("HAL Aerospace Backend Operational Gateway Ready.")

@app.get("/")
def root():
    return {
        "system": "HAL Aerospace Mission Control Backend",
        "status": "ONLINE // AIR-GAPPED",
        "docs_url": "/docs",
        "api_v1": "/api/v1/auth"
    }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
