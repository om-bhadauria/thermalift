"""
Shared ML model initialization for THERMALIFT API.
Provides centralized model training and caching for prediction and optimization endpoints.
"""
from typing import Dict, Any, Optional
import pandas as pd

from app.ml.production_forecaster import ProductionForecaster
from app.ml.risk_predictor import RiskPredictor
from app.ml.features import generate_training_data, split_train_test, FeatureBuilder


# Global model cache (shared across prediction and optimization)
_model_cache = {
    "production_forecaster": None,
    "rod_float_predictor": None,
    "impact_loading_predictor": None,
    "feature_builder": None,
    "initialized": False
}


def initialize_models() -> Dict[str, Any]:
    """
    Initialize and train ML models (run once at startup).
    Returns the model cache dict.
    Raises RuntimeError if initialization fails.
    """
    global _model_cache
    
    if _model_cache["initialized"]:
        return _model_cache
    
    try:
        # Generate training data
        df = generate_training_data(n_days=60, freq_hours=12, seed=42)
        train_df, _ = split_train_test(df, test_size=0.25, random_state=42)
        
        # Train production forecaster
        prod_forecaster = ProductionForecaster(n_estimators=50, random_state=42)
        prod_forecaster.train(train_df)
        
        # Train risk predictors
        rod_float_predictor = RiskPredictor(risk_target="rod_float_risk", n_estimators=50, random_state=42)
        rod_float_predictor.train(train_df)
        
        impact_loading_predictor = RiskPredictor(risk_target="impact_loading_risk", n_estimators=50, random_state=42)
        impact_loading_predictor.train(train_df)
        
        # Feature builder
        feature_builder = FeatureBuilder(add_derived=True)
        
        # Cache models
        _model_cache["production_forecaster"] = prod_forecaster
        _model_cache["rod_float_predictor"] = rod_float_predictor
        _model_cache["impact_loading_predictor"] = impact_loading_predictor
        _model_cache["feature_builder"] = feature_builder
        _model_cache["initialized"] = True
        
        return _model_cache
        
    except Exception as e:
        # Clear any partial state
        _model_cache["initialized"] = False
        _model_cache["production_forecaster"] = None
        _model_cache["rod_float_predictor"] = None
        _model_cache["impact_loading_predictor"] = None
        _model_cache["feature_builder"] = None
        raise RuntimeError(f"Model initialization failed: {str(e)}") from e


def get_models() -> Dict[str, Any]:
    """Get cached models, initializing if needed."""
    if not _model_cache["initialized"]:
        initialize_models()
    return _model_cache


def get_model_cache() -> Dict[str, Any]:
    """Get the model cache directly (for status checks without initialization)."""
    return _model_cache