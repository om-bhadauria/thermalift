"""
THERMALIFT FastAPI Application.

Main API entry point that exposes:
- Health check
- Physics simulation
- ML predictions
- Constrained optimization

All data and results are synthetic/demo - NOT validated against real Baghewala/OIL field operations.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import health, simulation, prediction, optimization
from app.ml.model_registry import initialize_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - initialize models on startup."""
    # Startup: initialize ML models
    initialize_models()
    yield
    # Shutdown: cleanup if needed


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="THERMALIFT API - Thermal Lift Optimization for CSS/SRP Operations. All data is synthetic/demo.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers with API prefix
    api_prefix = settings.API_V1_PREFIX
    
    app.include_router(
        health.router,
        prefix=api_prefix,
        tags=["health"]
    )
    
    app.include_router(
        simulation.router,
        prefix=api_prefix,
        tags=["simulation"]
    )
    
    app.include_router(
        prediction.router,
        prefix=api_prefix,
        tags=["prediction"]
    )
    
    app.include_router(
        optimization.router,
        prefix=api_prefix,
        tags=["optimization"]
    )
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "service": settings.APP_NAME,
            "version": "1.0.0",
            "data_policy": "SYNTHETIC/DEMO",
            "docs": "/docs",
            "health": f"{api_prefix}/health"
        }
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )