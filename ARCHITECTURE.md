# THERMALIFT Architecture

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        THERMALIFT SYSTEM                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐         │
│  │   FRONTEND   │◄────►│   BACKEND    │◄────►│  DATABASE    │         │
│  │  (React/TS)  │ REST │  (FastAPI)   │ SQL  │  (PostgreSQL)│         │
│  └──────────────┘      └──────┬───────┘      └──────────────┘         │
│                               │                                        │
│                    ┌──────────┼──────────┐                             │
│                    ▼          ▼          ▼                             │
│            ┌─────────────┐ ┌─────────┐ ┌─────────┐                    │
│            │  MODEL      │ │ DATA    │ │ OPTIMIZER│                    │
│            │  PIPELINE   │ │ GEN     │ │ (SciPy) │                    │
│            └─────────────┘ └─────────┘ └─────────┘                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Separation of Concerns:**
- **Frontend**: Pure UI/UX, state management, visualization
- **Backend**: Business logic, model pipeline, optimization, API
- **Database**: Persistence for wells, scenarios, optimization runs, recommendations
- **Model Pipeline**: Pure Python scientific computing (testable independently)

---

## 2. Frontend / Backend Separation

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   ├── pages/            # Page-level components
│   ├── hooks/            # Custom React hooks
│   ├── services/         # API client (Axios/Fetch)
│   ├── store/            # State management (Zustand/Redux)
│   ├── types/            # TypeScript interfaces
│   └── utils/            # Helpers, formatters
├── package.json
└── vite.config.ts
```

### Backend (FastAPI)
```
backend/
├── app/
│   ├── api/              # API routes (v1/)
│   │   ├── wells.py
│   │   ├── scenarios.py
│   │   ├── optimization.py
│   │   └── recommendations.py
│   ├── core/             # Config, security, database
│   ├── models/           # Pydantic schemas
│   ├── services/         # Business logic
│   │   ├── thermal_model.py
│   │   ├── viscosity_model.py
│   │   ├── wellbore_model.py
│   │   ├── srp_model.py
│   │   ├── forecast_model.py
│   │   ├── risk_model.py
│   │   └── optimizer.py
│   ├── data/             # Synthetic data generators
│   │   └── synthetic_data.py
│   └── main.py           # FastAPI app entry
├── requirements.txt
└── pyproject.toml
```

---

## 3. Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  Synthetic  │────►│ Data Prep &  │────►│ Thermal Model  │
│  Well Data  │     │ Validation   │     │ (T(z,t) field) │
└─────────────┘     └──────────────┘     └───────┬────────┘
                                                  │
                                                  ▼
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  Optimizer  │◄────│ Forecast &   │◄────│ Viscosity Model│
│  (SciPy)    │     │ Risk Models  │     │ (μ(T))         │
└─────────────┘     └──────┬───────┘     └────────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
            ┌───────────┐ ┌─────────────┐
            │ Wellbore  │ │ SRP Model   │
            │ Model     │ │ (Dynamometer│
            │ (p, v, ρ) │ │  Card)      │
            └───────────┘ └─────────────┘
```

**Causal Chain (MUST be preserved):**
```
CSS Parameters → Thermal Response → Temperature Field
                                    → Viscosity (μ = μ₀ × exp(Ea/RT))
                                    → Wellbore Fluid State (ρ, p, flow regime)
                                    → SRP Load (Polished Rod Load, Fillage)
                                    → Production Rate + Risk (Rod Float, Impact)
                                    → Optimization Objective
                                    → Recommended Settings + Explanation
```

---

## 4. Core Modules

### 4.1 Thermal Model (`thermal_model.py`)
- **Input**: CSS schedule (steam rate, quality, duration, soak, cycles), reservoir properties
- **Physics**: 1D radial heat conduction + convection, analytical/semi-analytical solution
- **Output**: Temperature field `T(r, z, t)` at wellbore and near-wellbore
- **Key Equation**: `∂T/∂t = α∇²T - v·∇T + Q/(ρcₚ)`

### 4.2 Viscosity Model (`viscosity_model.py`)
- **Input**: Temperature, oil composition (API gravity, SARA)
- **Physics**: Modified Andrade / WLF / Arrhenius correlation
- **Output**: Dynamic viscosity `μ(T)` [cP]
- **Key Equation**: `μ = A × exp(B / (T - C))` or `log μ = a + b/(T - c)`

