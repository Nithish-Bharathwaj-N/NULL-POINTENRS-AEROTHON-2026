# ✈️ SubAero: Presentation Pitch Deck & Speaker Guide
### Aerothon 2026 Pitch Document | 10-Slide Deck with Speaker Notes & Judge Q&A

---

## 🎯 Slide 1: Title & Executive Summary
**Slide Title**: SubAero: Physics-Informed Digital Twin & Health Prognostics Engine  
**Subtitle**: 100% White-Box Interpretable Machine Learning for High-Bypass Turbofan Engines  
**Presenter**: Aerothon 2026 Team SubAero  

### Key Visuals / Bullet Points
- **Architecture**: 3-Layer Hybrid Framework (First-Principles Physics $\rightarrow$ White-Box ML $\rightarrow$ Constraint Validator).
- **Core Results**: **$99.44\%$ Accuracy**, **$R^2 = 0.9741$** on held-out unseen engines across 30,000 dataset rows.
- **Interpretability**: Zero Black-Box models — 100% closed-form Polynomial Ridge & Explainable Boosting Machines (EBM).

> 📢 **Speaker Script**:
> *"Good morning, esteemed judges. Today we present **SubAero**, a Physics-Informed Digital Twin for turbofan engine prognostics. In safety-critical aerospace applications, black-box AI is unacceptable. SubAero achieves enterprise-grade accuracy—99.44% on unseen engines—while remaining 100% white-box, mathematically interpretable, and backed by first-principles gas dynamics."*

---

## ⚠️ Slide 2: The Problem – The Aerospace AI Dilemma
**Slide Title**: The Dilemma: Accuracy vs. Interpretability in Aerospace Health Monitoring

### Key Visuals / Bullet Points
1. **Engine Degradation Complexity**: Thermal and mechanical degradation across 300+ flight cycles creates non-linear wear patterns across high-pressure compressors, combustors, and turbines.
2. **The Certification Barrier**: Deep Learning & Black-Box Ensembles (RandomForest, Neural Nets) are non-explainable, making FAA/EASA safety certification impossible.
3. **The Data Leakage Pitfall**: Conventional ML split strategies leak cycle sequences between training and validation engines, giving false 99% training scores that fail on hidden test data.

> 📢 **Speaker Script**:
> *"The fundamental challenge in aviation prognostic AI is that high accuracy usually comes at the cost of opacity. Furthermore, standard ML benchmarks often suffer from data leakage by splitting cycles randomly instead of holding out entire engines. SubAero solves both problems simultaneously."*

---

## 🏗️ Slide 3: System Architecture Overview
**Slide Title**: 3-Layer Hybrid Physics + White-Box ML Pipeline

### Key Visuals / Diagram
```
CSV Telemetry / Live Stream (12 Ambient & Thermodynamic Sensors + Usage Cycle)
                                 │
  ┌──────────────────────────────┴──────────────────────────────┐
  │ LAYER 1: First-Principles Gas Dynamics Engine               │
  │ • Isentropic Efficiency (ηc)  • Temperature Ratio (TR = T3/T2)│
  │ • Turbine Work Coeff (W)     • Air Density Scaling Ratio    │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
  ┌──────────────────────────────┴──────────────────────────────┐
  │ LAYER 2: 100% White-Box Interpretable ML Engine             │
  │ • Degree-2 Polynomial Ridge  • Explainable Boosting (EBM)   │
  │ • Target-Specific Features   • Closed-Form Matrices         │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
  ┌──────────────────────────────┴──────────────────────────────┐
  │ LAYER 3: Bidirectional Physics Constraint Checker           │
  │ • T3 > T2  • T4 < T3  • EGT < 1273.15K  • Health ∈ [0.1, 1.0] │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
         Overall Health (99.44%) | Thrust (99.35%) | RUL Prediction
```

> 📢 **Speaker Script**:
> *"SubAero operates on a 3-Layer Hybrid Architecture. Layer 1 computes first-principles thermodynamic state variables like compressor isentropic efficiency and turbine expansion work. Layer 2 applies white-box ML to predict health degradation. Layer 3 acts as a physical guardian, verifying that every prediction obeys fundamental laws of thermodynamics like energy conservation and thermal limits."*

---

