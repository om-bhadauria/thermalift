"""
Optimization endpoint for THERMALIFT API.
Calls the existing constrained optimization engine.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.models.synthetic import WellConfig
from app.services.physics_models import PipelineEngine
from app.ml.production_forecaster import ProductionForecaster
from app.ml.risk_predictor import RiskPredictor
from app.ml.features import generate_training_data, split_train_test
from app.optimization import run_optimization, OptimizationConfig, OptimizationConstraints, ObjectiveWeights
from app.core.config import settings
from app.data.synthetic_data import DEFAULT_WELL_CONFIGS
from app.ml.model_registry import get_models


router = APIRouter()


# Request/Response Models
class OptimizationRequest(BaseModel):
    """Request model for optimization."""
    well_id: str = Field(..., description="Well identifier (e.g., BW-001)")
    grid_resolution: int = Field(default=2, ge=1, le=5, description="Grid resolution for search")
    day_in_cycle: float = Field(default=5.0, description="Day within CSS cycle for evaluation")
    cycle_num: int = Field(default=1, description="CSS cycle number")
    wellhead_pressure_kpa: float = Field(default=500.0, description="Wellhead pressure in kPa")
    constraints: Optional[Dict[str, Any]] = Field(default=None, description="Custom constraint bounds")
    weights: Optional[Dict[str, float]] = Field(default=None, description="Custom objective weights")
    random_seed: int = Field(default=42, description="Random seed for reproducibility")


class OptimizationResponse(BaseModel):
    """Response model for optimization."""
    well_id: str
    best_candidate: Dict[str, Any]
    baseline_comparison: Dict[str, Any]
    recommendation: Dict[str, Any]
    total_evaluated: int
    feasible_count: int
    execution_time_seconds: float
    data_source: str = "SYNTHETIC_DEMO"
    disclaimer: str = "Optimization results are prototype recommendations generated from synthetic/demo data and are not validated against real Baghewala/OIL field operations."


def get_well_config(well_id: str) -> WellConfig:
    """Get well configuration by ID."""
    for config in DEFAULT_WELL_CONFIGS:
        if config.well_id == well_id:
            return config
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Well configuration not found for well_id: {well_id}"
    )


def build_optimization_config(request: OptimizationRequest) -> OptimizationConfig:
    """Build optimization config from request."""
    constraints = OptimizationConstraints()
    if request.constraints:
        for key, value in request.constraints.items():
            if hasattr(constraints, key):
                setattr(constraints, key, value)
    
    weights = ObjectiveWeights()
    if request.weights:
        for key, value in request.weights.items():
            if hasattr(weights, key):
                setattr(weights, key, value)
    
    return OptimizationConfig(
        well_id=request.well_id,
        grid_resolution=request.grid_resolution,
        day_in_cycle=request.day_in_cycle,
        cycle_num=request.cycle_num,
        wellhead_pressure_kpa=request.wellhead_pressure_kpa,
        constraints=constraints,
        weights=weights,
        random_seed=request.random_seed
    )


@router.post("/optimization", response_model=OptimizationResponse)
async def optimize(request: OptimizationRequest):
    """
    Run constrained optimization for CSS and SRP parameters.
    
    Uses the existing GridSearchOptimizer which evaluates candidates through:
    - Physics simulation (PipelineEngine)
    - ML forecasting (ProductionForecaster)
    - ML risk prediction (RiskPredictor)
    - Constraint validation
    - Multi-objective scoring
    
    Returns the best feasible candidate with baseline comparison.
    All results based on synthetic/demo data.
    """
    try:
        # Get well config (validates well_id)
        well_config = get_well_config(request.well_id)
        
        # Get optimization models
        models = get_models()
        
        # Build optimization config
        config = build_optimization_config(request)
        
        # Run optimization
        result = run_optimization(
            well_config=well_config,
            physics_engine=PipelineEngine(well_config),
            production_forecaster=models["production_forecaster"],
            rod_float_predictor=models["rod_float_predictor"],
            impact_loading_predictor=models["impact_loading_predictor"],
            config=config
        )
        
        # Build response
        return OptimizationResponse(
            well_id=result.config.well_id,
            best_candidate=result.best_candidate.model_dump(),
            baseline_comparison=result.recommendation.baseline_comparison.model_dump(),
            recommendation={
                "recommended_css": result.recommendation.recommended_css.model_dump(),
                "recommended_srp": result.recommendation.recommended_srp.model_dump(),
                "predicted_production_stb_d": result.recommendation.predicted_production_stb_d,
                "predicted_rod_float_risk": result.recommendation.predicted_rod_float_risk,
                "predicted_impact_loading_risk": result.recommendation.predicted_impact_loading_risk,
                "objective_score": result.recommendation.objective_score,
                "constraints_satisfied": result.recommendation.constraints_satisfied,
                "explanation": result.recommendation.explanation
            },
            total_evaluated=result.total_evaluated,
            feasible_count=result.feasible_count,
            execution_time_seconds=result.execution_time_seconds
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(e)}"
        )


@router.get("/optimization/constraints/default")
async def get_default_constraints():
    """Get default optimization constraints."""
    constraints = OptimizationConstraints()
    return {
        "constraints": constraints.model_dump(),
        "description": "Default DEMO/SYNTHETIC constraint bounds - NOT actual field limits"
    }


@router.get("/optimization/weights/default")
async def get_default_weights():
    """Get default objective function weights."""
    weights = ObjectiveWeights()
    return {
        "weights": weights.model_dump(),
        "description": "Default DEMO/PROTOTYPE objective weights - NOT optimized from real economics"
    }