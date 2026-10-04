# THERMALIFT Backend

Backend API for THERMALIFT - Digital Twin for Well-to-Surface Optimization of Cycle Steam Stimulation (CSS) and Sucker Rod Pump (SRP) Operations.

## Installation

```bash
pip install -e .
```

## Development

```bash
pip install -e ".[dev]"
uvicorn app.api.main:app --reload
```

## API Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/simulation/wells` - List wells
- `GET /docs` - API documentation (Swagger UI)

## Data Policy

**SYNTHETIC/DEMO DATA ONLY** - All data is physics-informed synthetic/demo data, explicitly labelled as such. Never present synthetic results as real field results.