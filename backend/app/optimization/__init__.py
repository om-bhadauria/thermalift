"""
THERMALIFT Optimization Module.

Constrained optimization engine for CSS steam and SRP operations.
Uses existing physics-informed simulation and ML forecasting layers.

All results are based on synthetic/demo data - NOT validated against real Baghewala/OIL field operations.
"""
from app.optimization.schemas import (
    CSSParams,
    SRPParams,
    OptimizationConstraints,
    ObjectiveWeights,
    CandidateScenario,
    BaselineComparison,
    OptimizationRecommendation,
    OptimizationConfig,
    OptimizationResult,
    OperatingMode,
)

from app.optimization.constraints import (
    validate_css_params,
    validate_srp_params,
    validate_simulation_outputs,
    check_all_constraints,
    is_feasible,
)

from app.optimization.objectives import ObjectiveCalculator

from app.optimization.optimizer import GridSearchOptimizer, run_optimization

__all__ = [
    "CSSParams",
    "SRPParams",
    "OptimizationConstraints",
    "ObjectiveWeights",
    "CandidateScenario",
    "BaselineComparison",
    "OptimizationRecommendation",
    "OptimizationConfig",
    "OptimizationResult",
    "OperatingMode",
    "validate_css_params",
    "validate_srp_params",
    "validate_simulation_outputs",
    "check_all_constraints",
    "is_feasible",
    "ObjectiveCalculator",
    "GridSearchOptimizer",
    "run_optimization",
]