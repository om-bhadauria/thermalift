from typing import List, Tuple, Dict, Any
from app.models.synthetic import WellState, WellConfig
import numpy as np
import pandas as pd


class SyntheticDataValidator:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_well_state(self, state: WellState, config: WellConfig = None) -> bool:
        self.errors = []
        self.warnings = []

        self._check_bounds(state)
        self._check_physics_consistency(state, config)
        self._check_synthetic_label(state)

        return len(self.errors) == 0

    def validate_dataset(self, states: List[WellState], configs: Dict[str, WellConfig] = None) -> Tuple[bool, List[str], List[str]]:
        all_errors = []
        all_warnings = []

        for i, state in enumerate(states):
            self.validate_well_state(state, configs.get(state.well_id) if configs else None)
            for e in self.errors:
                all_errors.append(f"Row {i} ({state.well_id} @ {state.timestamp}): {e}")
            for w in self.warnings:
                all_warnings.append(f"Row {i} ({state.well_id} @ {state.timestamp}): {w}")

        return len(all_errors) == 0, all_errors, all_warnings

    def _check_bounds(self, state: WellState) -> None:
        bounds = {
            "temperature_c": (20, 350),
            "viscosity_cp": (0.1, 100000),
            "production_rate_stb_d": (0, 5000),
            "steam_rate_m3_d": (0, 500),
            "steam_pressure_kpa": (0, 10000),
            "css_cycle": (0, 20),
            "srp_spm": (0, 30),
            "stroke_length_m": (0.5, 5.0),
            "pump_load_kn": (0, 500),
            "fillage": (0.0, 1.0),
            "pump_efficiency": (0.0, 1.0),
            "vfd_frequency_hz": (0, 60),
            "rod_float_risk": (0.0, 1.0),
            "impact_loading_risk": (0.0, 1.0),
        }

        for field, (min_v, max_v) in bounds.items():
            val = getattr(state, field)
            if not (min_v <= val <= max_v):
                self.errors.append(f"{field}={val} out of bounds [{min_v}, {max_v}]")

    def _check_physics_consistency(self, state: WellState, config: WellConfig = None) -> None:
        if state.temperature_c > 250 and state.viscosity_cp > 1000:
            self.warnings.append(
                f"High temp ({state.temperature_c:.1f}°C) but high viscosity ({state.viscosity_cp:.1f} cP) - "
                "viscosity should decrease with temperature"
            )

        if state.temperature_c < 60 and state.viscosity_cp < 100:
            self.warnings.append(
                f"Low temp ({state.temperature_c:.1f}°C) but low viscosity ({state.viscosity_cp:.1f} cP) - "
                "heavy oil should be viscous at low temp"
            )

        if state.steam_rate_m3_d == 0 and state.steam_pressure_kpa > 100:
            self.warnings.append(
                f"Steam rate is 0 but steam_pressure_kpa={state.steam_pressure_kpa:.1f}"
            )

        if state.steam_rate_m3_d > 0 and state.steam_pressure_kpa < 500:
            self.warnings.append(
                f"Steam injection active but low pressure: {state.steam_pressure_kpa:.1f} kPa"
            )

        if state.pump_load_kn < 20 and state.srp_spm > 2:
            self.warnings.append(
                f"Very low pump load ({state.pump_load_kn:.1f} kN) at SPM={state.srp_spm:.1f}"
            )

        if state.fillage > 0.95 and state.pump_efficiency < 0.7:
            self.warnings.append(
                f"High fillage ({state.fillage:.3f}) but low efficiency ({state.pump_efficiency:.3f})"
            )

        if state.rod_float_risk > 0.7 and state.fillage > 0.8:
            self.warnings.append(
                f"High rod float risk ({state.rod_float_risk:.3f}) with good fillage ({state.fillage:.3f})"
            )

        if state.impact_loading_risk > 0.7 and state.srp_spm < 4:
            self.warnings.append(
                f"High impact risk ({state.impact_loading_risk:.3f}) at low SPM ({state.srp_spm:.1f})"
            )

        if config:
            if state.stroke_length_m > config.stroke_length_m * 1.2:
                self.warnings.append(
                    f"Stroke length {state.stroke_length_m:.2f}m exceeds configured {config.stroke_length_m:.2f}m by >20%"
                )

    def _check_synthetic_label(self, state: WellState) -> None:
        if state.data_source != "SYNTHETIC":
            self.errors.append(f"data_source must be 'SYNTHETIC', got '{state.data_source}'")


def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
    from app.models.synthetic import WellState
    validator = SyntheticDataValidator()
    states = [WellState(**row) for _, row in df.iterrows()]
    return validator.validate_dataset(states)


def check_causal_relationships(df: pd.DataFrame) -> Dict[str, Any]:
    results = {}

    temp_visc_corr = df["temperature_c"].corr(df["viscosity_cp"])
    results["temp_viscosity_correlation"] = round(temp_visc_corr, 4)
    results["temp_viscosity_expected_negative"] = temp_visc_corr < -0.3

    visc_load_corr = df["viscosity_cp"].corr(df["pump_load_kn"])
    results["viscosity_load_correlation"] = round(visc_load_corr, 4)
    results["viscosity_load_expected_positive"] = visc_load_corr > 0.3

    temp_prod_corr = df["temperature_c"].corr(df["production_rate_stb_d"])
    results["temp_production_correlation"] = round(temp_prod_corr, 4)
    results["temp_production_expected_positive"] = temp_prod_corr > 0.1

    spm_risk_corr = df["srp_spm"].corr(df["impact_loading_risk"])
    results["spm_impact_risk_correlation"] = round(spm_risk_corr, 4)
    results["spm_impact_risk_expected_positive"] = spm_risk_corr > 0.2

    fillage_eff_corr = df["fillage"].corr(df["pump_efficiency"])
    results["fillage_efficiency_correlation"] = round(fillage_eff_corr, 4)
    results["fillage_efficiency_expected_positive"] = fillage_eff_corr > 0.5

    steam_temp_corr = df[df["steam_rate_m3_d"] > 0]["temperature_c"].mean() - df[df["steam_rate_m3_d"] == 0]["temperature_c"].mean()
    results["steam_heating_effect"] = round(steam_temp_corr, 1)
    results["steam_heating_expected_positive"] = steam_temp_corr > 5

    return results