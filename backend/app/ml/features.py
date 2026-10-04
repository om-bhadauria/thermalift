"""
Feature engineering for ML models.
Builds features from synthetic dataset for production forecasting and risk prediction.
"""
from typing import List, Tuple, Dict, Any
import numpy as np
import pandas as pd
from datetime import datetime

from app.data.synthetic_data import SyntheticDataGenerator, DEFAULT_WELL_CONFIGS
from app.models.synthetic import WellState


class FeatureBuilder:
    """Builds ML features from well state data."""
    
    # Features available for both models
    BASE_FEATURES = [
        "temperature_c",
        "viscosity_cp",
        "steam_rate_m3_d",
        "steam_pressure_kpa",
        "css_cycle",
        "srp_spm",
        "stroke_length_m",
        "pump_load_kn",
        "fillage",
        "pump_efficiency",
        "vfd_frequency_hz",
    ]
    
    # Production model features (excludes target)
    PRODUCTION_FEATURES = BASE_FEATURES.copy()
    
    # Risk model features (excludes risk targets)
    RISK_FEATURES = BASE_FEATURES.copy()
    
    def __init__(self, add_derived: bool = True):
        self.add_derived = add_derived
    
    def build_features(self, states: List[WellState]) -> pd.DataFrame:
        """Convert WellState list to feature DataFrame."""
        records = [s.model_dump() for s in states]
        df = pd.DataFrame(records)
        
        if self.add_derived:
            df = self._add_derived_features(df)
        
        return df
    
    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add physics-informed derived features."""
        df = df.copy()
        
        # Temperature-viscosity interaction
        df["temp_visc_ratio"] = df["temperature_c"] / (df["viscosity_cp"] + 1)
        
        # Steam thermal power proxy
        df["steam_thermal_power"] = df["steam_rate_m3_d"] * df["steam_pressure_kpa"] / 1000
        
        # Pump hydraulic power proxy
        df["pump_hydraulic_power"] = df["pump_load_kn"] * df["srp_spm"] * df["stroke_length_m"]
        
        # Efficiency-weighted SPM
        df["effective_spm"] = df["srp_spm"] * df["pump_efficiency"]
        
        # Viscosity-normalized load
        df["load_per_viscosity"] = df["pump_load_kn"] / (df["viscosity_cp"] / 1000 + 1)
        
        # Cycle phase encoding (0=injection, 1=soak, 2=production)
        df["cycle_phase"] = np.where(
            df["steam_rate_m3_d"] > 0, 0,
            np.where(df["css_cycle"] > 0, 2, 1)
        )
        
        # Days since cycle start (approximate)
        df["days_in_cycle"] = df.groupby("css_cycle").cumcount() if "css_cycle" in df.columns else 0
        
        # Well-specific static features (from config)
        well_static = {
            "BW-001": {"depth_m": 950, "oil_api": 12.5, "perm_md": 1200, "pay_m": 18},
            "BW-002": {"depth_m": 1100, "oil_api": 11.0, "perm_md": 800, "pay_m": 22},
            "BW-003": {"depth_m": 850, "oil_api": 14.0, "perm_md": 1500, "pay_m": 15},
            "BW-004": {"depth_m": 1200, "oil_api": 10.5, "perm_md": 600, "pay_m": 25},
            "BW-005": {"depth_m": 900, "oil_api": 13.0, "perm_md": 1000, "pay_m": 20},
        }
        
        for well_id, static in well_static.items():
            mask = df["well_id"] == well_id
            for key, val in static.items():
                df.loc[mask, f"well_{key}"] = val
        
        return df
    
    def get_inference_features(self, df: pd.DataFrame, model_type: str = "production") -> pd.DataFrame:
        """
        Extract features for inference (no target columns required).
        
        Args:
            df: Input DataFrame with base features
            model_type: "production" or "risk"
            
        Returns:
            DataFrame with only feature columns (no target columns)
        """
        # Add derived features if enabled
        if self.add_derived:
            df = self._add_derived_features(df)
        
        if model_type == "production":
            feature_cols = [c for c in self.PRODUCTION_FEATURES if c in df.columns]
        elif model_type == "risk":
            feature_cols = [c for c in self.RISK_FEATURES if c in df.columns]
        else:
            raise ValueError(f"Unsupported model_type: {model_type}")
        
        # Add derived features if they exist (avoid duplicates)
        derived_cols = [c for c in df.columns if c.startswith(("temp_", "steam_", "pump_", "effective_", "load_", "cycle_", "days_", "well_"))]
        for c in derived_cols:
            if c not in feature_cols:
                feature_cols.append(c)
        
        # Remove ALL target columns to prevent leakage
        target_cols = ["production_rate_stb_d", "rod_float_risk", "impact_loading_risk", "gas_lock_risk"]
        feature_cols = [c for c in feature_cols if c not in target_cols]
        
        X = df[feature_cols].copy()
        
        # Handle any missing values - only for numeric columns
        X = X.select_dtypes(include=[np.number])
        X = X.fillna(X.median())
        
        return X
    
    def get_production_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Extract features and target for production forecasting."""
        # Add derived features if enabled
        if self.add_derived:
            df = self._add_derived_features(df)
        
        # Ensure no target leakage
        feature_cols = [c for c in self.PRODUCTION_FEATURES if c in df.columns]
        
        # Add derived features if they exist (avoid duplicates)
        derived_cols = [c for c in df.columns if c.startswith(("temp_", "steam_", "pump_", "effective_", "load_", "cycle_", "days_", "well_"))]
        for c in derived_cols:
            if c not in feature_cols:
                feature_cols.append(c)
        
        # Remove target if accidentally present
        feature_cols = [c for c in feature_cols if c not in ["production_rate_stb_d", "rod_float_risk", "impact_loading_risk", "gas_lock_risk"]]
        
        X = df[feature_cols].copy()
        y = df["production_rate_stb_d"].copy()
        
        # Handle any missing values - only for numeric columns
        X = X.select_dtypes(include=[np.number])
        X = X.fillna(X.median())
        
        return X, y
    
    def get_risk_features(self, df: pd.DataFrame, risk_target: str = "rod_float_risk") -> Tuple[pd.DataFrame, pd.Series]:
        """Extract features and target for risk prediction."""
        if risk_target not in ["rod_float_risk", "impact_loading_risk"]:
            raise ValueError(f"Unsupported risk target: {risk_target}")
        
        # Add derived features if enabled
        if self.add_derived:
            df = self._add_derived_features(df)
        
        feature_cols = [c for c in self.RISK_FEATURES if c in df.columns]
        
        # Add derived features (avoid duplicates)
        derived_cols = [c for c in df.columns if c.startswith(("temp_", "steam_", "pump_", "effective_", "load_", "cycle_", "days_", "well_"))]
        for c in derived_cols:
            if c not in feature_cols:
                feature_cols.append(c)
        
        # Remove ALL risk targets to prevent leakage
        risk_targets = ["rod_float_risk", "impact_loading_risk", "gas_lock_risk"]
        feature_cols = [c for c in feature_cols if c not in risk_targets + ["production_rate_stb_d"]]
        
        X = df[feature_cols].copy()
        y = df[risk_target].copy()
        
        # Handle any missing values - only for numeric columns
        X = X.select_dtypes(include=[np.number])
        X = X.fillna(X.median())
        
        return X, y


def generate_training_data(
    n_days: int = 180,
    freq_hours: int = 6,
    seed: int = 42
) -> pd.DataFrame:
    """Generate synthetic dataset for ML training."""
    generator = SyntheticDataGenerator(seed=seed)
    all_states = generator.generate_all_wells(n_days=n_days, freq_hours=freq_hours)
    
    all_records = []
    for well_id, states in all_states.items():
        for s in states:
            all_records.append(s.model_dump())
    
    df = pd.DataFrame(all_records)
    return df


def split_train_test(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
    group_by: str = "well_id"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split data ensuring no well appears in both train and test (prevents leakage)."""
    from sklearn.model_selection import GroupShuffleSplit
    
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    groups = df[group_by]
    
    train_idx, test_idx = next(gss.split(df, groups=groups))
    
    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)
    
    return train_df, test_df