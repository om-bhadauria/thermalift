"""
Production forecasting model using RandomForestRegressor.
Trained on physics-informed synthetic/demo data.
"""
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score
import joblib
import json
from pathlib import Path

from app.ml.features import FeatureBuilder, generate_training_data, split_train_test


class ProductionForecaster:
    """
    RandomForest-based production rate forecaster.
    
    Trained on physics-informed synthetic/demo data.
    Results are prototype/demo outputs - NOT validated against real Baghewala/OIL field data.
    """
    
    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int = 15,
        min_samples_split: int = 5,
        min_samples_leaf: int = 2,
        random_state: int = 42,
        n_jobs: int = -1
    ):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state,
            n_jobs=n_jobs
        )
        self.feature_builder = FeatureBuilder(add_derived=True)
        self.feature_names: Optional[list] = None
        self.is_fitted = False
        self.training_metrics: Dict[str, float] = {}
    
    def train(self, train_df: pd.DataFrame) -> Dict[str, float]:
        """Train the production forecasting model."""
        X, y = self.feature_builder.get_production_features(train_df)
        self.feature_names = list(X.columns)
        
        self.model.fit(X, y)
        self.is_fitted = True
        
        # Training metrics
        y_pred = self.model.predict(X)
        self.training_metrics = {
            "train_mae": mean_absolute_error(y, y_pred),
            "train_rmse": np.sqrt(mean_squared_error(y, y_pred)),
            "train_r2": r2_score(y, y_pred),
            "n_samples": len(X),
            "n_features": len(self.feature_names)
        }
        
        return self.training_metrics
    
    def evaluate(self, test_df: pd.DataFrame) -> Dict[str, float]:
        """Evaluate on test data."""
        if not self.is_fitted:
            raise ValueError("Model must be trained before evaluation")
        
        X_test, y_test = self.feature_builder.get_production_features(test_df)
        
        # Ensure same features
        X_test = X_test[self.feature_names]
        
        y_pred = self.model.predict(X_test)
        
        metrics = {
            "test_mae": mean_absolute_error(y_test, y_pred),
            "test_rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
            "test_r2": r2_score(y_test, y_pred),
            "n_samples": len(X_test)
        }
        
        return metrics
    
    def predict(self, states: pd.DataFrame) -> np.ndarray:
        """Predict production rate for new data."""
        if not self.is_fitted:
            raise ValueError("Model must be trained before prediction")
        
        X = self.feature_builder.get_inference_features(states, model_type="production")
        X = X[self.feature_names]
        
        preds = self.model.predict(X)
        return np.maximum(preds, 0)  # Ensure non-negative
    
    def predict_single(self, state_dict: Dict[str, Any]) -> float:
        """Predict for a single state dict."""
        df = pd.DataFrame([state_dict])
        return float(self.predict(df)[0])
    
    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """Get feature importance rankings."""
        if not self.is_fitted:
            raise ValueError("Model must be trained first")
        
        importance = pd.DataFrame({
            "feature": self.feature_names,
            "importance": self.model.feature_importances_
        }).sort_values("importance", ascending=False).head(top_n)
        
        return importance
    
    def cross_validate(self, df: pd.DataFrame, cv: int = 5) -> Dict[str, float]:
        """Cross-validation on full dataset."""
        X, y = self.feature_builder.get_production_features(df)
        
        scores = cross_val_score(
            self.model, X, y, cv=cv, 
            scoring="neg_mean_absolute_error", n_jobs=-1
        )
        
        return {
            "cv_mae_mean": -scores.mean(),
            "cv_mae_std": scores.std(),
            "cv_folds": cv
        }
    
    def save(self, path: str) -> None:
        """Save model to disk."""
        if not self.is_fitted:
            raise ValueError("Cannot save unfitted model")
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            "model": self.model,
            "feature_names": self.feature_names,
            "training_metrics": self.training_metrics,
            "model_params": self.model.get_params()
        }
        joblib.dump(model_data, path)
    
    @classmethod
    def load(cls, path: str) -> "ProductionForecaster":
        """Load model from disk."""
        model_data = joblib.load(path)
        
        forecaster = cls()
        forecaster.model = model_data["model"]
        forecaster.feature_names = model_data["feature_names"]
        forecaster.training_metrics = model_data["training_metrics"]
        forecaster.is_fitted = True
        forecaster.feature_builder = FeatureBuilder(add_derived=True)
        
        return forecaster


def train_production_model(
    n_days: int = 180,
    freq_hours: int = 6,
    test_size: float = 0.2,
    random_state: int = 42,
    save_path: Optional[str] = None
) -> Tuple[ProductionForecaster, Dict[str, float], Dict[str, float]]:
    """
    Complete training pipeline for production forecaster.
    
    Returns:
        (trained_model, train_metrics, test_metrics)
    """
    # Generate data
    print("Generating synthetic training data...")
    df = generate_training_data(n_days=n_days, freq_hours=freq_hours, seed=random_state)
    print(f"Generated {len(df)} records from {df['well_id'].nunique()} wells")
    
    # Split
    print("Splitting train/test (grouped by well)...")
    train_df, test_df = split_train_test(df, test_size=test_size, random_state=random_state)
    print(f"Train: {len(train_df)}, Test: {len(test_df)}")
    print(f"Train wells: {train_df['well_id'].unique()}")
    print(f"Test wells: {test_df['well_id'].unique()}")
    
    # Train
    print("Training RandomForestRegressor...")
    forecaster = ProductionForecaster(random_state=random_state)
    train_metrics = forecaster.train(train_df)
    
    # Evaluate
    print("Evaluating on test set...")
    test_metrics = forecaster.evaluate(test_df)
    
    # Cross-validation
    print("Running cross-validation...")
    cv_metrics = forecaster.cross_validate(df)
    
    # Feature importance
    importance = forecaster.get_feature_importance(15)
    print("\nTop 15 Feature Importances:")
    print(importance.to_string(index=False))
    
    # Combine metrics
    all_metrics = {**train_metrics, **test_metrics, **cv_metrics}
    
    # Save if requested
    if save_path:
        print(f"Saving model to {save_path}...")
        forecaster.save(save_path)
    
    return forecaster, train_metrics, test_metrics