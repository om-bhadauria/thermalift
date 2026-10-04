"""
Risk prediction model for SRP failure modes.
Uses RandomForestRegressor for continuous risk score prediction [0, 1].

Trained on physics-informed synthetic/demo data.
Results are prototype/demo outputs - NOT validated against real Baghewala/OIL field data.
"""
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score
import joblib
from pathlib import Path

from app.ml.features import FeatureBuilder, generate_training_data, split_train_test


class RiskPredictor:
    """
    RandomForest-based risk score predictor for rod float and impact loading.
    
    Predicts continuous risk scores in [0, 1].
    Trained on physics-informed synthetic/demo data.
    Results are prototype/demo outputs - NOT validated against real Baghewala/OIL field data.
    """
    
    RISK_TARGETS = ["rod_float_risk", "impact_loading_risk"]
    
    def __init__(
        self,
        risk_target: str = "rod_float_risk",
        n_estimators: int = 200,
        max_depth: int = 12,
        min_samples_split: int = 5,
        min_samples_leaf: int = 2,
        random_state: int = 42,
        n_jobs: int = -1
    ):
        if risk_target not in self.RISK_TARGETS:
            raise ValueError(f"risk_target must be one of {self.RISK_TARGETS}")
        
        self.risk_target = risk_target
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
        """Train the risk prediction model."""
        X, y = self.feature_builder.get_risk_features(train_df, self.risk_target)
        self.feature_names = list(X.columns)
        
        self.model.fit(X, y)
        self.is_fitted = True
        
        # Training metrics
        y_pred = self.model.predict(X)
        y_pred_clipped = np.clip(y_pred, 0, 1)
        
        self.training_metrics = {
            "train_mae": mean_absolute_error(y, y_pred_clipped),
            "train_rmse": np.sqrt(mean_squared_error(y, y_pred_clipped)),
            "train_r2": r2_score(y, y_pred_clipped),
            "n_samples": len(X),
            "n_features": len(self.feature_names),
            "risk_target": self.risk_target
        }
        
        return self.training_metrics
    
    def evaluate(self, test_df: pd.DataFrame) -> Dict[str, float]:
        """Evaluate on test data."""
        if not self.is_fitted:
            raise ValueError("Model must be trained before evaluation")
        
        X_test, y_test = self.feature_builder.get_risk_features(test_df, self.risk_target)
        X_test = X_test[self.feature_names]
        
        y_pred = self.model.predict(X_test)
        y_pred_clipped = np.clip(y_pred, 0, 1)
        
        metrics = {
            "test_mae": mean_absolute_error(y_test, y_pred_clipped),
            "test_rmse": np.sqrt(mean_squared_error(y_test, y_pred_clipped)),
            "test_r2": r2_score(y_test, y_pred_clipped),
            "n_samples": len(X_test)
        }
        
        return metrics
    
    def predict(self, states: pd.DataFrame) -> np.ndarray:
        """Predict risk score for new data."""
        if not self.is_fitted:
            raise ValueError("Model must be trained before prediction")
        
        X = self.feature_builder.get_inference_features(states, model_type="risk")
        X = X[self.feature_names]
        
        preds = self.model.predict(X)
        return np.clip(preds, 0, 1)  # Ensure bounded [0, 1]
    
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
        X, y = self.feature_builder.get_risk_features(df, self.risk_target)
        
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
            "model_params": self.model.get_params(),
            "risk_target": self.risk_target
        }
        joblib.dump(model_data, path)
    
    @classmethod
    def load(cls, path: str) -> "RiskPredictor":
        """Load model from disk."""
        model_data = joblib.load(path)
        
        predictor = cls(risk_target=model_data["risk_target"])
        predictor.model = model_data["model"]
        predictor.feature_names = model_data["feature_names"]
        predictor.training_metrics = model_data["training_metrics"]
        predictor.is_fitted = True
        predictor.feature_builder = FeatureBuilder(add_derived=True)
        
        return predictor


def train_risk_model(
    risk_target: str = "rod_float_risk",
    n_days: int = 180,
    freq_hours: int = 6,
    test_size: float = 0.2,
    random_state: int = 42,
    save_path: Optional[str] = None
) -> Tuple[RiskPredictor, Dict[str, float], Dict[str, float]]:
    """
    Complete training pipeline for risk predictor.
    
    Returns:
        (trained_model, train_metrics, test_metrics)
    """
    # Generate data
    print(f"Generating synthetic training data for {risk_target}...")
    df = generate_training_data(n_days=n_days, freq_hours=freq_hours, seed=random_state)
    print(f"Generated {len(df)} records from {df['well_id'].nunique()} wells")
    
    # Split
    print("Splitting train/test (grouped by well)...")
    train_df, test_df = split_train_test(df, test_size=test_size, random_state=random_state)
    print(f"Train: {len(train_df)}, Test: {len(test_df)}")
    print(f"Train wells: {train_df['well_id'].unique()}")
    print(f"Test wells: {test_df['well_id'].unique()}")
    
    # Train
    print(f"Training RandomForestRegressor for {risk_target}...")
    predictor = RiskPredictor(risk_target=risk_target, random_state=random_state)
    train_metrics = predictor.train(train_df)
    
    # Evaluate
    print("Evaluating on test set...")
    test_metrics = predictor.evaluate(test_df)
    
    # Cross-validation
    print("Running cross-validation...")
    cv_metrics = predictor.cross_validate(df)
    
    # Feature importance
    importance = predictor.get_feature_importance(15)
    print(f"\nTop 15 Feature Importances for {risk_target}:")
    print(importance.to_string(index=False))
    
    # Combine metrics
    all_metrics = {**train_metrics, **test_metrics, **cv_metrics}
    
    # Save if requested
    if save_path:
        print(f"Saving model to {save_path}...")
        predictor.save(save_path)
    
    return predictor, train_metrics, test_metrics