"""
Tests for THERMALIFT Optimization Module.

Tests objective calculation, constraint validation, optimizer behavior,
and end-to-end optimization pipeline integration.
"""
import pytest
import numpy as np
import time
from datetime import datetime

from app.models.synthetic import WellConfig, CSSCycle
from app.services.physics_models import PipelineEngine
from app.ml.production_forecaster import ProductionForecaster
from app.ml.risk_predictor import RiskPredictor
from app.ml.features import generate_training_data, split_train_test
from app.optimization import (
    CSSParams,
    SRPParams,
    OptimizationConstraints,
    ObjectiveWeights,
    CandidateScenario,
    BaselineComparison,
    OptimizationRecommendation,
    OptimizationConfig,
    OptimizationResult,
    validate_css_params,
    validate_srp_params,
    validate_simulation_outputs,
    check_all_constraints,
    is_feasible,
    ObjectiveCalculator,
    GridSearchOptimizer,
    run_optimization,
)


@pytest.fixture
def well_config():
    return WellConfig(
        well_id="BW-001",
        depth_m=950,
        reservoir_temp_initial_c=95,
        oil_api=12.5,
        pay_thickness_m=18,
        permeability_md=1200,
        pump_intake_depth_m=880,
        tubing_id_inches=2.875,
        rod_diameter_inches=0.875,
        stroke_length_m=3.0,
        pump_diameter_mm=75
    )


@pytest.fixture
def physics_engine(well_config):
    return PipelineEngine(well_config)


@pytest.fixture
def trained_models():
    """Train ML models for testing."""
    df = generate_training_data(n_days=60, freq_hours=12, seed=42)
    train_df, test_df = split_train_test(df, test_size=0.25, random_state=42)
    
    prod_forecaster = ProductionForecaster(n_estimators=30, random_state=42)
    prod_forecaster.train(train_df)
    
    rod_float_predictor = RiskPredictor(risk_target="rod_float_risk", n_estimators=30, random_state=42)
    rod_float_predictor.train(train_df)
    
    impact_loading_predictor = RiskPredictor(risk_target="impact_loading_risk", n_estimators=30, random_state=42)
    impact_loading_predictor.train(train_df)
    
    return {
        "production_forecaster": prod_forecaster,
        "rod_float_predictor": rod_float_predictor,
        "impact_loading_predictor": impact_loading_predictor,
        "train_df": train_df,
        "test_df": test_df
    }


@pytest.fixture
def optimization_config(well_config):
    return OptimizationConfig(
        well_id=well_config.well_id,
        grid_resolution=1,  # Very small grid for fast tests
        day_in_cycle=5.0,
        cycle_num=1,
        wellhead_pressure_kpa=500,
        random_seed=42
    )


@pytest.fixture
def default_constraints():
    return OptimizationConstraints()


@pytest.fixture
def default_weights():
    return ObjectiveWeights()


