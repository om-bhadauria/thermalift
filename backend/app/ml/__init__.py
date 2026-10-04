"""
THERMALIFT ML Module

ML models for production forecasting and risk prediction.
All models trained on physics-informed synthetic/demo data.

Results are prototype/demo outputs - NOT validated against real Baghewala/OIL field data.
"""

from app.ml.features import (
    FeatureBuilder,
    generate_training_data,
    split_train_test,
)

from app.ml.production_forecaster import (
    ProductionForecaster,
    train_production_model,
)

from app.ml.risk_predictor import (
    RiskPredictor,
    train_risk_model,
)

__all__ = [
    "FeatureBuilder",
    "generate_training_data",
    "split_train_test",
    "ProductionForecaster",
    "train_production_model",
    "RiskPredictor",
    "train_risk_model",
]

# Version
__version__ = "0.1.0"