## 💡 Slide 4: Scientific Breakthrough 1 – Feature Allocation & Leakage Prevention
**Slide Title**: Eliminating Rank Deficiency & Target-Specific Feature Engineering

### Key Visuals / Bullet Points
- **Root Cause Identified**: Health degradation correlates with usage count (`Cycle`, $r = -0.96$). Excluding `Cycle` forces models to guess degradation from static ambient temperature variations.
- **Target-Specific Feature Allocation**:
  - **Health Targets** (`Compressor`, `Combustor`, `Turbine`, `Overall`): Raw 12 sensors + `Cycle`.
  - **Performance Targets** (`Thrust_N`, `TSFC`): Raw 12 sensors (flight point dependent).
- **Collinearity Removal**: Removed duplicate pressure ratios ($\text{PR}_{3,2} \equiv \text{PR}_{\text{compressor}}$, $r = 1.00$) which previously caused singular matrix inversion.

> 📢 **Speaker Script**:
> *"Our first major breakthrough was discovering why existing models stalled at 64% accuracy. Health degradation is cumulative over time, correlating with usage cycles at r = -0.96. By pairing cycle progression with raw sensor telemetry and stripping out collinear duplicate features, we restored mathematical rank stability to our regression matrices."*

---

## 🔬 Slide 5: Scientific Breakthrough 2 – 100% White-Box Mathematics
**Slide Title**: Transparent Mathematics: Closed-Form Degree-2 Polynomial Ridge

### Key Visuals / Formula
Every prediction in SubAero is a readable, deterministic mathematical equation:

$$\hat{y} = \beta_0 + \sum_{i=1}^{13} \beta_i x_i + \sum_{i=1}^{13} \sum_{j=i}^{13} \gamma_{ij} x_i x_j$$

- **Number of Terms**: Exactly 104 explicit linear and quadratic cross-terms.
- **Model Properties**:
  - Closed-form solution: $\hat{\beta} = (X^T X + \alpha I)^{-1} X^T y$
  - Fully inspectable coefficients ($\beta_0, \beta_i, \gamma_{ij}$).
  - 0ms inference latency (exportable to 104-element dot product in TypeScript/C++).

> 📢 **Speaker Script**:
> *"Notice there are no hidden layers, no decision trees, and no random seeds in inference. Every single prediction is an explicit polynomial dot product with 104 readable coefficients. This allows aerospace engineers to audit the exact weight of every sensor interaction."*

---

## 📊 Slide 6: Validation Methodology – GroupKFold by EngineID
**Slide Title**: Leak-Free Validation on 30,000 Dataset Rows

### Key Visuals / Bullet Points
- **Dataset Size**: 100 Physical Turbofan Engines × 300 Cycles = **30,000 Total Rows**.
- **Split Strategy**: 5-Fold `GroupKFold` partitioned strictly by `EngineID`.
  - **Train**: 80 Engines (24,000 rows).
  - **Test**: 20 Unseen Engines (6,000 rows).
- **Zero Contamination**: Training folds never observe any flight cycle belonging to test engines.

> 📢 **Speaker Script**:
> *"To ensure true performance on hidden evaluation data, we strictly enforce GroupKFold validation by Engine ID. Our test set consists of 20 completely unseen engines. When our model scores 99.4% accuracy, it is predicting on physical engines it has never encountered before."*

---

## 🏆 Slide 7: Empirical Results & Benchmark Table
**Slide Title**: Empirical Performance on Unseen Test Engines (30,000 Rows)

### Key Visuals / Results Table

| Target Variable | MAE | RMSE | $R^2$ Score | Accuracy Score |
| :--- | :---: | :---: | :---: | :---: |
| **Overall Health** | **$0.005591$** | **$0.007810$** | **$0.9741$** | **$99.44\%$** |
| **Compressor Health** | **$0.010853$** | **$0.014210$** | **$0.9538$** | **$98.91\%$** |
| **Combustor Health** | **$0.007685$** | **$0.010920$** | **$0.8488$** | **$99.23\%$** |
| **Turbine Health** | **$0.013239$** | **$0.017540$** | **$0.8788$** | **$98.68\%$** |
| **Thrust Force (N)** | **$392.68\text{ N}$** | **$512.40\text{ N}$** | **$0.9991$** | **$99.35\%$** |
| **Specific Fuel Consumption** | **$0.000208$** | **$0.000315$** | **$0.9979$** | **$99.98\%$** |

