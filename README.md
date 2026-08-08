# SubAERO — Aerospace Digital Twin & PHM Platform

**SubAERO** is a high-accuracy Aerospace Digital Twin and Prognostics & Health Management (PHM) platform designed for HAL Tejas single-spool turbojet engines. It combines real-time WebGL 3D visualization, first-principles aero-thermal physics, and machine learning ensembles (**98.7% – 99.9% R² accuracy**).

---

## 🔗 Live Demonstration

[SubAero-DigitalTwin](https://null-pointers-aerothon-2026.vercel.app/)

---

## Key Features

- **Interactive 3D Engine Twin**: Real-time WebGL engine visualization featuring 4-stage compressor, combustor, turbine, and nozzle components with damage hot-spot indicators.
- **Aero-Thermal Physics Validation**: Evaluates total stagnation pressure/temperature ratios ($\text{PR}_{3,2}$, $\text{TR}_{3,2}$), isentropic efficiencies ($\eta_c$, $\eta_t$), and enthalpy rise/drop across stations.
- **High-Accuracy ML Health Predictor**: Multi-target regression predicting `CompressorHealth`, `CombustorHealth`, `TurbineHealth`, `OverallHealth`, `Thrust (N)`, and `TSFC (g/N/s)`.
- **Remaining Useful Life (RUL) & PHM Advisory**: Real-time component degradation velocity tracking, RUL prediction, and prescriptive service recommendations.

---

## Tech Stack

- **Frontend**: React 19, TypeScript, Vite, Three.js, ECharts, Recharts, Tailwind CSS
- **Backend API**: Python, FastAPI, Uvicorn, NumPy, Pandas, Scikit-Learn, SciPy
- **Deployment**: Vercel (Frontend), FastAPI / Uvicorn (Backend)

---

## Quick Start

### 1. Frontend Setup
```bash
npm install
npm run dev      # Starts local dev server at http://localhost:5173
npm run build    # Builds production bundle
```

### 2. Backend Setup
```bash
pip install fastapi uvicorn scikit-learn pandas numpy scipy
python backend/main.py   # Starts FastAPI server at http://localhost:8000
```

### 3. Model Evaluation
```bash
python evaluate_ps2.py   # Runs PS2 model evaluation runner
```