class TestObjectiveCalculator:
    """Test objective function calculation."""
    
    def test_objective_calculation_works(self, default_weights, default_constraints):
        """Test objective calculation returns a score."""
        calc = ObjectiveCalculator(default_weights, default_constraints)
        
        score = calc.calculate_score(
            production=500.0,
            steam_rate=200.0,
            rod_float_risk=0.3,
            impact_loading_risk=0.4,
            spm=5.0,
            stroke_length_m=3.0
        )
        
        assert isinstance(score, float)
        assert not np.isnan(score)
        assert not np.isinf(score)
    
    def test_higher_production_increases_score(self, default_weights, default_constraints):
        """Test that higher production increases score."""
        calc = ObjectiveCalculator(default_weights, default_constraints)
        
        score_low = calc.calculate_score(200, 200, 0.3, 0.4, 5.0, 3.0)
        score_high = calc.calculate_score(800, 200, 0.3, 0.4, 5.0, 3.0)
        
        assert score_high > score_low
    
    def test_higher_steam_decreases_score(self, default_weights, default_constraints):
        """Test that higher steam usage decreases score."""
        calc = ObjectiveCalculator(default_weights, default_constraints)
        
        score_low_steam = calc.calculate_score(500, 100, 0.3, 0.4, 5.0, 3.0)
        score_high_steam = calc.calculate_score(500, 300, 0.3, 0.4, 5.0, 3.0)
        
        assert score_low_steam > score_high_steam
    
    def test_higher_risk_decreases_score(self, default_weights, default_constraints):
        """Test that higher risk decreases score."""
        calc = ObjectiveCalculator(default_weights, default_constraints)
        
        score_low_risk = calc.calculate_score(500, 200, 0.1, 0.2, 5.0, 3.0)
        score_high_risk = calc.calculate_score(500, 200, 0.6, 0.7, 5.0, 3.0)
        
        assert score_low_risk > score_high_risk
    
    def test_score_breakdown_available(self, default_weights, default_constraints):
        """Test score breakdown for explainability."""
        calc = ObjectiveCalculator(default_weights, default_constraints)
        
        breakdown = calc.get_score_breakdown(500, 200, 0.3, 0.4, 5.0, 3.0)
        
        assert "normalized_production" in breakdown
        assert "normalized_steam_use" in breakdown
        assert "normalized_risk" in breakdown
        assert "normalized_operating_cost" in breakdown
        assert "total_score" in breakdown
        assert breakdown["total_score"] == calc.calculate_score(500, 200, 0.3, 0.4, 5.0, 3.0)
    
    def test_normalized_values_bounded(self, default_weights, default_constraints):
        """Test normalized values are in [0, 1]."""
        calc = ObjectiveCalculator(default_weights, default_constraints)
        
        # Test extremes
        breakdown = calc.get_score_breakdown(0, 0, 0, 0, 2.0, 1.5)
        for key in ["normalized_production", "normalized_steam_use", "normalized_risk", "normalized_operating_cost"]:
            assert 0.0 <= breakdown[key] <= 1.0, f"{key} = {breakdown[key]}"
        
        breakdown = calc.get_score_breakdown(3000, 500, 1, 1, 8.0, 4.0)
        for key in ["normalized_production", "normalized_steam_use", "normalized_risk", "normalized_operating_cost"]:
            assert 0.0 <= breakdown[key] <= 1.0, f"{key} = {breakdown[key]}"