### 4.3 Wellbore Model (`wellbore_model.py`)
- **Input**: Viscosity, well geometry, completion, fluid properties
- **Physics**: Multiphase flow (HEM/ drift-flux), pressure drop, holdup
- **Output**: Bottomhole pressure, wellhead pressure, flow regime, liquid holdup

### 4.4 SRP Model (`srp_model.py`)
- **Input**: Wellbore pressure, pump geometry, rod string, SPM
- **Physics**: Wave equation for rod dynamics, polished rod load, dynamometer card
- **Output**: Polished rod load (min/max), fillage, pump efficiency, rod stress

### 4.5 Forecast Model (`forecast_model.py`)
- **Input**: Current state, CSS/SRP schedule, decline parameters
- **Physics**: Arps decline + thermal recovery factor, SRP efficiency decay
- **Output**: Production forecast (Qo, Qw, Qg) for N days

### 4.6 Risk Model (`risk_model.py`)
- **Input**: SRP dynamometer card, rod string properties, fluid properties
- **Output**: Rod float probability, impact loading risk score, gas lock risk

### 4.7 Optimizer (`optimizer.py`)
- **Method**: SciPy `minimize` (SLSQP / COBYLA / differential_evolution)
- **Variables**: CSS (steam rate, cycle duration, soak time), SRP (SPM, stroke length)
- **Objective**: Maximize NPV / oil recovery / minimize steam-oil ratio
- **Constraints**: Max BHP, max rod stress, max surface temperature, equipment limits

### 4.8 Recommendation Engine (`recommendation.py`)
- **Input**: Optimization result, sensitivity analysis, model traces
- **Output**: Recommended settings + natural language explanation + confidence

---

## 5. API Boundaries

### REST API (v1)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/wells` | GET | List all wells |
| `/api/v1/wells/{well_id}` | GET | Get well details + current state |
| `/api/v1/wells/{well_id}/state` | GET | Current thermal/wellbore/SRP state |
| `/api/v1/wells/{well_id}/forecast` | GET | Production forecast |
| `/api/v1/wells/{well_id}/scenarios` | POST | Create scenario |
| `/api/v1/wells/{well_id}/scenarios/{scenario_id}` | GET | Get scenario results |
| `/api/v1/wells/{well_id}/optimize` | POST | Run constrained optimization |
| `/api/v1/wells/{well_id}/recommendations` | GET | Get explainable recommendations |
| `/api/v1/wells/{well_id}/compare` | POST | Compare scenarios |

### Request/Response Schemas (Pydantic)

```python
# Well State
class WellState(BaseModel):
    well_id: str
    timestamp: datetime
    temperature_profile: List[float]      # T(z) at discrete depths
    viscosity_profile: List[float]        # μ(z)
    wellhead_pressure: float
    bottomhole_pressure: float
    production_rate: float                # STB/day
    spm: float
    polished_rod_load_min: float
    polished_rod_load_max: float
    fillage: float
    pump_efficiency: float
    rod_float_risk: float                 # 0-1
    impact_risk: float                    # 0-1
    data_source: Literal["SYNTHETIC", "REAL"] = "SYNTHETIC"

# Scenario
class CSSScenario(BaseModel):
    steam_rate: float          # m³/day
    steam_quality: float       # 0-1
    injection_duration: float  # days
    soak_duration: float       # days
    cycles: int

class SRPScenario(BaseModel):
    spm: float                 # strokes/min
    stroke_length: float       # m
    pump_diameter: float       # mm

class ScenarioRequest(BaseModel):
    css: CSSScenario
    srp: SRPScenario
    forecast_days: int = 90

# Optimization
class OptimizationRequest(BaseModel):
    objective: Literal["max_oil", "min_sor", "max_npv"]
    css_bounds: Dict[str, Tuple[float, float]]
    srp_bounds: Dict[str, Tuple[float, float]]
    constraints: List[Constraint]

class OptimizationResult(BaseModel):
    optimal_css: CSSScenario
    optimal_srp: SRPScenario
    predicted_state: WellState
    objective_value: float
    sensitivity: Dict[str, float]
    explanation: str
```

