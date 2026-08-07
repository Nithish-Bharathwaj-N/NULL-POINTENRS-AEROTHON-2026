<div align="center">

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/HAL_Logo.svg/200px-HAL_Logo.svg.png" width="80" alt="HAL Logo"/>

# HAL Aerospace — LCA Tejas Mk1A
## Physics-Informed Digital Twin Platform

**AEROTHON 2026 | Hindustan Aeronautics Limited**

[![React](https://img.shields.io/badge/React-19.0-61DAFB?logo=react&logoColor=white)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.140-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Vite](https://img.shields.io/badge/Vite-6.1-646CFF?logo=vite&logoColor=white)](https://vitejs.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38BDF8?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

*An enterprise-grade, physics-informed digital twin for real-time GE F404-IN20 fighter engine health monitoring, built for HAL Mission Control operations.*

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Platform Features](#platform-features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Frontend Setup](#2-frontend-setup)
  - [3. Backend Setup](#3-backend-setup)
  - [4. Environment Configuration](#4-environment-configuration)
- [Running the Platform](#running-the-platform)
- [Authentication Workflow](#authentication-workflow)
- [Platform Modules](#platform-modules)
- [Default Operators](#default-operators)
- [Recording a Demo](#recording-a-demo)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

---

## Overview

The **HAL Aerospace Digital Twin Platform** is a full-stack, real-time mission control workstation for monitoring and diagnosing the health of the **GE F404-IN20 turbofan engine** on the **LCA Tejas Mk1A** fighter aircraft.

Built for aerospace engineers, propulsion leads, and flight test operators inside Hindustan Aeronautics Limited, the platform delivers:

- **Physics-based engine modelling** (Brayton cycle, isentropic compression/expansion, 0D/1D solver)
- **AI-powered predictive maintenance** (Weibull reliability, Remaining Useful Life prediction)
- **Real-time telemetry streaming** at 60 FPS (N1/N2 RPM, T4 inlet temp, vibration, fuel flow)
- **Military-grade biometric authentication** (Operator ID + Password + Live Face Verification)
- **Interactive 3D digital twin** (SVG cutaway with Normal / X-Ray / Thermal field view modes)
- **Fleet management** across 12 aircraft in 3 squadrons (No. 45 Sqn, No. 18 Sqn, HAL FTC)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   HAL Mission Control Platform                   │
├───────────────────────────┬─────────────────────────────────────┤
│      FRONTEND (React 19)  │         BACKEND (FastAPI)           │
│      Vite + TypeScript    │         Python 3.10+                │
│      TailwindCSS          │         SQLAlchemy + SQLite          │
│      Zustand State        │         JWT Authentication           │
│      ECharts / Recharts   │         Passlib + pbkdf2_sha256      │
│                           │         OpenCV + MediaPipe (opt)     │
│      Port: 3000           │         Port: 8000                  │
└───────────────────────────┴─────────────────────────────────────┘
         │                                      │
         └──────── REST API (JSON) ─────────────┘
                   /api/v1/auth/*
```

---

## Platform Features

| Module | Description |
|--------|-------------|
| 🔐 **Biometric Auth** | 3-factor: Operator ID + Password + Live facial verification |
| ✈️ **Digital Twin Viewport** | Interactive GE F404 SVG cutaway — Normal / X-Ray / Thermal modes |
| 📡 **Live Telemetry** | 60 FPS N1/N2 RPM, T4 temp, vibration, fuel flow, compressor PR |
| 🧠 **AI Diagnostics** | Weibull reliability curves, anomaly scoring, RUL prediction |
| 🔬 **XAI Explainability** | SHAP waterfall charts — top contributing fault factors |
| ⚙️ **Physics Models** | 0D/1D Brayton cycle solver, compressor maps, surge margin |
| 🌳 **Fault Tree** | Causal fault propagation tree (injector → hot spot → creep → fatigue) |
| 🔁 **Mission Replay** | 500-sortie historical replay with compressor surge event simulation |
| 📊 **Historical Trends** | Fleet-wide health degradation curves across 500 sorties |
| 🛩️ **Fleet Management** | 12 aircraft across 3 squadrons with real-time status |
| 🚨 **Active Alerts** | Prioritized alert center (CRITICAL / WARNING / INFO) |
| 🛠️ **Work Orders** | Open maintenance queue with MIL-STD work orders |

---

## Tech Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.0 | UI framework |
| TypeScript | 5.7 | Type safety |
| Vite | 6.1 | Build tool & dev server |
| TailwindCSS | 3.4 | Utility-first styling |
| Zustand | 5.0 | Global state management |
| ECharts | 5.6 | Advanced telemetry charts |
| Recharts | 2.15 | Data visualization |
| Framer Motion | 12.0 | Animations |
| React Router | 7.1 | Navigation |
| TanStack Query | 5.66 | Server state management |
| Lucide React | 0.475 | Icon system |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.140 | REST API framework |
| Uvicorn | 0.51 | ASGI server |
| SQLAlchemy | 2.0 | ORM & database layer |
| SQLite | — | Operator registry database |
| PyJWT | 2.13 | JWT token generation |
| Passlib | 1.7 | Password hashing (pbkdf2_sha256) |
| Pydantic | 2.13 | Request/response validation |
| NumPy | 2.5 | Biometric vector math |
| OpenCV | *(optional)* | Live webcam face capture |
| MediaPipe | *(optional)* | Facial landmark detection |

---

## Prerequisites

Ensure you have the following installed:

| Requirement | Minimum Version | Check Command |
|-------------|----------------|---------------|
| **Node.js** | 20.0+ | `node --version` |
| **npm** | 10.0+ | `npm --version` |
| **Python** | 3.10+ | `python3 --version` |
| **pip** | 23.0+ | `pip --version` |
| **Git** | 2.x | `git --version` |

> **Webcam** is required only for `REAL` biometric mode. `DEMO` mode works without a webcam using seeded operator profiles.

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Nithish-Bharathwaj-N/AEROTHON2026.git
cd AEROTHON2026
```

---

### 2. Frontend Setup

Install all Node.js dependencies:

```bash
npm install
```

This installs React 19, Vite, TailwindCSS, Zustand, ECharts, Playwright, and all other frontend dependencies.

---

### 3. Backend Setup

Create a Python virtual environment and install backend dependencies:

```bash
# Create virtual environment
python3 -m venv backend_venv

# Activate it
# Linux / macOS:
source backend_venv/bin/activate
# Windows:
backend_venv\Scripts\activate

# Install required packages
pip install fastapi uvicorn sqlalchemy pyjwt passlib pydantic requests numpy
```

> **Optional — for REAL biometric mode (live webcam face verification):**
> ```bash
> pip install opencv-python-headless mediapipe
> ```
> *(These are large packages ~300MB. Skip them if using DEMO mode only.)*

---

### 4. Environment Configuration

No `.env` file is required for local development. The platform uses the following defaults:

| Setting | Default | Notes |
|---------|---------|-------|
| Frontend URL | `http://localhost:3000` | Vite dev server |
| Backend URL | `http://localhost:8000` | Uvicorn ASGI server |
| Auth Mode | `DEMO` | Switch to `REAL` for live webcam |
| JWT Secret | Auto-generated | Rotates on each backend restart |
| Database | `./hal_mission_control.db` | Auto-created on first run |

---

## Running the Platform

You need **two terminals** running simultaneously.

### Terminal 1 — Start the Backend (FastAPI)

```bash
# From project root
source backend_venv/bin/activate      # Linux/macOS
# OR: backend_venv\Scripts\activate   # Windows

uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected output:
```
Initializing SQLite Database Tables...
Seeding HAL default military operators into SQLite database...
Successfully seeded 3 default HAL operators.
HAL Aerospace Backend Operational Gateway Ready.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

> **Verify backend is live:** Open [http://localhost:8000](http://localhost:8000)
> ```json
> {"system": "HAL Aerospace Mission Control Backend", "status": "ONLINE // AIR-GAPPED"}
> ```

---

### Terminal 2 — Start the Frontend (Vite)

```bash
# From project root
npm run dev
```

Expected output:
```
  VITE v6.x.x  ready in 800ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://0.0.0.0:3000/
```

> **Open the platform:** [http://localhost:3000](http://localhost:3000)

---

## Authentication Workflow

The platform uses a **3-step biometric authentication workflow**:

```
┌──────────────────────────────────────────────────────────────┐
│  STEP 1: Select Operator + Enter PKI Password                │
│          ↓                                                    │
│  STEP 2: Live Biometric Scan (webcam face verification)      │
│          ↓ (or DEMO mode: auto-verifies with seeded profile) │
│  STEP 3: Clearance Summary → Boot Mission Control            │
└──────────────────────────────────────────────────────────────┘
```

### Authentication Modes

| Mode | Description | Use When |
|------|-------------|----------|
| **DEMO** | Uses pre-seeded operator profiles. No webcam required. Automatically passes face verification. | Hackathons, demos, presentations, development |
| **REAL** | Requires live webcam. Captures your face and compares against registered embedding. | Production, actual operator onboarding |

### Switching Modes

On the workstation login screen, toggle between `[ REAL // WEBCAM ]` and `[ DEMO // SEEDED ]` using the mode button in the top-right of the auth panel.

---

## Default Operators

Three operators are auto-seeded into the database on first backend startup:

| Operator | ID | Password | Role | Squadron |
|----------|----|----------|------|----------|
| Wgd Cdr S. Rao | `USR-8821` | `commander2026` | COMMANDER | No. 45 Sqn (Flying Daggers) |
| Sqn Ldr K. Sharma | `USR-4402` | `engineer2026` | ENGINEER | No. 18 Sqn (Flying Bullets) |
| Flt Lt M. Varma | `USR-9104` | `analyst2026` | ANALYST | HAL Overhaul & Maintenance |

> These credentials work in **both DEMO and REAL** mode for logging in.
> In REAL mode, you must also register your face using the **Register New Operator** button on the workstation.

### Registering a New Operator (REAL mode)

1. Click **"Register New Operator"** on the auth screen
2. Fill in: Operator ID, Employee ID, Full Name, Role, Callsign, Squadron, Password
3. Allow webcam access — the system captures 3 facial frames and stores a normalized embedding
4. Use your credentials to log in with live face verification

---

## Platform Modules

Once authenticated, the sidebar navigates to these modules:

| Nav Item | Module | Description |
|----------|--------|-------------|
| **MISSION OVERVIEW** | `OverviewView` | Dashboard: KPIs, CAD viewport, telemetry, alerts |
| **3D DIGITAL TWIN** | `TwinView` | Full-screen interactive GE F404 CAD + stage inspector |
| **LIVE TELEMETRY** | `TelemetryView` | 60 FPS streaming charts for all 12 transducer channels |
| **ENGINE ANALYSIS** | `EngineAnalysisView` | Thermodynamic cycle efficiency, compressor maps |
| **AI DIAGNOSTICS** | `AiDiagnosticsView` | Weibull RUL, anomaly scoring, maintenance recommendations |
| **EXPLAINABILITY** | `ExplainabilityView` | SHAP waterfall, feature importance rankings |
| **PHYSICS MODELS** | `PhysicsView` | 0D/1D Brayton cycle solver, isentropic calculations |
| **ROOT CAUSE** | `InvestigationView` | Causal fault propagation tree |
| **MISSION REPLAY** | `ReplayView` | Historical sortie replay with event scrubbing |
| **HISTORICAL** | `HistoricalView` | 500-sortie fleet health trend analysis |
| **EVENT TIMELINE** | `EventTimelineView` | Chronological sortie event log |
| **FLEET** | `FleetView` | 12-aircraft fleet matrix, status, maintenance queue |
| **ACTIVE ALERTS** | `AlertsView` | Prioritized alert center (CRITICAL / WARNING / INFO) |
| **MAINTENANCE** | `MaintenanceView` | Open MIL-STD work orders and schedules |
| **SETTINGS** | `SettingsView` | HUD configuration, display options |

---

## Recording a Demo

The platform includes a Playwright-based **cinematic demo director** that auto-navigates through all 19 scenes and records a Full HD 1920×1080 video.

### Setup

```bash
# Install Playwright Chromium browser
npx playwright install chromium
```

### Run the Recording

Make sure both backend (port 8000) and frontend (port 3000) are running, then:

```bash
node record_cinematic_demo.mjs
```

The script will:
1. Launch a headless Chromium browser at 1920×1080
2. Navigate through all 19 scenes with human-like cursor movements
3. Save the recording to `./demo_recordings/` as a `.webm` file

> **Output:** `./demo_recordings/hal_aerospace_demo.webm` (~40MB, ~7 minutes)

Open the `.webm` with any modern browser (Chrome, Firefox) or VLC media player.

---

## Project Structure

```
AEROTHON2026/
├── backend/                          # FastAPI Backend
│   ├── main.py                       # App entry point, DB seeding, CORS
│   └── auth/
│       ├── models.py                 # SQLAlchemy Operator model
│       ├── routes.py                 # API endpoints (/register, /login/*)
│       ├── services.py               # Auth business logic
│       ├── jwt_service.py            # JWT token creation & validation
│       ├── password_service.py       # pbkdf2_sha256 hashing
│       ├── face_encoding.py          # Base64 → OpenCV image decode
│       ├── face_verification.py      # Cosine similarity + liveness check
│       ├── biometric_engine.py       # Unified biometric facade
│       ├── embedding_service.py      # InsightFace/fallback embedding
│       ├── registration.py           # Multi-frame operator enrollment
│       └── verification.py           # Challenge-response verification
│
├── src/                              # React Frontend
│   ├── app/
│   │   ├── App.tsx                   # Root component + auth gate
│   │   └── router.tsx                # React Router configuration
│   ├── features/
│   │   ├── auth/                     # Authentication workstation
│   │   │   ├── MissionAccessWorkstation.tsx
│   │   │   └── components/
│   │   │       ├── LiveWebcamScanner.tsx
│   │   │       ├── BiometricScanner.tsx
│   │   │       ├── OperatorRegistrationModal.tsx
│   │   │       ├── ServiceLoader.tsx
│   │   │       └── LcaTejasWireframe.tsx
│   │   ├── overview/                 # Mission Overview Dashboard
│   │   ├── digital-twin/             # Full 3D Digital Twin view
│   │   ├── telemetry/                # Live telemetry streaming
│   │   ├── engine-analysis/          # Thermodynamic analysis
│   │   ├── ai-diagnostics/           # AI predictive maintenance
│   │   ├── explainability/           # XAI SHAP charts
│   │   ├── physics/                  # Physics solver
│   │   ├── investigation/            # Fault tree analysis
│   │   ├── replay/                   # Mission replay
│   │   ├── historical/               # Historical trends
│   │   ├── event-timeline/           # Event log
│   │   ├── fleet/                    # Fleet management
│   │   ├── alerts/                   # Active alerts
│   │   ├── maintenance/              # Work orders
│   │   └── settings/                 # HUD settings
│   ├── stores/                       # Zustand global state
│   │   ├── useAuthStore.ts           # JWT token, operator profile
│   │   ├── useMissionStore.ts        # Telemetry, alerts, subsystems
│   │   ├── useAircraftStore.ts       # Active aircraft
│   │   ├── useTelemetryStore.ts      # Live sensor streams
│   │   └── useUiStore.ts             # UI state (selected stage, etc.)
│   ├── services/
│   │   ├── apiClient.ts              # Axios/fetch wrapper for backend
│   │   ├── missionEngine.ts          # Real-time mission data engine
│   │   ├── missionEventBus.ts        # Cross-module event system
│   │   ├── missionPlaybackEngine.ts  # Replay scrubbing engine
│   │   ├── telemetryService.ts       # Telemetry stream manager
│   │   └── aiService.ts              # AI diagnostics client
│   ├── constants/
│   │   ├── operationalBaseline.ts    # 12-aircraft fleet data
│   │   ├── missionDataset.ts         # 500-sortie historical dataset
│   │   └── mockData.ts               # Engine parameters & thresholds
│   └── types/                        # TypeScript type definitions
│
├── record_cinematic_demo.mjs         # Playwright demo recording director
├── package.json                      # Frontend dependencies
├── vite.config.ts                    # Vite configuration
├── tailwind.config.js                # TailwindCSS configuration
├── tsconfig.json                     # TypeScript configuration
└── .gitignore                        # Excludes node_modules, venv, DB, recordings
```

---

## API Reference

### Base URL: `http://localhost:8000/api/v1/auth`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Backend health check |
| `GET` | `/api/v1/auth/config` | Get current auth mode (REAL/DEMO) |
| `POST` | `/api/v1/auth/config` | Switch auth mode |
| `GET` | `/api/v1/auth/operators` | List all registered operators |
| `POST` | `/api/v1/auth/register` | Enroll new operator with face embedding |
| `POST` | `/api/v1/auth/login/initiate` | Step 1: Validate credentials, get challenge |
| `POST` | `/api/v1/auth/login/verify-face` | Step 2: Verify face frame, receive JWT |

### Example: Login Initiate
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "operator_id": "USR-8821",
    "password": "commander2026",
    "auth_mode": "DEMO"
  }'
```

**Response:**
```json
{
  "success": true,
  "challenge_id": "f14a33f3805d416b9aa3859638fb19c6",
  "liveness_action": "TURN_RIGHT",
  "operator": {
    "id": "USR-8821",
    "name": "Wgd Cdr S. Rao (Chief Propulsion Lead)",
    "role": "COMMANDER",
    "callsign": "DAGGER-LEAD",
    "squadron": "No. 45 Sqn (Flying Daggers)"
  },
  "similarity_threshold": 0.7
}
```

> **Interactive API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)

---

## Troubleshooting

### ❌ "Could not connect to military backend on port 8000"

The frontend cannot reach the backend. Fix:
```bash
# Make sure backend is running:
source backend_venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Verify it's up:
curl http://localhost:8000/
```

### ❌ "No module named 'cv2'" on backend startup

OpenCV is optional. The backend will start without it using graceful fallback. If you need REAL biometric mode:
```bash
pip install opencv-python-headless
```

### ❌ "password cannot be longer than 72 bytes" (bcrypt error)

Your `bcrypt` version is incompatible. The backend now uses `pbkdf2_sha256` — no action needed. If you see this with an old install, delete `hal_mission_control.db` and restart the backend.

### ❌ Frontend shows blank screen / 404

Ensure Vite is running on port 3000:
```bash
npm run dev
```
Then open [http://localhost:3000](http://localhost:3000).

### ❌ Playwright recording fails to launch

Install the Chromium browser binary:
```bash
npx playwright install chromium
```

### ❌ Git push authentication failed

GitHub no longer accepts passwords. Use SSH (recommended):
```bash
# Test SSH connection
ssh -T git@github.com

# If not set up, follow: https://docs.github.com/en/authentication/connecting-to-github-with-ssh
```

---

## License

MIT License — © 2026 Nithish Bharathwaj N | AEROTHON 2026

---

<div align="center">

**Built for AEROTHON 2026 | Hindustan Aeronautics Limited**

*LCA Tejas Mk1A · GE F404-IN20 · Physics-Informed Digital Twin · Mission Control*

</div>
