"""
Constraint validation for optimization candidates.
All constraints use DEMO/SYNTHETIC bounds - NOT actual field limits.
"""
from typing import List
from app.optimization.schemas import (
    CSSParams,
    SRPParams,
    OptimizationConstraints,
    CandidateScenario,
)


def validate_css_params(css: CSSParams, constraints: OptimizationConstraints) -> List[str]:
    """Validate CSS parameters against constraints. Returns list of violations."""
    violations = []
    
    if css.steam_rate_m3_d < constraints.steam_rate_min:
        violations.append(f"steam_rate_m3_d {css.steam_rate_m3_d} < min {constraints.steam_rate_min}")
    if css.steam_rate_m3_d > constraints.steam_rate_max:
        violations.append(f"steam_rate_m3_d {css.steam_rate_m3_d} > max {constraints.steam_rate_max}")
    
    if css.steam_quality < constraints.steam_quality_min:
        violations.append(f"steam_quality {css.steam_quality} < min {constraints.steam_quality_min}")
    if css.steam_quality > constraints.steam_quality_max:
        violations.append(f"steam_quality {css.steam_quality} > max {constraints.steam_quality_max}")
    
    if css.injection_days < constraints.injection_days_min:
        violations.append(f"injection_days {css.injection_days} < min {constraints.injection_days_min}")
    if css.injection_days > constraints.injection_days_max:
        violations.append(f"injection_days {css.injection_days} > max {constraints.injection_days_max}")
    
    if css.soak_days < constraints.soak_days_min:
        violations.append(f"soak_days {css.soak_days} < min {constraints.soak_days_min}")
    if css.soak_days > constraints.soak_days_max:
        violations.append(f"soak_days {css.soak_days} > max {constraints.soak_days_max}")
    
    if css.production_days < constraints.production_days_min:
        violations.append(f"production_days {css.production_days} < min {constraints.production_days_min}")
    if css.production_days > constraints.production_days_max:
        violations.append(f"production_days {css.production_days} > max {constraints.production_days_max}")
    
    return violations


def validate_srp_params(srp: SRPParams, constraints: OptimizationConstraints) -> List[str]:
    """Validate SRP parameters against constraints. Returns list of violations."""
    violations = []
    
    if srp.spm < constraints.spm_min:
        violations.append(f"spm {srp.spm} < min {constraints.spm_min}")
    if srp.spm > constraints.spm_max:
        violations.append(f"spm {srp.spm} > max {constraints.spm_max}")
    
    if srp.stroke_length_m < constraints.stroke_length_min:
        violations.append(f"stroke_length_m {srp.stroke_length_m} < min {constraints.stroke_length_min}")
    if srp.stroke_length_m > constraints.stroke_length_max:
        violations.append(f"stroke_length_m {srp.stroke_length_m} > max {constraints.stroke_length_max}")
    
    if srp.vfd_frequency_hz < constraints.vfd_frequency_min:
        violations.append(f"vfd_frequency_hz {srp.vfd_frequency_hz} < min {constraints.vfd_frequency_min}")
    if srp.vfd_frequency_hz > constraints.vfd_frequency_max:
        violations.append(f"vfd_frequency_hz {srp.vfd_frequency_hz} > max {constraints.vfd_frequency_max}")
    
    return violations


def validate_simulation_outputs(
    production_stb_d: float,
    rod_float_risk: float,
    impact_loading_risk: float,
    fillage: float,
    pump_efficiency: float,
    constraints: OptimizationConstraints
) -> List[str]:
    """Validate simulation outputs against constraints. Returns list of violations."""
    violations = []
    
    if production_stb_d < constraints.min_production_stb_d:
        violations.append(f"production {production_stb_d} < min {constraints.min_production_stb_d}")
    
    if rod_float_risk > constraints.max_rod_float_risk:
        violations.append(f"rod_float_risk {rod_float_risk} > max {constraints.max_rod_float_risk}")
    if rod_float_risk < 0.0 or rod_float_risk > 1.0:
        violations.append(f"rod_float_risk {rod_float_risk} not in [0, 1]")
    
    if impact_loading_risk > constraints.max_impact_loading_risk:
        violations.append(f"impact_loading_risk {impact_loading_risk} > max {constraints.max_impact_loading_risk}")
    if impact_loading_risk < 0.0 or impact_loading_risk > 1.0:
        violations.append(f"impact_loading_risk {impact_loading_risk} not in [0, 1]")
    
    if fillage < constraints.min_fill_age:
        violations.append(f"fillage {fillage} < min {constraints.min_fill_age}")
    if fillage < 0.0 or fillage > 1.0:
        violations.append(f"fillage {fillage} not in [0, 1]")
    
    if pump_efficiency < constraints.min_pump_efficiency:
        violations.append(f"pump_efficiency {pump_efficiency} < min {constraints.min_pump_efficiency}")
    if pump_efficiency < 0.0 or pump_efficiency > 1.0:
        violations.append(f"pump_efficiency {pump_efficiency} not in [0, 1]")
    
    return violations


def check_all_constraints(
    css: CSSParams,
    srp: SRPParams,
    production_stb_d: float,
    rod_float_risk: float,
    impact_loading_risk: float,
    fillage: float,
    pump_efficiency: float,
    constraints: OptimizationConstraints
) -> List[str]:
    """Check all constraints for a candidate scenario."""
    violations = []
    violations.extend(validate_css_params(css, constraints))
    violations.extend(validate_srp_params(srp, constraints))
    violations.extend(validate_simulation_outputs(
        production_stb_d, rod_float_risk, impact_loading_risk,
        fillage, pump_efficiency, constraints
    ))
    return violations


def is_feasible(candidate: CandidateScenario) -> bool:
    """Check if candidate is feasible (no constraint violations)."""
    return candidate.is_feasible and len(candidate.constraint_violations) == 0