---

## 6. Synthetic Data Strategy

### 6.1 Well Configuration (Baghewala Field Typical)
| Parameter | Value | Source |
|-----------|-------|--------|
| Depth | 800-1200 m | Typical heavy oil |
| Reservoir Temp (initial) | 80-110 °C | Baghewala |
| Oil API | 10-15 °API | Heavy oil |
| Viscosity @ reservoir | 5,000-50,000 cP | Heavy oil |
| Pay thickness | 10-30 m | Typical |
| Permeability | 500-2000 mD | Heavy oil sand |

### 6.2 Synthetic Generator (`data/synthetic_data.py`)
```python
class SyntheticWellGenerator:
    def generate_well(well_id: str, seed: int = 42) -> WellConfig:
        # Physics-informed ranges, not random
        # All outputs must be reproducible with same seed
        
    def generate_css_history(well_id: str, n_cycles: int) -> List[CSSCycle]:
        # Realistic steam injection patterns
        
    def generate_srp_history(well_id: str, n_days: int) -> List[SRPReading]:
        # SPM, load, fillage with diurnal/seasonal variation
```

### 6.3 Labelling Requirements
- **Every API response** must include `data_source: "SYNTHETIC"`
- **Frontend** must display "DEMO MODE - SYNTHETIC DATA" banner
- **Database** stores `source = 'synthetic'` on all generated records

---

## 7. Model Pipeline

### 7.1 Execution Order (Single Forward Pass)
```python
def run_pipeline(well: WellConfig, css: CSSScenario, srp: SRPScenario) -> WellState:
    # 1. Thermal
    T_field = thermal_model.solve(well, css)
    
    # 2. Viscosity (at pump intake depth)
    mu = viscosity_model.compute(T_field[well.pump_depth])
    
    # 3. Wellbore
    wb_state = wellbore_model.solve(well, mu, srp)
    
    # 4. SRP
    srp_state = srp_model.solve(well, wb_state, srp)
    
    # 5. Production
    q_forecast = forecast_model.predict(well, T_field, wb_state, srp_state)
    
    # 6. Risk
    risks = risk_model.assess(srp_state, wb_state)
    
    # 7. Aggregate
    return WellState(
        temperature_profile=T_field,
        viscosity_profile=[viscosity_model.compute(t) for t in T_field],
        wellhead_pressure=wb_state.p_wh,
        bottomhole_pressure=wb_state.p_bh,
        production_rate=q_forecast.current,
        spm=srp.spm,
        polished_rod_load_min=srp_state.load_min,
        polished_rod_load_max=srp_state.load_max,
        fillage=srp_state.fillage,
        pump_efficiency=srp_state.efficiency,
        rod_float_risk=risks.rod_float,
        impact_risk=risks.impact,
        data_source="SYNTHETIC"
    )
```

### 7.2 Testing Strategy for Pipeline
- **Unit tests**: Each model with known analytical solutions
- **Integration tests**: Full pipeline with synthetic well
- **Regression tests**: Golden master outputs for fixed seeds
- **Sensitivity tests**: Verify causal chain (change CSS → T → μ → load → prod)

---

## 8. Optimization Approach

### 8.1 Problem Formulation
```
maximize:  NPV = Σ [Qo(t) × OilPrice - Qsteam(t) × SteamCost - OpEx(t)] / (1+r)^t
subject to:
    T_surface ≤ T_max                    (equipment limit)
    σ_rod ≤ σ_yield / SF                 (rod stress)
    P_bh ≥ P_bubble                     (avoid gas breakout)
    Fillage ∈ [0.7, 1.0]                (pump efficiency)
    RodFloatRisk ≤ 0.3                  (operational limit)
    SPM_min ≤ SPM ≤ SPM_max             (equipment range)
    SteamRate_min ≤ q_steam ≤ SteamRate_max
```

### 8.2 Algorithm Selection
| Problem Type | Algorithm | Why |
|--------------|-----------|-----|
| Smooth, gradient-available | SLSQP | Fast, handles bounds/constraints |
| Non-smooth, noisy | COBYLA | Derivative-free |
| Global search needed | Differential Evolution | Avoids local optima |
| Multi-objective | NSGA-II (future) | Pareto front |

