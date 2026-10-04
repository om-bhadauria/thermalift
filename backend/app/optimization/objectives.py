"""
Objective function for optimization.
Multi-objective weighted score - DEMO/PROTOTYPE weights.
"""
import numpy as np
from typing import Dict, Any
from app.optimization.schemas import (
    CandidateScenario,
    ObjectiveWeights,
    OptimizationConstraints,
)


class ObjectiveCalculator:
    """
    Calculates multi-objective optimization score.
    
    Score = production_weight * norm_production
          - steam_weight * norm_steam_use
          - risk_weight * norm_risk
          - operating_weight * norm_operating_cost
    
    All weights are DEMO/PROTOTYPE assumptions.
    Normalization uses min-max scaling with synthetic bounds.
    """
    
    # Synthetic normalization bounds (DEMO values)
    PRODUCTION_MIN = 0.0
    PRODUCTION_MAX = 2000.0  # STB/d
    STEAM_MIN = 0.0
    STEAM_MAX = 350.0  # m3/d
    RISK_MIN = 0.0
    RISK_MAX = 1.0
    OPERATING_COST_MIN = 0.0
    OPERATING_COST_MAX = 1000.0  # arbitrary units
    
    def __init__(self, weights: ObjectiveWeights, constraints: OptimizationConstraints):
        self.weights = weights
        self.constraints = constraints
    
    def normalize_production(self, production: float) -> float:
        """Normalize production to [0, 1] using synthetic bounds."""
        return np.clip(
            (production - self.PRODUCTION_MIN) / (self.PRODUCTION_MAX - self.PRODUCTION_MIN),
            0.0, 1.0
        )
    
    def normalize_steam(self, steam_rate: float) -> float:
        """Normalize steam usage to [0, 1]."""
        return np.clip(
            (steam_rate - self.STEAM_MIN) / (self.STEAM_MAX - self.STEAM_MIN),
            0.0, 1.0
        )
    
    def normalize_risk(self, rod_float: float, impact_loading: float) -> float:
        """Normalize combined risk to [0, 1]."""
        combined_risk = max(rod_float, impact_loading)
        return np.clip(
            (combined_risk - self.RISK_MIN) / (self.RISK_MAX - self.RISK_MIN),
            0.0, 1.0
        )
    
    def normalize_operating_cost(
        self,
        steam_rate: float,
        spm: float,
        stroke_length: float
    ) -> float:
        """
        Normalize operating cost proxy.
        Uses steam rate + mechanical energy proxy.
        """
        # Simple proxy: steam thermal energy + mechanical work
        steam_cost = steam_rate * 0.5  # arbitrary scaling
        mechanical_cost = spm * stroke_length * 10  # arbitrary scaling
        total_cost = steam_cost + mechanical_cost
        
        return np.clip(
            (total_cost - self.OPERATING_COST_MIN) / (self.OPERATING_COST_MAX - self.OPERATING_COST_MIN),
            0.0, 1.0
        )
    
    def calculate_score(
        self,
        production: float,
        steam_rate: float,
        rod_float_risk: float,
        impact_loading_risk: float,
        spm: float,
        stroke_length_m: float
    ) -> float:
        """
        Calculate objective score.
        Higher is better.
        """
        norm_prod = self.normalize_production(production)
        norm_steam = self.normalize_steam(steam_rate)
        norm_risk = self.normalize_risk(rod_float_risk, impact_loading_risk)
        norm_operating = self.normalize_operating_cost(steam_rate, spm, stroke_length_m)
        
        score = (
            self.weights.production_weight * norm_prod
            - self.weights.steam_weight * norm_steam
            - self.weights.risk_weight * norm_risk
            - self.weights.operating_weight * norm_operating
        )
        
        return float(score)
    
    def calculate_from_candidate(self, candidate: CandidateScenario) -> float:
        """Calculate score from candidate scenario."""
        return self.calculate_score(
            production=candidate.predicted_production_stb_d,
            steam_rate=candidate.steam_usage_m3_d,
            rod_float_risk=candidate.predicted_rod_float_risk,
            impact_loading_risk=candidate.predicted_impact_loading_risk,
            spm=candidate.srp_params.spm,
            stroke_length_m=candidate.srp_params.stroke_length_m
        )
    
    def get_score_breakdown(
        self,
        production: float,
        steam_rate: float,
        rod_float_risk: float,
        impact_loading_risk: float,
        spm: float,
        stroke_length_m: float
    ) -> Dict[str, float]:
        """Get detailed score component breakdown for explainability."""
        norm_prod = self.normalize_production(production)
        norm_steam = self.normalize_steam(steam_rate)
        norm_risk = self.normalize_risk(rod_float_risk, impact_loading_risk)
        norm_operating = self.normalize_operating_cost(steam_rate, spm, stroke_length_m)
        
        return {
            "normalized_production": norm_prod,
            "normalized_steam_use": norm_steam,
            "normalized_risk": norm_risk,
            "normalized_operating_cost": norm_operating,
            "production_contribution": self.weights.production_weight * norm_prod,
            "steam_penalty": -self.weights.steam_weight * norm_steam,
            "risk_penalty": -self.weights.risk_weight * norm_risk,
            "operating_penalty": -self.weights.operating_weight * norm_operating,
            "total_score": (
                self.weights.production_weight * norm_prod
                - self.weights.steam_weight * norm_steam
                - self.weights.risk_weight * norm_risk
                - self.weights.operating_weight * norm_operating
            )
        }