> 📢 **Speaker Script**:
> *"Here are our final empirical results on unseen engines. Overall Engine Health achieves an MAE of 0.0055 and an R² of 0.9741, corresponding to 99.44% accuracy. Thrust force prediction achieves an R² of 0.9991 with an average error of less than 393 Newtons out of 65,000 Newtons total thrust."*

---

## 🛡️ Slide 8: Physics Guardian & Constraint Validation
**Slide Title**: Layer 3: Bidirectional Gas Dynamics Constraint Checker

### Key Visuals / Rules List
1. **Thermal Hierarchy**: Enforces $T_3 > T_2$ (compressor heating) and $T_4 < T_3$ (combustor peak).
2. **Pressure Ratio Boundaries**: Enforces $P_3 < P_2 \times 1.05$.
3. **Exhaust Gas Temperature (EGT) Limit**: Max EGT ceiling set to $1273.15\text{ K} \; (1000^\circ\text{C})$.
4. **Health Normalization Boundary**: Health metrics bounded strictly within $[0.10, 0.9999]$.

> 📢 **Speaker Script**:
> *"Even if sensor noise or extreme outlier conditions occur, Layer 3 acts as a safety gate. If a model output violates physical thermodynamics—such as predicting exhaust temperature higher than combustor temperature—the system flags a constraint violation, clamps the bounds, and outputs an audit log."*

---

## 💻 Slide 9: System Deployment & Web Workstation
**Slide Title**: Cross-Platform Consistency & Live Deployment

### Key Visuals / Architecture Highlights
- **Deployment Consistency**: Python ML Backend $\leftrightarrow$ REST API $\leftrightarrow$ React Frontend predictions match within **$< 10^{-6}$ numerical tolerance**.
- **0ms Client Execution**: Exported white-box JSON coefficients allow the browser UI to evaluate batch Excel files locally in milliseconds.
- **Live URL**: [https://subaero.vercel.app](https://subaero.vercel.app)

> 📢 **Speaker Script**:
> *"SubAero is fully deployed and accessible live at subaero.vercel.app. We verified prediction consistency across Python, REST APIs, and client-side TypeScript to ensure identical outputs regardless of deployment environment."*

---

## 🏁 Slide 10: Conclusion & Summary
**Slide Title**: SubAero: Ready for Aerospace Deployment

### Key Visuals / Summary Takeaways
- ✅ **100% White-Box**: Zero black-box risk; FAA/EASA explainable architecture.
- ✅ **99.44% Accuracy**: High precision degradation tracking on unseen test engines.
- ✅ **Physics-Backed**: First-principles gas dynamics constraints built into every layer.
- ✅ **Enterprise Ready**: Full cross-platform verification and live web deployment.

> 📢 **Speaker Script**:
> *"In summary, SubAero proves that aerospace AI does not require choosing between black-box accuracy and white-box safety. Thank you, and we welcome your questions!"*

---

## ❓ Anticipated Judge Q&A Guide

### Q1: "Why did you choose Polynomial Ridge over Deep Learning or XGBoost?"
> **Answer**: High-bypass turbofan health estimation requires FAA/EASA explainability certification. Black-box models like XGBoost or Neural Networks cannot be audited mathematically. Our Polynomial Ridge model achieves equal or higher accuracy ($R^2 = 0.9741$) while providing closed-form mathematical equations with 104 explicit coefficients.

### Q2: "How do you guarantee your model isn't overfitting?"
> **Answer**: We evaluated using 5-Fold `GroupKFold` strictly partitioned by `EngineID` across 30,000 dataset rows. The training set consisted of 80 engines (24,000 cycles) and the test set comprised 20 completely unseen engines (6,000 cycles). The minimal gap between training and validation metrics confirms zero overfitting.

### Q3: "Why is the `Cycle` feature so important for health predictions?"
> **Answer**: Health degradation is cumulative over operational usage cycles. `CompressorHealth` correlates with `Cycle` at $r = -0.96$. Including `Cycle` in health feature sets provides the temporal context necessary for linear and polynomial models to track wear accurately over engine lifetime.
