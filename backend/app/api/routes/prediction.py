"""
ML Prediction endpoint for THERMALIFT API.
Uses the existing ML models for production forecasting and risk prediction.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import pandas as pd

from app.models.synthetic import WellConfig, WellState
from app.services.physics_models import PipelineEngine
from app.ml.production_forecaster import ProductionForecaster
from app.ml.risk_predictor import RiskPredictor
from app.ml.features import generate_training_data, split_train_test, FeatureBuilder
from app.core.config import settings
from app.data.synthetic_data import DEFAULT_WELL_CONFIGS
from app.ml.model_registry import get_models


router = APIRouter()


# Request/Response Models
class PredictionRequest(BaseModel):
    """Request model for ML prediction."""
    well_id: str = Field(..., description="Well identifier (e.g., BW-001)")
    state: dict = Field(..., description="Well state data for prediction")


class PredictionResponse(BaseModel):
    """Response model for ML prediction."""
    well_id: str
    predicted_production_stb_d: float
    predicted_rod_float_risk: float
    predicted_impact_loading_risk: float
    model_info: Dict[str, Any]
    data_source: str = "SYNTHETIC_DEMO"
    disclaimer: str = "Predictions are based on models trained on synthetic/demo data and are not validated against real Baghewala/OIL field operations."


def get_well_config(well_id: str) -> WellConfig:
    """Get well configuration by ID."""
    for config in DEFAULT_WELL_CONFIGS:
        if config.well_id == well_id:
            return config
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Well configuration not found for well_id: {well_id}"
    )


@router.post("/prediction", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Get ML predictions for production and risk.
    
    Uses pre-trained RandomForest models:
    - ProductionForecaster for production rate
    - RiskPredictor for rod float risk
    - RiskPredictor for impact loading risk
    
    All models trained on synthetic/demo data.
    """
    try:
        # Get well config (validates well_id)
        get_well_config(request.well_id)
        
        # Get models
        models = get_models()
        prod_forecaster = models["production_forecaster"]
        rod_float_predictor = models["rod_float_predictor"]
        impact_loading_predictor = models["impact_loading_predictor"]
        
        # Prepare state data
        state_dict = request.state.copy()
        state_dict["well_id"] = request.well_id
        
        # Make predictions
        predicted_production = prod_forecaster.predict_single(state_dict)
        predicted_rod_float = rod_float_predictor.predict_single(state_dict)
        predicted_impact_loading = impact_loading_predictor.predict_single(state_dict)
        
        # Model info
        model_info = {
            "production_model": {
                "type": "RandomForestRegressor",
                "n_estimators": prod_forecaster.model.n_estimators,
                "features": len(prod_forecaster.feature_names) if prod_forecaster.feature_names else 0,
                "training_metrics": prod_forecaster.training_metrics
            },
            "rod_float_risk_model": {
                "type": "RandomForestRegressor",
                "n_estimators": rod_float_predictor.model.n_estimators,
                "features": len(rod_float_predictor.feature_names) if rod_float_predictor.feature_names else 0,
                "training_metrics": rod_float_predictor.training_metrics
            },
            "impact_loading_risk_model": {
                "type": "RandomForestRegressor",
                "n_estimators": impact_loading_predictor.model.n_estimators,
                "features": len(impact_loading_predictor.feature_names) if impact_loading_predictor.feature_names else 0,
                "training_metrics": impact_loading_predictor.training_metrics
            }
        }
        
        return PredictionResponse(
            well_id=request.well_id,
            predicted_production_stb_d=round(float(predicted_production), 1),
            predicted_rod_float_risk=round(float(predicted_rod_float), 3),
            predicted_impact_loading_risk=round(float(predicted_impact_loading), 3),
            model_info=model_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get("/prediction/models/status")
async def model_status():
    """Get status of ML models."""
    models = get_models()
    return {
        "initialized": models["initialized"],
        "production_forecaster": models["production_forecaster"] is not None,
        "rod_float_predictor": models["rod_float_predictor"] is not None,
        "impact_loading_predictor": models["impact_loading_predictor"] is not None,
        "data_source": "SYNTHETIC_DEMO"
    }