# THERMALIFT

Digital Twin for Well-to-Surface Optimization of Cycle Steam Stimulation (CSS) and Sucker Rod Pump (SRP) Operations for Heavy Oil Wells of Baghewala Field.

**Problem Statement ID:** SIH26120

---

## Status
**Loop 0** - Architecture documentation only. No code implemented yet.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React + TypeScript |
| Backend | Python + FastAPI |
| Scientific | NumPy, SciPy, pandas |
| ML | scikit-learn |
| Database | PostgreSQL |

---

## MVP Features (17)

1. Well selection
2. Current thermal state
3. Temperature
4. Estimated viscosity
5. Production rate
6. SRP speed / SPM
7. Pump load
8. Fillage / efficiency
9. Rod-float / impact risk
10. Production forecast
11. CSS scenario parameters
12. SRP scenario parameters
13. Constrained optimization
14. Recommended operating settings
15. Explainable "Why this recommendation?" section
16. Scenario comparison
17. Clear SYNTHETIC DATA / DEMO MODE label

---

## Core Pipeline

```
Operational/Synthetic Data
        ↓
Data Preparation
        ↓
Thermal & Viscosity Model
        ↓
Wellbore & SRP Model
        ↓
Production Forecast + Risk
        ↓
Constrained Optimizer
        ↓
Explainable Recommendation
        ↓
Dashboard / Scenario Simulation
```

---

## Data Policy

**NO REAL FIELD DATA EXISTS.** All data is physics-informed synthetic/demo data, explicitly labelled as such. Never present synthetic results as real field results.

---

## Quick Start (After Implementation)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture, data flow, modules, API boundaries