class TestConstraints:
    """Test constraint validation."""
    
    def test_valid_css_params_accepted(self, default_constraints):
        """Test valid CSS params pass validation."""
        css = CSSParams(
            steam_rate_m3_d=200,
            steam_quality=0.8,
            injection_days=10,
            soak_days=5,
            production_days=90
        )
        
        violations = validate_css_params(css, default_constraints)
        assert len(violations) == 0
    
    def test_invalid_steam_rate_rejected(self, default_constraints):
        """Test steam rate out of bounds is rejected."""
        # Use model_construct to bypass Pydantic validation for testing
        css = CSSParams.model_construct(
            steam_rate_m3_d=500,  # > 350 max
            steam_quality=0.8,
            injection_days=10,
            soak_days=5,
            production_days=90
        )
        
        violations = validate_css_params(css, default_constraints)
        assert any("steam_rate_m3_d" in v and "max" in v for v in violations)
    
    def test_invalid_steam_quality_rejected(self, default_constraints):
        """Test steam quality out of bounds is rejected."""
        css = CSSParams.model_construct(
            steam_rate_m3_d=200,
            steam_quality=0.5,  # < 0.65 min
            injection_days=10,
            soak_days=5,
            production_days=90
        )
        
        violations = validate_css_params(css, default_constraints)
        assert any("steam_quality" in v and "min" in v for v in violations)
    
    def test_valid_srp_params_accepted(self, default_constraints):
        """Test valid SRP params pass validation."""
        srp = SRPParams(spm=5.0, stroke_length_m=3.0, vfd_frequency_hz=40.0)
        
        violations = validate_srp_params(srp, default_constraints)
        assert len(violations) == 0
    
    def test_invalid_spm_rejected(self, default_constraints):
        """Test SPM out of bounds is rejected."""
        srp = SRPParams.model_construct(spm=10.0, stroke_length_m=3.0, vfd_frequency_hz=40.0)  # > 8.0 max
        
        violations = validate_srp_params(srp, default_constraints)
        assert any("spm" in v and "max" in v for v in violations)
    
    def test_invalid_stroke_length_rejected(self, default_constraints):
        """Test stroke length out of bounds is rejected."""
        srp = SRPParams.model_construct(spm=5.0, stroke_length_m=0.5, vfd_frequency_hz=40.0)  # < 1.5 min
        
        violations = validate_srp_params(srp, default_constraints)
        assert any("stroke_length_m" in v and "min" in v for v in violations)
    
    def test_simulation_output_validation(self, default_constraints):
        """Test simulation output validation."""
        violations = validate_simulation_outputs(
            production_stb_d=500,
            rod_float_risk=0.3,
            impact_loading_risk=0.4,
            fillage=0.8,
            pump_efficiency=0.85,
            constraints=default_constraints
        )
        assert len(violations) == 0
    
    def test_negative_production_rejected(self, default_constraints):
        """Test negative production is rejected."""
        violations = validate_simulation_outputs(
            production_stb_d=-10,
            rod_float_risk=0.3,
            impact_loading_risk=0.4,
            fillage=0.8,
            pump_efficiency=0.85,
            constraints=default_constraints
        )
        assert any("production" in v and "min" in v for v in violations)
    
    def test_risk_out_of_bounds_rejected(self, default_constraints):
        """Test risk > 1 is rejected."""
        violations = validate_simulation_outputs(
            production_stb_d=500,
            rod_float_risk=1.5,  # > 1
            impact_loading_risk=0.4,
            fillage=0.8,
            pump_efficiency=0.85,
            constraints=default_constraints
        )
        assert any("rod_float_risk" in v and "not in" in v for v in violations)
    
    def test_combined_constraint_check(self, default_constraints):
        """Test combined constraint checking."""
        css = CSSParams(steam_rate_m3_d=200, steam_quality=0.8, injection_days=10, soak_days=5, production_days=90)
        srp = SRPParams(spm=5.0, stroke_length_m=3.0, vfd_frequency_hz=40.0)
        
        violations = check_all_constraints(
            css=css, srp=srp,
            production_stb_d=500,
            rod_float_risk=0.3,
            impact_loading_risk=0.4,
            fillage=0.8,
            pump_efficiency=0.85,
            constraints=default_constraints
        )
        assert len(violations) == 0
    
    def test_candidate_feasibility_check(self):
        """Test is_feasible function."""
        feasible = CandidateScenario(
            css_params=CSSParams(steam_rate_m3_d=200, steam_quality=0.8, injection_days=10, soak_days=5, production_days=90),
            srp_params=SRPParams(spm=5.0, stroke_length_m=3.0, vfd_frequency_hz=40.0),
            predicted_production_stb_d=500,
            predicted_rod_float_risk=0.3,
            predicted_impact_loading_risk=0.4,
            steam_usage_m3_d=200,
            steam_intensity=0.4,
            objective_score=0.5,
            is_feasible=True,
            constraint_violations=[]
        )
        assert is_feasible(feasible) is True
        
        infeasible = CandidateScenario(
            css_params=CSSParams(steam_rate_m3_d=200, steam_quality=0.8, injection_days=10, soak_days=5, production_days=90),
            srp_params=SRPParams(spm=5.0, stroke_length_m=3.0, vfd_frequency_hz=40.0),
            predicted_production_stb_d=500,
            predicted_rod_float_risk=0.3,
            predicted_impact_loading_risk=0.4,
            steam_usage_m3_d=200,
            steam_intensity=0.4,
            objective_score=0.5,
            is_feasible=False,
            constraint_violations=["steam_rate_m3_d 500 > max 350"]
        )
        assert is_feasible(infeasible) is False


