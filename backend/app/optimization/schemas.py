"""
Optimization schemas for THERMALIFT.
Defines input parameters, candidate scenarios, and recommendation outputs.

All ranges are DEMO/SYNTHETIC ASSUMPTIONS - NOT field limits.
Optimization results are prototype recommendations from synthetic/demo data.
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class OperatingMode(str, Enum):
    CSS = "CSS"
    SRP = "SRP"
    COUPLED = "COUPLED"


class CSSParams(BaseModel):
    """CSS steam operation parameters - DEMO/SYNTHETIC ranges."""
    steam_rate_m3_d: float = Field(..., ge=100, le=350, description="Steam injection rate (m3/day) - DEMO RANGE")
    steam_quality: float = Field(..., ge=0.65, le=0.90, description="Steam quality fraction - DEMO RANGE")
    injection_days: float = Field(..., ge=5, le=20, description="Injection phase duration (days) - DEMO RANGE")
    soak_days: float = Field(..., ge=1, le=10, description="Soak phase duration (days) - DEMO RANGE")
    production_days: float = Field(..., ge=30, le=150, description="Production phase duration (days) - DEMO RANGE")


class SRPParams(BaseModel):
    """SRP operation parameters - DEMO/SYNTHETIC ranges."""
    spm: float = Field(..., ge=2.0, le=8.0, description="Strokes per minute - DEMO RANGE")
    stroke_length_m: float = Field(..., ge=1.5, le=4.0, description="Stroke length (m) - DEMO RANGE")
    vfd_frequency_hz: float = Field(..., ge=20, le=55, description="VFD frequency (Hz) - DEMO RANGE")


class OptimizationConstraints(BaseModel):
    """Configurable constraint bounds - DEMO/SYNTHETIC values."""
    steam_rate_min: float = 100
    steam_rate_max: float = 350
    steam_quality_min: float = 0.65
    steam_quality_max: float = 0.90
    injection_days_min: float = 5
    injection_days_max: float = 20
    soak_days_min: float = 1
    soak_days_max: float = 10
    production_days_min: float = 30
    production_days_max: float = 150
    spm_min: float = 2.0
    spm_max: float = 8.0
    stroke_length_min: float = 1.5
    stroke_length_max: float = 4.0
    vfd_frequency_min: float = 20
    vfd_frequency_max: float = 55
    max_rod_float_risk: float = 0.7
    max_impact_loading_risk: float = 0.7
    min_production_stb_d: float = 0
    min_fill_age: float = 0.3
    min_pump_efficiency: float = 0.4


class ObjectiveWeights(BaseModel):
    """Objective function weights - DEMO/PROTOTYPE assumptions."""
    production_weight: float = 1.0
    steam_weight: float = 0.3
    risk_weight: float = 0.5
    operating_weight: float = 0.2


class CandidateScenario(BaseModel):
    """A single evaluated optimization candidate."""
    css_params: CSSParams
    srp_params: SRPParams
    predicted_production_stb_d: float
    predicted_rod_float_risk: float
    predicted_impact_loading_risk: float
    steam_usage_m3_d: float
    steam_intensity: float
    objective_score: float
    is_feasible: bool
    constraint_violations: List[str] = []


class BaselineComparison(BaseModel):
    """Baseline vs optimized comparison."""
    baseline_production_stb_d: float
    optimized_production_stb_d: float
    production_change_pct: float
    baseline_steam_m3_d: float
    optimized_steam_m3_d: float
    steam_change_pct: float
    baseline_rod_float_risk: float
    optimized_rod_float_risk: float
    baseline_impact_loading_risk: float
    optimized_impact_loading_risk: float
    baseline_objective_score: float
    optimized_objective_score: float
    objective_improvement: float


class OptimizationRecommendation(BaseModel):
    """Final optimization recommendation output."""
    well_id: str
    timestamp: datetime
    recommended_css: CSSParams
    recommended_srp: SRPParams
    predicted_production_stb_d: float
    predicted_rod_float_risk: float
    predicted_impact_loading_risk: float
    objective_score: float
    baseline_comparison: BaselineComparison
    constraints_satisfied: List[str]
    explanation: str
    data_source: str = "SYNTHETIC_DEMO"
    disclaimer: str = (
        "Optimization results are prototype recommendations generated from synthetic/demo data "
        "and are not validated against real Baghewala/OIL field operations."
    )


class OptimizationConfig(BaseModel):
    """Full optimization configuration."""
    well_id: str = "BW-001"
    constraints: OptimizationConstraints = OptimizationConstraints()
    weights: ObjectiveWeights = ObjectiveWeights()
    grid_resolution: int = 5
    day_in_cycle: float = 5.0
    cycle_num: int = 1
    wellhead_pressure_kpa: float = 500
    random_seed: int = 42


class OptimizationResult(BaseModel):
    """Complete optimization result."""
    config: OptimizationConfig
    best_candidate: CandidateScenario
    all_candidates: List[CandidateScenario]
    recommendation: OptimizationRecommendation
    total_evaluated: int
    feasible_count: int
    execution_time_seconds: float