"""
Tests for ML models.
Tests feature generation, training, prediction, and explainability.
"""
import pytest
import numpy as np
import pandas as pd
import tempfile
import os

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


class TestFeatureBuilder:
    @pytest.fixture
    def sample_df(self):
        """Generate small synthetic dataset for testing."""
        df = generate_training_data(n_days=30, freq_hours=12, seed=42)
        return df
    
    def test_generate_training_data(self, sample_df):
        """Test data generation produces valid DataFrame."""
        assert isinstance(sample_df, pd.DataFrame)
        assert len(sample_df) > 0
        assert "well_id" in sample_df.columns
        assert "production_rate_stb_d" in sample_df.columns
        assert "rod_float_risk" in sample_df.columns
        assert "impact_loading_risk" in sample_df.columns
    
    def test_split_train_test_no_leakage(self, sample_df):
        """Test train/test split prevents well leakage."""
        train_df, test_df = split_train_test(sample_df, test_size=0.2, random_state=42)
        
        train_wells = set(train_df["well_id"].unique())
        test_wells = set(test_df["well_id"].unique())
        
        # No well should appear in both
        assert len(train_wells & test_wells) == 0
        assert len(train_wells) + len(test_wells) == sample_df["well_id"].nunique()
    
    def test_feature_builder_base_features(self, sample_df):
        """Test base feature extraction."""
        builder = FeatureBuilder(add_derived=False)
        X_prod, y_prod = builder.get_production_features(sample_df)
        X_risk, y_risk = builder.get_risk_features(sample_df, "rod_float_risk")
        
        # Check production features
        assert isinstance(X_prod, pd.DataFrame)
        assert isinstance(y_prod, pd.Series)
        assert len(X_prod) == len(sample_df)
        assert len(y_prod) == len(sample_df)
        
        # Check target not in features
        assert "production_rate_stb_d" not in X_prod.columns
        assert "rod_float_risk" not in X_prod.columns
        assert "impact_loading_risk" not in X_prod.columns
        
        # Check risk features
        assert isinstance(X_risk, pd.DataFrame)
        assert isinstance(y_risk, pd.Series)
        assert len(X_risk) == len(sample_df)
        assert len(y_risk) == len(sample_df)
        
        # Check no risk targets in features
        assert "rod_float_risk" not in X_risk.columns
        assert "impact_loading_risk" not in X_risk.columns
        assert "gas_lock_risk" not in X_risk.columns
        assert "production_rate_stb_d" not in X_risk.columns
    
    def test_feature_builder_derived_features(self, sample_df):
        """Test derived feature generation."""
        builder = FeatureBuilder(add_derived=True)
        X_prod, _ = builder.get_production_features(sample_df)
        
        # Check some derived features exist
        derived_patterns = ["temp_", "steam_", "pump_", "effective_", "load_", "cycle_", "well_"]
        has_derived = any(
            any(p in col for p in derived_patterns)
            for col in X_prod.columns
        )
        assert has_derived, "No derived features found"
    
    def test_no_nan_inf_features(self, sample_df):
        """Test features have no NaN or Inf values."""
        builder = FeatureBuilder(add_derived=True)
        X_prod, y_prod = builder.get_production_features(sample_df)
        X_risk, y_risk = builder.get_risk_features(sample_df, "rod_float_risk")
        
        assert not X_prod.isnull().any().any(), "Production features contain NaN"
        assert not np.isinf(X_prod.values).any(), "Production features contain Inf"
        assert not y_prod.isnull().any(), "Production target contains NaN"
        
        assert not X_risk.isnull().any().any(), "Risk features contain NaN"
        assert not np.isinf(X_risk.values).any(), "Risk features contain Inf"
        assert not y_risk.isnull().any(), "Risk target contains NaN"


