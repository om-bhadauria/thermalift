"""
Grid search optimizer for THERMALIFT.
Simple, deterministic, explainable optimization using existing physics/ML pipeline.
"""
import time
import numpy as np
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass

from app.models.synthetic import WellConfig, CSSCycle
from app.services.physics_models import PipelineEngine
from app.ml.production_forecaster import ProductionForecaster
from app.ml.risk_predictor import RiskPredictor
from app.optimization.schemas import (
    CSSParams,
    SRPParams,
    OptimizationConfig,
    OptimizationConstraints,
    ObjectiveWeights,
    CandidateScenario,
    BaselineComparison,
    OptimizationRecommendation,
    OptimizationResult,
)
from app.optimization.constraints import check_all_constraints, is_feasible
from app.optimization.objectives import ObjectiveCalculator


@dataclass
class EvaluationResult:
    """Internal result from evaluating a candidate."""
    css: CSSParams
    srp: SRPParams
    production: float
    rod_float_risk: float
    impact_loading_risk: float
    fillage: float
    pump_efficiency: float
    steam_usage: float
    steam_intensity: float
    violations: List[str]
    score: float


class GridSearchOptimizer:
    """
    Deterministic grid search optimizer.
    
    Evaluates candidates through physics pipeline + ML models.
    Returns best feasible candidate.
    """
    
    def __init__(
        self,
        well_config: WellConfig,
        physics_engine: PipelineEngine,
        production_forecaster: ProductionForecaster,
        rod_float_predictor: RiskPredictor,
        impact_loading_predictor: RiskPredictor,
        config: OptimizationConfig
    ):
        self.well_config = well_config
        self.physics = physics_engine
        self.prod_forecaster = production_forecaster
        self.rod_float_predictor = rod_float_predictor
        self.impact_loading_predictor = impact_loading_predictor
        self.config = config
        self.constraints = config.constraints
        self.weights = config.weights
        self.objective = ObjectiveCalculator(self.weights, self.constraints)
        self.resolution = config.grid_resolution
        # Create a seeded physics engine for deterministic evaluation
        self._seeded_physics = PipelineEngine(well_config, random_seed=config.random_seed)
    
    def _generate_css_grid(self) -> List[CSSParams]:
        """Generate grid of CSS parameter combinations."""
        css_list = []
        
        steam_rates = np.linspace(
            self.constraints.steam_rate_min,
            self.constraints.steam_rate_max,
            self.resolution
        )
        steam_qualities = np.linspace(
            self.constraints.steam_quality_min,
            self.constraints.steam_quality_max,
            self.resolution
        )
        injection_days = np.linspace(
            self.constraints.injection_days_min,
            self.constraints.injection_days_max,
            self.resolution
        )
        soak_days = np.linspace(
            self.constraints.soak_days_min,
            self.constraints.soak_days_max,
            self.resolution
        )
        production_days = np.linspace(
            self.constraints.production_days_min,
            self.constraints.production_days_max,
            self.resolution
        )
        
        for sr in steam_rates:
            for sq in steam_qualities:
                for inj in injection_days:
                    for soak in soak_days:
                        for prod in production_days:
                            css_list.append(CSSParams(
                                steam_rate_m3_d=round(float(sr), 1),
                                steam_quality=round(float(sq), 3),
                                injection_days=round(float(inj), 1),
                                soak_days=round(float(soak), 1),
                                production_days=round(float(prod), 1)
                            ))
        
        return css_list
    
    def _generate_srp_grid(self) -> List[SRPParams]:
        """Generate grid of SRP parameter combinations."""
        srp_list = []
        
        spm_values = np.linspace(
            self.constraints.spm_min,
            self.constraints.spm_max,
            self.resolution
        )
        stroke_values = np.linspace(
            self.constraints.stroke_length_min,
            self.constraints.stroke_length_max,
            self.resolution
        )
        vfd_values = np.linspace(
            self.constraints.vfd_frequency_min,
            self.constraints.vfd_frequency_max,
            self.resolution
        )
        
        for spm in spm_values:
            for stroke in stroke_values:
                for vfd in vfd_values:
                    srp_list.append(SRPParams(
                        spm=round(float(spm), 2),
                        stroke_length_m=round(float(stroke), 2),
                        vfd_frequency_hz=round(float(vfd), 1)
                    ))
        
        return srp_list
    
    def _evaluate_candidate(
        self,
        css: CSSParams,
        srp: SRPParams
    ) -> EvaluationResult:
        """Evaluate a single candidate through physics + ML pipeline."""
        
        # Convert to physics model format
        css_cycle = CSSCycle(
            cycle_num=self.config.cycle_num,
            steam_rate_m3_d=css.steam_rate_m3_d,
            steam_quality=css.steam_quality,
            injection_days=css.injection_days,
            soak_days=css.soak_days,
            production_days=css.production_days
        )
        
        srp_dict = {
            "spm": srp.spm,
            "stroke_length_m": srp.stroke_length_m,
            "vfd_frequency_hz": srp.vfd_frequency_hz
        }
        
        # Run physics simulation with seeded engine for determinism
        state = self._seeded_physics.run_simulation(
            css_params=css_cycle,
            srp_params=srp_dict,
            day_in_cycle=self.config.day_in_cycle,
            cycle_num=self.config.cycle_num,
            wellhead_pressure_kpa=self.config.wellhead_pressure_kpa
        )
        
        # Prepare state dict for ML models
        state_dict = state.model_dump()
        
        # Get ML predictions
        try:
            ml_production = self.prod_forecaster.predict_single(state_dict)
        except Exception:
            ml_production = state.production_rate_stb_d
        
        try:
            ml_rod_float = self.rod_float_predictor.predict_single(state_dict)
        except Exception:
            ml_rod_float = state.rod_float_risk
        
        try:
            ml_impact_loading = self.impact_loading_predictor.predict_single(state_dict)
        except Exception:
            ml_impact_loading = state.impact_loading_risk
        
        # Steam usage (only during injection)
        steam_usage = css.steam_rate_m3_d if self.config.day_in_cycle < css.injection_days else 0.0
        
        # Steam intensity (steam per barrel)
        steam_intensity = steam_usage / max(ml_production, 0.1) if steam_usage > 0 else 0.0
        
        # Check constraints
        violations = check_all_constraints(
            css=css,
            srp=srp,
            production_stb_d=ml_production,
            rod_float_risk=ml_rod_float,
            impact_loading_risk=ml_impact_loading,
            fillage=state.fillage,
            pump_efficiency=state.pump_efficiency,
            constraints=self.constraints
        )
        
        # Calculate objective score
        score = self.objective.calculate_score(
            production=ml_production,
            steam_rate=steam_usage,
            rod_float_risk=ml_rod_float,
            impact_loading_risk=ml_impact_loading,
            spm=srp.spm,
            stroke_length_m=srp.stroke_length_m
        )
        
        return EvaluationResult(
            css=css,
            srp=srp,
            production=ml_production,
            rod_float_risk=ml_rod_float,
            impact_loading_risk=ml_impact_loading,
            fillage=state.fillage,
            pump_efficiency=state.pump_efficiency,
            steam_usage=steam_usage,
            steam_intensity=steam_intensity,
            violations=violations,
            score=score
        )
    
    def _evaluation_result_to_candidate(self, result: EvaluationResult) -> CandidateScenario:
        """Convert internal evaluation result to CandidateScenario."""
        is_feas = len(result.violations) == 0
        
        return CandidateScenario(
            css_params=result.css,
            srp_params=result.srp,
            predicted_production_stb_d=round(result.production, 1),
            predicted_rod_float_risk=round(result.rod_float_risk, 3),
            predicted_impact_loading_risk=round(result.impact_loading_risk, 3),
            steam_usage_m3_d=round(result.steam_usage, 1),
            steam_intensity=round(result.steam_intensity, 3),
            objective_score=round(result.score, 4),
            is_feasible=is_feas,
            constraint_violations=result.violations
        )
    
    def optimize(self) -> OptimizationResult:
        """
        Run grid search optimization.
        Returns best feasible candidate and full results.
        """
        start_time = time.time()
        
        # Generate parameter grids
        css_grid = self._generate_css_grid()
        srp_grid = self._generate_srp_grid()
        
        total_combinations = len(css_grid) * len(srp_grid)
        
        all_candidates = []
        best_feasible = None
        best_score = -np.inf
        feasible_count = 0
        
        # Grid search
        for css in css_grid:
            for srp in srp_grid:
                result = self._evaluate_candidate(css, srp)
                candidate = self._evaluation_result_to_candidate(result)
                all_candidates.append(candidate)
                
                if is_feasible(candidate):
                    feasible_count += 1
                    if result.score > best_score:
                        best_score = result.score
                        best_feasible = candidate
        
        execution_time = time.time() - start_time
        
        # If no feasible candidate found, return best infeasible with warning
        if best_feasible is None:
            # Sort by fewest violations then by score
            sorted_candidates = sorted(
                all_candidates,
                key=lambda c: (len(c.constraint_violations), -c.objective_score)
            )
            best_feasible = sorted_candidates[0]
            best_feasible.is_feasible = False
        
        # Build recommendation
        recommendation = self._build_recommendation(best_feasible, all_candidates)
        
        return OptimizationResult(
            config=self.config,
            best_candidate=best_feasible,
            all_candidates=all_candidates,
            recommendation=recommendation,
            total_evaluated=total_combinations,
            feasible_count=feasible_count,
            execution_time_seconds=round(execution_time, 2)
        )
    
    def _build_recommendation(
        self,
        best: CandidateScenario,
        all_candidates: List[CandidateScenario]
    ) -> OptimizationRecommendation:
        """Build final recommendation with baseline comparison."""
        
        # Define baseline (mid-range parameters)
        baseline_css = CSSParams(
            steam_rate_m3_d=200.0,
            steam_quality=0.80,
            injection_days=12.0,
            soak_days=5.0,
            production_days=90.0
        )
        baseline_srp = SRPParams(
            spm=5.0,
            stroke_length_m=3.0,
            vfd_frequency_hz=40.0
        )
        
        # Evaluate baseline
        baseline_result = self._evaluate_candidate(baseline_css, baseline_srp)
        baseline_candidate = self._evaluation_result_to_candidate(baseline_result)
        
        # Build comparison
        prod_change = 0.0
        if baseline_candidate.predicted_production_stb_d > 0:
            prod_change = (
                (best.predicted_production_stb_d - baseline_candidate.predicted_production_stb_d)
                / baseline_candidate.predicted_production_stb_d * 100
            )
        
        steam_change = 0.0
        if baseline_candidate.steam_usage_m3_d > 0:
            steam_change = (
                (best.steam_usage_m3_d - baseline_candidate.steam_usage_m3_d)
                / baseline_candidate.steam_usage_m3_d * 100
            )
        
        comparison = BaselineComparison(
            baseline_production_stb_d=round(baseline_candidate.predicted_production_stb_d, 1),
            optimized_production_stb_d=best.predicted_production_stb_d,
            production_change_pct=round(prod_change, 1),
            baseline_steam_m3_d=round(baseline_candidate.steam_usage_m3_d, 1),
            optimized_steam_m3_d=best.steam_usage_m3_d,
            steam_change_pct=round(steam_change, 1),
            baseline_rod_float_risk=round(baseline_candidate.predicted_rod_float_risk, 3),
            optimized_rod_float_risk=best.predicted_rod_float_risk,
            baseline_impact_loading_risk=round(baseline_candidate.predicted_impact_loading_risk, 3),
            optimized_impact_loading_risk=best.predicted_impact_loading_risk,
            baseline_objective_score=round(baseline_candidate.objective_score, 4),
            optimized_objective_score=best.objective_score,
            objective_improvement=round(best.objective_score - baseline_candidate.objective_score, 4)
        )
        
        # Constraints satisfied
        constraints_satisfied = []
        if best.is_feasible:
            constraints_satisfied = [
                "steam_rate_bounds",
                "steam_quality_bounds",
                "injection_days_bounds",
                "soak_days_bounds",
                "production_days_bounds",
                "spm_bounds",
                "stroke_length_bounds",
                "vfd_frequency_bounds",
                "production_non_negative",
                "risk_bounds",
                "fillage_bounds",
                "efficiency_bounds"
            ]
        else:
            # List which constraints are satisfied despite violations
            all_constraints = [
                "steam_rate_bounds",
                "steam_quality_bounds",
                "injection_days_bounds",
                "soak_days_bounds",
                "production_days_bounds",
                "spm_bounds",
                "stroke_length_bounds",
                "vfd_frequency_bounds",
                "production_non_negative",
                "risk_bounds",
                "fillage_bounds",
                "efficiency_bounds"
            ]
            for constraint in all_constraints:
                # Check if this specific constraint is violated
                violated = any(constraint.split('_')[0] in v.lower() for v in best.constraint_violations)
                if not violated:
                    constraints_satisfied.append(constraint)
        
        # Build explanation
        explanation = self._generate_explanation(best, baseline_candidate)
        
        return OptimizationRecommendation(
            well_id=self.config.well_id,
            timestamp=time.time(),
            recommended_css=best.css_params,
            recommended_srp=best.srp_params,
            predicted_production_stb_d=best.predicted_production_stb_d,
            predicted_rod_float_risk=best.predicted_rod_float_risk,
            predicted_impact_loading_risk=best.predicted_impact_loading_risk,
            objective_score=best.objective_score,
            baseline_comparison=comparison,
            constraints_satisfied=constraints_satisfied,
            explanation=explanation
        )
    
    def _generate_explanation(
        self,
        best: CandidateScenario,
        baseline: CandidateScenario
    ) -> str:
        """Generate human-readable explanation of recommendation."""
        
        prod_diff = best.predicted_production_stb_d - baseline.predicted_production_stb_d
        steam_diff = best.steam_usage_m3_d - baseline.steam_usage_m3_d
        risk_diff = max(best.predicted_rod_float_risk, best.predicted_impact_loading_risk) - \
                    max(baseline.predicted_rod_float_risk, baseline.predicted_impact_loading_risk)
        
        parts = []
        
        if prod_diff > 0:
            parts.append(f"higher predicted production (+{prod_diff:.1f} STB/d)")
        elif prod_diff < 0:
            parts.append(f"lower predicted production ({prod_diff:.1f} STB/d)")
        else:
            parts.append("similar predicted production")
        
        if steam_diff < 0:
            parts.append(f"reduced steam usage ({steam_diff:.1f} m3/d)")
        elif steam_diff > 0:
            parts.append(f"increased steam usage (+{steam_diff:.1f} m3/d)")
        else:
            parts.append("similar steam usage")
        
        if risk_diff < 0:
            parts.append(f"lower SRP failure risk ({risk_diff:.3f})")
        elif risk_diff > 0:
            parts.append(f"higher SRP failure risk (+{risk_diff:.3f})")
        else:
            parts.append("similar SRP failure risk")
        
        if best.is_feasible:
            feasibility = "within all configured constraints"
        else:
            feasibility = f"violates {len(best.constraint_violations)} constraint(s)"
        
        explanation = (
            f"Selected scenario provides {', '.join(parts)} and is {feasibility}. "
            f"Objective score: {best.objective_score:.4f} vs baseline {baseline.objective_score:.4f}. "
            f"Prototype prediction based on synthetic/demo data."
        )
        
        return explanation


def run_optimization(
    well_config: WellConfig,
    physics_engine: PipelineEngine,
    production_forecaster: ProductionForecaster,
    rod_float_predictor: RiskPredictor,
    impact_loading_predictor: RiskPredictor,
    config: OptimizationConfig = None
) -> OptimizationResult:
    """
    Convenience function to run optimization.
    
    Args:
        well_config: Well configuration
        physics_engine: Physics pipeline engine
        production_forecaster: Trained production ML model
        rod_float_predictor: Trained rod float risk ML model
        impact_loading_predictor: Trained impact loading risk ML model
        config: Optimization configuration (uses defaults if None)
    
    Returns:
        OptimizationResult with best candidate and recommendation
    """
    if config is None:
        config = OptimizationConfig(well_id=well_config.well_id)
    
    optimizer = GridSearchOptimizer(
        well_config=well_config,
        physics_engine=physics_engine,
        production_forecaster=production_forecaster,
        rod_float_predictor=rod_float_predictor,
        impact_loading_predictor=impact_loading_predictor,
        config=config
    )
    
    return optimizer.optimize()