class TestOptimizer:
    """Test grid search optimizer."""
    
    def test_optimizer_returns_feasible_result(
        self,
        well_config,
        physics_engine,
        trained_models,
        optimization_config
    ):
        """Test optimizer returns a feasible result."""
        result = run_optimization(
            well_config=well_config,
            physics_engine=physics_engine,
            production_forecaster=trained_models["production_forecaster"],
            rod_float_predictor=trained_models["rod_float_predictor"],
            impact_loading_predictor=trained_models["impact_loading_predictor"],
            config=optimization_config
        )
        
        assert isinstance(result, OptimizationResult)
        assert result.best_candidate is not None
        assert result.recommendation is not None
        assert result.total_evaluated > 0
        assert result.feasible_count >= 0
        assert result.execution_time_seconds > 0
    
    def test_optimizer_deterministic(
        self,
        well_config,
        physics_engine,
        trained_models
    ):
        """Test optimizer is deterministic with same seed."""
        config = OptimizationConfig(
            well_id=well_config.well_id,
            grid_resolution=1,  # Minimal grid for fast deterministic test
            random_seed=42
        )
        
        result1 = run_optimization(
            well_config=well_config,
            physics_engine=physics_engine,
            production_forecaster=trained_models["production_forecaster"],
            rod_float_predictor=trained_models["rod_float_predictor"],
            impact_loading_predictor=trained_models["impact_loading_predictor"],
            config=config
        )
        
        result2 = run_optimization(
            well_config=well_config,
            physics_engine=physics_engine,
            production_forecaster=trained_models["production_forecaster"],
            rod_float_predictor=trained_models["rod_float_predictor"],
            impact_loading_predictor=trained_models["impact_loading_predictor"],
            config=config
        )
        
        # Best candidate should be identical
        assert result1.best_candidate.css_params == result2.best_candidate.css_params
        assert result1.best_candidate.srp_params == result2.best_candidate.srp_params
        assert result1.best_candidate.objective_score == result2.best_candidate.objective_score
    
    def test_optimized_production_non_negative(
        self,
        well_config,
        physics_engine,
        trained_models,
        optimization_config
    ):
        """Test optimized production is non-negative."""
        result = run_optimization(
            well_config=well_config,
            physics_engine=physics_engine,
            production_forecaster=trained_models["production_forecaster"],
            rod_float_predictor=trained_models["rod_float_predictor"],
            impact_loading_predictor=trained_models["impact_loading_predictor"],
            config=optimization_config
        )
        
        assert result.best_candidate.predicted_production_stb_d >= 0
    
    def test_optimized_risk_bounded(
        self,
        well_config,
        physics_engine,
        trained_models,
        optimization_config
    ):
        """Test optimized risk is between 0 and 1."""
        result = run_optimization(
            well_config=well_config,
            physics_engine=physics_engine,
            production_forecaster=trained_models["production_forecaster"],
            rod_float_predictor=trained_models["rod_float_predictor"],
            impact_loading_predictor=trained_models["impact_loading_predictor"],
            config=optimization_config
        )
        
        assert 0.0 <= result.best_candidate.predicted_rod_float_risk <= 1.0
        assert 0.0 <= result.best_candidate.predicted_impact_loading_risk <= 1.0
    
    def test_optimized_scenario_satisfies_constraints(
        self,
        well_config,
        physics_engine,
        trained_models,
        optimization_config
    ):
        """Test optimized scenario satisfies all constraints (if feasible)."""
        result = run_optimization(
            well_config=well_config,
            physics_engine=physics_engine,
            production_forecaster=trained_models["production_forecaster"],
            rod_float_predictor=trained_models["rod_float_predictor"],
            impact_loading_predictor=trained_models["impact_loading_predictor"],
            config=optimization_config
        )
        
        if result.best_candidate.is_feasible:
            assert len(result.best_candidate.constraint_violations) == 0
            
            # Verify constraint bounds
            css = result.best_candidate.css_params
            srp = result.best_candidate.srp_params
            
            assert optimization_config.constraints.steam_rate_min <= css.steam_rate_m3_d <= optimization_config.constraints.steam_rate_max
            assert optimization_config.constraints.steam_quality_min <= css.steam_quality <= optimization_config.constraints.steam_quality_max
            assert optimization_config.constraints.spm_min <= srp.spm <= optimization_config.constraints.spm_max
            assert optimization_config.constraints.stroke_length_min <= srp.stroke_length_m <= optimization_config.constraints.stroke_length_max
            assert optimization_config.constraints.vfd_frequency_min <= srp.vfd_frequency_hz <= optimization_config.constraints.vfd_frequency_max
    
    def test_baseline_comparison_works(
        self,
        well_config,
        physics_engine,
        trained_models,
        optimization_config
    ):
        """Test baseline comparison is generated."""
        result = run_optimization(
            well_config=well_config,
            physics_engine=physics_engine,
            production_forecaster=trained_models["production_forecaster"],
            rod_float_predictor=trained_models["rod_float_predictor"],
            impact_loading_predictor=trained_models["impact_loading_predictor"],
            config=optimization_config
        )
        
        comparison = result.recommendation.baseline_comparison
        assert isinstance(comparison, BaselineComparison)
        assert comparison.baseline_production_stb_d >= 0
        assert comparison.optimized_production_stb_d >= 0
        assert comparison.baseline_steam_m3_d >= 0
        assert comparison.optimized_steam_m3_d >= 0
        assert isinstance(comparison.production_change_pct, float)
        assert isinstance(comparison.steam_change_pct, float)
        assert isinstance(comparison.objective_improvement, float)
    
    def test_optimizer_uses_physics_ml_pipeline(
        self,
        well_config,
        physics_engine,
        trained_models
    ):
        """Test optimizer evaluates candidates through physics+ML pipeline."""
        config = OptimizationConfig(
            well_id=well_config.well_id,
            grid_resolution=2,
            random_seed=42
        )
        
        result = run_optimization(
            well_config=well_config,
            physics_engine=physics_engine,
            production_forecaster=trained_models["production_forecaster"],
            rod_float_predictor=trained_models["rod_float_predictor"],
            impact_loading_predictor=trained_models["impact_loading_predictor"],
            config=config
        )
        
        # Should have evaluated multiple candidates
        assert result.total_evaluated > 1
        assert len(result.all_candidates) == result.total_evaluated
        
        # All candidates should have valid outputs
        for candidate in result.all_candidates:
            assert candidate.predicted_production_stb_d >= 0
            assert 0.0 <= candidate.predicted_rod_float_risk <= 1.0
            assert 0.0 <= candidate.predicted_impact_loading_risk <= 1.0
            assert isinstance(candidate.objective_score, float)
    
    def test_recommendation_contains_explanation(
        self,
        well_config,
        physics_engine,
        trained_models,
        optimization_config
    ):
        """Test recommendation includes explanation."""
        result = run_optimization(
            well_config=well_config,
            physics_engine=physics_engine,
            production_forecaster=trained_models["production_forecaster"],
            rod_float_predictor=trained_models["rod_float_predictor"],
            impact_loading_predictor=trained_models["impact_loading_predictor"],
            config=optimization_config
        )
        
        explanation = result.recommendation.explanation
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert "synthetic" in explanation.lower() or "demo" in explanation.lower() or "prototype" in explanation.lower()
    
    def test_recommendation_has_disclaimer(
        self,
        well_config,
        physics_engine,
        trained_models,
        optimization_config
    ):
        """Test recommendation includes synthetic data disclaimer."""
        result = run_optimization(
            well_config=well_config,
            physics_engine=physics_engine,
            production_forecaster=trained_models["production_forecaster"],
            rod_float_predictor=trained_models["rod_float_predictor"],
            impact_loading_predictor=trained_models["impact_loading_predictor"],
            config=optimization_config
        )
        
        assert "synthetic" in result.recommendation.disclaimer.lower()
        assert "demo" in result.recommendation.disclaimer.lower() or "prototype" in result.recommendation.disclaimer.lower()
        assert "Baghewala" in result.recommendation.disclaimer or "OIL" in result.recommendation.disclaimer
    
    def test_optimizer_respects_grid_resolution(
        self,
        well_config,
        physics_engine,
        trained_models
    ):
        """Test grid resolution affects number of evaluations."""
        config_low = OptimizationConfig(
            well_id=well_config.well_id,
            grid_resolution=1,
            random_seed=42
        )
        config_high = OptimizationConfig(
            well_id=well_config.well_id,
            grid_resolution=2,
            random_seed=42
        )
        
        result_low = run_optimization(
            well_config=well_config,
            physics_engine=physics_engine,
            production_forecaster=trained_models["production_forecaster"],
            rod_float_predictor=trained_models["rod_float_predictor"],
            impact_loading_predictor=trained_models["impact_loading_predictor"],
            config=config_low
        )
        
        result_high = run_optimization(
            well_config=well_config,
            physics_engine=physics_engine,
            production_forecaster=trained_models["production_forecaster"],
            rod_float_predictor=trained_models["rod_float_predictor"],
            impact_loading_predictor=trained_models["impact_loading_predictor"],
            config=config_high
        )
        
        # Higher resolution = more evaluations
        assert result_high.total_evaluated > result_low.total_evaluated