class TestProductionForecaster:
    @pytest.fixture
    def train_test_data(self):
        """Generate train/test split for testing."""
        df = generate_training_data(n_days=60, freq_hours=12, seed=42)
        train_df, test_df = split_train_test(df, test_size=0.25, random_state=42)
        return train_df, test_df
    
    def test_training_completes(self, train_test_data):
        """Test model training completes without error."""
        train_df, _ = train_test_data
        forecaster = ProductionForecaster(n_estimators=50, random_state=42)
        metrics = forecaster.train(train_df)
        
        assert forecaster.is_fitted
        assert "train_mae" in metrics
        assert "train_rmse" in metrics
        assert "train_r2" in metrics
        assert metrics["n_samples"] == len(train_df)
        assert metrics["n_features"] > 0
    
    def test_prediction_completes(self, train_test_data):
        """Test prediction works and returns valid values."""
        train_df, test_df = train_test_data
        forecaster = ProductionForecaster(n_estimators=50, random_state=42)
        forecaster.train(train_df)
        
        preds = forecaster.predict(test_df)
        
        assert isinstance(preds, np.ndarray)
        assert len(preds) == len(test_df)
        assert np.all(preds >= 0), "Predictions should be non-negative"
        assert not np.any(np.isnan(preds)), "Predictions should not contain NaN"
        assert not np.any(np.isinf(preds)), "Predictions should not contain Inf"
    
    def test_predict_single(self, train_test_data):
        """Test single prediction."""
        train_df, test_df = train_test_data
        forecaster = ProductionForecaster(n_estimators=50, random_state=42)
        forecaster.train(train_df)
        
        single_state = test_df.iloc[0].to_dict()
        pred = forecaster.predict_single(single_state)
        
        assert isinstance(pred, float)
        assert pred >= 0
    
    def test_evaluation_metrics(self, train_test_data):
        """Test evaluation returns proper metrics."""
        train_df, test_df = train_test_data
        forecaster = ProductionForecaster(n_estimators=50, random_state=42)
        forecaster.train(train_df)
        
        metrics = forecaster.evaluate(test_df)
        
        assert "test_mae" in metrics
        assert "test_rmse" in metrics
        assert "test_r2" in metrics
        assert metrics["n_samples"] == len(test_df)
        assert metrics["test_mae"] >= 0
        assert metrics["test_rmse"] >= 0
    
    def test_feature_importance_available(self, train_test_data):
        """Test feature importance is accessible."""
        train_df, _ = train_test_data
        forecaster = ProductionForecaster(n_estimators=50, random_state=42)
        forecaster.train(train_df)
        
        importance = forecaster.get_feature_importance(10)
        
        assert isinstance(importance, pd.DataFrame)
        assert len(importance) <= 10
        assert "feature" in importance.columns
        assert "importance" in importance.columns
        assert importance["importance"].sum() > 0
    
    def test_deterministic_training(self):
        """Test training is deterministic with same seed."""
        df = generate_training_data(n_days=30, freq_hours=12, seed=42)
        train_df, _ = split_train_test(df, test_size=0.2, random_state=42)
        
        forecaster1 = ProductionForecaster(n_estimators=30, random_state=123)
        forecaster1.train(train_df)
        
        forecaster2 = ProductionForecaster(n_estimators=30, random_state=123)
        forecaster2.train(train_df)
        
        # Predictions should be identical
        test_df, _ = split_train_test(df, test_size=0.2, random_state=42)
        preds1 = forecaster1.predict(test_df)
        preds2 = forecaster2.predict(test_df)
        
        np.testing.assert_array_almost_equal(preds1, preds2)
    
    def test_save_load_model(self, train_test_data):
        """Test model persistence."""
        train_df, test_df = train_test_data
        forecaster = ProductionForecaster(n_estimators=30, random_state=42)
        forecaster.train(train_df)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, "test_model.joblib")
            forecaster.save(model_path)
            
            loaded = ProductionForecaster.load(model_path)
            
            assert loaded.is_fitted
            assert loaded.feature_names == forecaster.feature_names
            
            preds_orig = forecaster.predict(test_df)
            preds_loaded = loaded.predict(test_df)
            np.testing.assert_array_almost_equal(preds_orig, preds_loaded)
    
    def test_cross_validation(self, train_test_data):
        """Test cross-validation runs."""
        train_df, _ = train_test_data
        forecaster = ProductionForecaster(n_estimators=30, random_state=42)
        
        cv_metrics = forecaster.cross_validate(train_df, cv=3)
        
        assert "cv_mae_mean" in cv_metrics
        assert "cv_mae_std" in cv_metrics
        assert cv_metrics["cv_folds"] == 3
        assert cv_metrics["cv_mae_mean"] >= 0