### 8.3 Implementation
```python
def optimize(well: WellConfig, request: OptimizationRequest) -> OptimizationResult:
    def objective(x):
        css, srp = decode(x)
        state = run_pipeline(well, css, srp)
        return -compute_npv(state, css, srp)  # minimize negative NPV
    
    constraints = build_constraints(request.constraints)
    bounds = build_bounds(request.css_bounds, request.srp_bounds)
    
    result = minimize(objective, x0, method='SLSQP', 
                      bounds=bounds, constraints=constraints)
    
    return build_result(result, well)
```

---

## 9. Testing Strategy

### 9.1 Backend Tests
```
backend/tests/
├── unit/
│   ├── test_thermal_model.py
│   ├── test_viscosity_model.py
│   ├── test_wellbore_model.py
│   ├── test_srp_model.py
│   ├── test_forecast_model.py
│   ├── test_risk_model.py
│   └── test_optimizer.py
├── integration/
│   ├── test_pipeline.py
│   └── test_api.py
└── fixtures/
    └── synthetic_wells.json
```

### 9.2 Test Requirements
- **Thermal**: Compare analytical vs numerical for simple cases
- **Viscosity**: Match published correlations (e.g., Beggs-Robinson)
- **SRP**: Verify dynamometer card shape for known inputs
- **Pipeline**: End-to-end with fixed seed → deterministic output
- **API**: Contract tests for all endpoints

### 9.3 Frontend Tests
- Component tests (React Testing Library)
- E2E tests (Playwright) for critical user flows
- Visual regression for dashboard charts

---

## 10. Future Extension Points

| Extension | Location | Interface |
|-----------|----------|-----------|
| Real SCADA ingestion | `data/ingestion/` | `DataIngestionAdapter` |
| ML surrogate models | `services/surrogate/` | `SurrogateModel` protocol |
| Multi-well optimization | `services/optimizer.py` | `MultiWellOptimizer` |
| Uncertainty quantification | `services/uq/` | `UQEngine` |
| Digital twin sync (real-time) | `services/realtime/` | `TwinSyncService` |
| Advanced economics | `services/economics/` | `EconomicModel` |
| 3D reservoir coupling | `services/reservoir/` | `ReservoirCoupler` |

---

## 11. Development Workflow

### Loop 1: Backend Foundation
- FastAPI app skeleton
- Pydantic models for all API schemas
- Synthetic data generator
- Basic thermal + viscosity model (analytical)
- Unit tests for models

### Loop 2: Wellbore + SRP Models
- Wellbore pressure drop model
- SRP wave equation solver
- Dynamometer card generation
- Pipeline integration test

### Loop 3: Forecast + Risk + Optimization
- Production forecast (Arps + thermal)
- Risk models (rod float, impact)
- SciPy optimizer integration
- Sensitivity analysis

### Loop 4: API + Explainability
- All REST endpoints
- Recommendation engine with natural language
- Scenario comparison endpoint

### Loop 5: Frontend Dashboard
- React + TypeScript + Vite setup
- Well selection page
- Real-time state dashboard
- Scenario builder
- Optimization results view
- Comparison view

### Loop 6: Polish & Demo
- Synthetic data banner everywhere
- Loading states, error handling
- Documentation screenshots
- Demo script for presentation

---

## 12. Configuration

### Environment Variables (`.env`)
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/thermalift

# Backend
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Frontend
VITE_API_URL=http://localhost:8000

# Synthetic Data
SYNTHETIC_SEED=42
DEMO_MODE=true
```

---

## 13. Repository Structure (Final)

```
THERMALIFT/
├── README.md
├── ARCHITECTURE.md
├── docker-compose.yml          # postgres + backend + frontend
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   ├── data/
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
└── docs/                       # Generated API docs, architecture diagrams
```

---

## 14. Commands Reference

```bash
# Start all services
docker-compose up -d

# Backend only
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend only
cd frontend && npm run dev

# Run backend tests
cd backend && pytest -v

# Run frontend tests
cd frontend && npm test

# Lint
cd backend && ruff check .
cd frontend && npm run lint

# Type check
cd backend && mypy app/
cd frontend && npx tsc --noEmit
```

---

**End of Architecture Document** - Ready for Loop 1 Implementation