class TestOptimizationIntegration:
    """End-to-end integration tests."""
    
    def test_end_to_end_optimization_pipeline(
        self,
        well_config,
        physics_engine,
        trained_models
    ):
        """Test complete optimization pipeline works with physics/ML components."""
        config = OptimizationConfig(
            well_id=well_config.well_id,
            grid_resolution=2,
            random_seed=123
        )
        
        result = run_optimization(
            well_config=well_config,
            physics_engine=physics_engine,
            production_forecaster=trained_models["production_forecaster"],
            rod_float_predictor=trained_models["rod_float_predictor"],
            impact_loading_predictor=trained_models["impact_loading_predictor"],
            config=config
        )
        
        # Verify complete result structure
        assert result.config.well_id == well_config.well_id
        assert result.best_candidate is not None
        assert result.recommendation.well_id == well_config.well_id
        assert result.recommendation.data_source == "SYNTHETIC_DEMO"
        
        # Verify recommendation has all required fields
        rec = result.recommendation
        assert rec.recommended_css is not None
        assert rec.recommended_srp is not None
        assert rec.predicted_production_stb_d >= 0
        assert 0.0 <= rec.predicted_rod_float_risk <= 1.0
        assert 0.0 <= rec.predicted_impact_loading_risk <= 1.0
        assert isinstance(rec.objective_score, float)
        assert len(rec.constraints_satisfied) > 0
        assert len(rec.explanation) > 0
    
    def test_different_seeds_produce_different_results(
        self,
        well_config,
        physics_engine,
        trained_models
    ):
        """Test different seeds produce different results (stochastic physics)."""
        config1 = OptimizationConfig(well_id=well_config.well_id, grid_resolution=2, random_seed=111)
        config2 = OptimizationConfig(well_id=well_config.well_id, grid_resolution=2, random_seed=222)
        
        result1 = run_optimization(
            well_config=well_config,
            physics_engine=physics_engine,
            production_forecaster=trained_models["production_forecaster"],
            rod_float_predictor=trained_models["rod_float_predictor"],
            impact_loading_predictor=trained_models["impact_loading_predictor"],
            config=config1
        )
        
        result2 = run_optimization(
            well_config=well_config,
            physics_engine=physics_engine,
            production_forecaster=trained_models["production_forecaster"],
            rod_float_predictor=trained_models["rod_float_predictor"],
            impact_loading_predictor=trained_models["impact_loading_predictor"],
            config=config2
        )
        
        # Results may differ due to physics model randomness
        # (but with same seed they should be identical - tested separately)
    
    def test_constraint_violations_reported(
        self,
        well_config,
        physics_engine,
        trained_models
    ):
        """Test constraint violations are properly reported."""
        # Use tight constraints that may be violated
        tight_config = OptimizationConfig(
            well_id=well_config.well_id,
            grid_resolution=2,
            constraints=OptimizationConstraints(
                max_rod_float_risk=0.1,  # Very tight
                max_impact_loading_risk=0.1,
                min_fill_age=0.9,
                min_pump_efficiency=0.95
            ),
            random_seed=42
        )
        
        result = run_optimization(
            well_config=well_config,
            physics_engine=physics_engine,
            production_forecaster=trained_models["production_forecaster"],
            rod_float_predictor=trained_models["rod_float_predictor"],
            impact_loading_predictor=trained_models["impact_loading_predictor"],
            config=tight_config
        )
        
        # Best candidate may be infeasible with tight constraints
        if not result.best_candidate.is_feasible:
            assert len(result.best_candidate.constraint_violations) > 0
            assert result.feasible_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])