class TestRiskPredictor:
    @pytest.fixture
    def train_test_data(self):
        """Generate train/test split for testing."""
        df = generate_training_data(n_days=60, freq_hours=12, seed=42)
        train_df, test_df = split_train_test(df, test_size=0.25, random_state=42)
        return train_df, test_df
    
    def test_training_rod_float(self, train_test_data):
        """Test rod float risk training."""
        train_df, _ = train_test_data
        predictor = RiskPredictor(risk_target="rod_float_risk", n_estimators=50, random_state=42)
        metrics = predictor.train(train_df)
        
        assert predictor.is_fitted
        assert metrics["risk_target"] == "rod_float_risk"
        assert "train_mae" in metrics
        assert metrics["n_features"] > 0
    
    def test_training_impact_loading(self, train_test_data):
        """Test impact loading risk training."""
        train_df, _ = train_test_data
        predictor = RiskPredictor(risk_target="impact_loading_risk", n_estimators=50, random_state=42)
        metrics = predictor.train(train_df)
        
        assert predictor.is_fitted
        assert metrics["risk_target"] == "impact_loading_risk"
    
    def test_invalid_risk_target(self):
        """Test invalid risk target raises error."""
        with pytest.raises(ValueError):
            RiskPredictor(risk_target="invalid_risk")
    
    def test_prediction_bounded(self, train_test_data):
        """Test risk predictions are bounded [0, 1]."""
        train_df, test_df = train_test_data
        predictor = RiskPredictor(risk_target="rod_float_risk", n_estimators=50, random_state=42)
        predictor.train(train_df)
        
        preds = predictor.predict(test_df)
        
        assert isinstance(preds, np.ndarray)
        assert len(preds) == len(test_df)
        assert np.all(preds >= 0), "Predictions should be >= 0"
        assert np.all(preds <= 1), "Predictions should be <= 1"
        assert not np.any(np.isnan(preds)), "Predictions should not contain NaN"
    
    def test_prediction_single(self, train_test_data):
        """Test single risk prediction."""
        train_df, test_df = train_test_data
        predictor = RiskPredictor(risk_target="rod_float_risk", n_estimators=50, random_state=42)
        predictor.train(train_df)
        
        single_state = test_df.iloc[0].to_dict()
        pred = predictor.predict_single(single_state)
        
        assert isinstance(pred, float)
        assert 0 <= pred <= 1
    
    def test_evaluation_metrics(self, train_test_data):
        """Test risk evaluation metrics."""
        train_df, test_df = train_test_data
        predictor = RiskPredictor(risk_target="rod_float_risk", n_estimators=50, random_state=42)
        predictor.train(train_df)
        
        metrics = predictor.evaluate(test_df)
        
        assert "test_mae" in metrics
        assert "test_rmse" in metrics
        assert "test_r2" in metrics
        assert metrics["test_mae"] >= 0
    
    def test_feature_importance(self, train_test_data):
        """Test risk feature importance."""
        train_df, _ = train_test_data
        predictor = RiskPredictor(risk_target="rod_float_risk", n_estimators=50, random_state=42)
        predictor.train(train_df)
        
        importance = predictor.get_feature_importance(10)
        
        assert isinstance(importance, pd.DataFrame)
        assert "feature" in importance.columns
        assert "importance" in importance.columns
    
    def test_no_target_leakage(self, train_test_data):
        """Test risk target not in features."""
        train_df, _ = train_test_data
        predictor = RiskPredictor(risk_target="rod_float_risk", n_estimators=10, random_state=42)
        predictor.train(train_df)
        
        # Check that no risk target appears in feature names
        for feat in predictor.feature_names:
            assert feat not in ["rod_float_risk", "impact_loading_risk", "gas_lock_risk", "production_rate_stb_d"]
    
    def test_save_load(self, train_test_data):
        """Test risk model persistence."""
        train_df, test_df = train_test_data
        predictor = RiskPredictor(risk_target="rod_float_risk", n_estimators=30, random_state=42)
        predictor.train(train_df)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, "test_risk.joblib")
            predictor.save(model_path)
            
            loaded = RiskPredictor.load(model_path)
            
            assert loaded.is_fitted
            assert loaded.risk_target == "rod_float_risk"
            assert loaded.feature_names == predictor.feature_names
            
            preds_orig = predictor.predict(test_df)
            preds_loaded = loaded.predict(test_df)
            np.testing.assert_array_almost_equal(preds_orig, preds_loaded)


class TestMLPipelineIntegration:
    """End-to-end integration tests."""
    
    def test_full_production_pipeline(self):
        """Test complete production forecasting pipeline."""
        # Small dataset for speed
        forecaster, train_metrics, test_metrics = train_production_model(
            n_days=30,
            freq_hours=12,
            test_size=0.25,
            random_state=42,
            save_path=None
        )
        
        assert forecaster.is_fitted
        assert train_metrics["train_r2"] > 0.5  # Should have some predictive power
        assert test_metrics["test_r2"] > 0.3
        assert forecaster.feature_names is not None
        assert len(forecaster.feature_names) > 5
    
    def test_full_risk_pipeline(self):
        """Test complete risk prediction pipeline."""
        predictor, train_metrics, test_metrics = train_risk_model(
            risk_target="rod_float_risk",
            n_days=30,
            freq_hours=12,
            test_size=0.25,
            random_state=42,
            save_path=None
        )
        
        assert predictor.is_fitted
        assert train_metrics["train_r2"] > 0.3
        assert predictor.feature_names is not None
    
    def test_feature_lists_documented(self):
        """Verify feature lists are as expected."""
        df = generate_training_data(n_days=10, freq_hours=12, seed=42)
        builder = FeatureBuilder(add_derived=True)
        
        X_prod, _ = builder.get_production_features(df)
        X_risk, _ = builder.get_risk_features(df, "rod_float_risk")
        
        # Production features should not include targets
        prod_features = list(X_prod.columns)
        assert "production_rate_stb_d" not in prod_features
        assert "rod_float_risk" not in prod_features
        assert "impact_loading_risk" not in prod_features
        
        # Risk features should not include any risk targets or production
        risk_features = list(X_risk.columns)
        assert "production_rate_stb_d" not in risk_features
        assert "rod_float_risk" not in risk_features
        assert "impact_loading_risk" not in risk_features
        assert "gas_lock_risk" not in risk_features
        
        print(f"\nProduction features ({len(prod_features)}): {sorted(prod_features)}")
        print(f"Risk features ({len(risk_features)}): {sorted(risk_features)}")


class TestExplainability:
    """Test explainability features."""
    
    def test_production_feature_importance_structure(self):
        df = generate_training_data(n_days=30, freq_hours=12, seed=42)
        train_df, _ = split_train_test(df, test_size=0.2, random_state=42)
        
        forecaster = ProductionForecaster(n_estimators=50, random_state=42)
        forecaster.train(train_df)
        
        importance = forecaster.get_feature_importance(20)
        
        # Should have feature and importance columns
        assert list(importance.columns) == ["feature", "importance"]
        # Should be sorted descending
        assert importance["importance"].is_monotonic_decreasing
    
    def test_risk_feature_importance_structure(self):
        df = generate_training_data(n_days=30, freq_hours=12, seed=42)
        train_df, _ = split_train_test(df, test_size=0.2, random_state=42)
        
        predictor = RiskPredictor(risk_target="rod_float_risk", n_estimators=50, random_state=42)
        predictor.train(train_df)
        
        importance = predictor.get_feature_importance(20)
        
        assert list(importance.columns) == ["feature", "importance"]
        assert importance["importance"].is_monotonic_decreasing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])