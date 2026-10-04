import pytest
import numpy as np
from datetime import datetime

from app.models.synthetic import WellConfig, CSSCycle
from app.services.physics_models import (
    ThermalModel,
    ViscosityModel,
    WellboreModel,
    SRPModel,
    PipelineEngine,
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
def css_params():
    return CSSCycle(
        cycle_num=1,
        steam_rate_m3_d=200,
        steam_quality=0.8,
        injection_days=10,
        soak_days=5,
        production_days=90
    )


@pytest.fixture
def srp_params():
    return {
        "spm": 5.0,
        "stroke_length_m": 3.0,
        "vfd_frequency_hz": 40.0
    }



    def test_temperature_prediction_works(self, well_config, css_params):
        model = ThermalModel(well_config)
        temp = model.predict_temperature(cycle_num=1, day_in_cycle=5, css_params=css_params)
        
        assert isinstance(temp, float)
        assert 20 <= temp <= 350

    def test_higher_steam_rate_higher_temperature(self, well_config):
        model = ThermalModel(well_config)
        
        css_low = CSSCycle(cycle_num=1, steam_rate_m3_d=100, steam_quality=0.8,
                           injection_days=10, soak_days=5, production_days=90)
        css_high = CSSCycle(cycle_num=1, steam_rate_m3_d=300, steam_quality=0.8,
                            injection_days=10, soak_days=5, production_days=90)
        
        temp_low = model.predict_temperature(1, 5, css_low)
        temp_high = model.predict_temperature(1, 5, css_high)
        
        assert temp_high > temp_low

    def test_temperature_decays_over_cycles(self, well_config, css_params):
        model = ThermalModel(well_config)
        
        temp_c1 = model.predict_temperature(1, 5, css_params)
        temp_c5 = model.predict_temperature(5, 5, css_params)
        
        assert temp_c1 > temp_c5

    def test_temperature_profile_valid_values(self, well_config, css_params):
        model = ThermalModel(well_config)
        profile = model.predict_temperature_profile([css_params], days=5, freq_hours=6)
        
        assert len(profile) == 5 * 4
        for point in profile:
            assert "timestamp" in point
            assert "cycle_num" in point
            assert "day_in_cycle" in point
            assert "temperature_c" in point
            assert 20 <= point["temperature_c"] <= 350
            assert isinstance(point["cycle_num"], int)
            assert point["cycle_num"] >= 1


class TestViscosityModel:
    def test_viscosity_decreases_with_temperature(self, well_config):
        model = ViscosityModel(well_config)
        
        viscosities = [model.predict_viscosity(t) for t in [60, 100, 140, 180, 220]]
        
        for i in range(len(viscosities) - 1):
            assert viscosities[i] > viscosities[i + 1], \
                f"Viscosity should decrease: {viscosities}"

    def test_viscosity_reasonable_bounds(self, well_config):
        model = ViscosityModel(well_config)
        
        for temp in [40, 80, 120, 160, 200, 250]:
            vis = model.predict_viscosity(temp)
            assert 0.5 <= vis <= 100000, f"Viscosity {vis} out of bounds at {temp}°C"

    def test_viscosity_profile_generation(self, well_config):
        model = ViscosityModel(well_config)
        temperatures = [80, 100, 120, 140, 160]
        viscosities = model.predict_viscosity_profile(temperatures)
        
        assert len(viscosities) == len(temperatures)
        for v in viscosities:
            assert 0.5 <= v <= 100000


class TestWellboreModel:
    def test_bottomhole_pressure_valid(self, well_config):
        model = WellboreModel(well_config)
        
        bhp = model.calculate_bottomhole_pressure(
            wellhead_pressure_kpa=500,
            temperature_c=120,
            viscosity_cp=5000,
            production_rate_stb_d=500
        )
        
        assert isinstance(bhp, float)
        assert bhp > 500
        assert bhp < 50000

    def test_pressure_responds_to_production_rate(self, well_config):
        model = WellboreModel(well_config)
        
        bhp_low = model.calculate_bottomhole_pressure(500, 120, 5000, 100)
        bhp_high = model.calculate_bottomhole_pressure(500, 120, 5000, 1000)
        
        assert bhp_high > bhp_low

    def test_pressure_responds_to_viscosity(self, well_config):
        model = WellboreModel(well_config)
        
        bhp_low_vis = model.calculate_bottomhole_pressure(500, 120, 100, 500)
        bhp_high_vis = model.calculate_bottomhole_pressure(500, 120, 10000, 500)
        
        assert bhp_high_vis > bhp_low_vis

    def test_flow_regime_calculation(self, well_config):
        model = WellboreModel(well_config)
        
        regime = model.calculate_flow_regime(500, 5000)
        assert regime in ["laminar", "transitional", "turbulent"]
        
        regime_low = model.calculate_flow_regime(10, 50000)
        regime_high = model.calculate_flow_regime(10000, 50)
        
        assert regime_low in ["laminar", "transitional"]
        assert regime_high == "turbulent"


class TestSRPModel:
    def test_pump_load_calculation_valid(self, well_config):
        model = SRPModel(well_config)
        
        result = model.calculate_pump_load(
            viscosity_cp=5000,
            spm=5.0,
            stroke_length_m=3.0,
            pump_diameter_mm=75,
            bottomhole_pressure_kpa=5000,
            wellhead_pressure_kpa=500
        )
        
        assert "polished_rod_load_max_kn" in result
        assert "polished_rod_load_min_kn" in result
        assert "fillage" in result
        assert "pump_efficiency" in result
        assert "fluid_load_kn" in result
        assert "theoretical_production_stb_d" in result
        
        assert result["polished_rod_load_max_kn"] > result["polished_rod_load_min_kn"]
        assert result["polished_rod_load_max_kn"] > 0

    def test_fillage_efficiency_bounds(self, well_config):
        model = SRPModel(well_config)
        
        for vis in [100, 1000, 5000, 20000, 50000]:
            result = model.calculate_pump_load(
                viscosity_cp=vis,
                spm=5.0,
                stroke_length_m=3.0,
                pump_diameter_mm=75,
                bottomhole_pressure_kpa=5000,
                wellhead_pressure_kpa=500
            )
            
            assert 0.3 <= result["fillage"] <= 1.0, f"Fillage {result['fillage']} out of bounds at vis={vis}"
            assert 0.0 <= result["pump_efficiency"] <= 1.0, f"Efficiency {result['pump_efficiency']} out of bounds at vis={vis}"

    def test_risk_calculations_bounded(self, well_config):
        model = SRPModel(well_config)
        
        for fillage in [0.3, 0.5, 0.7, 0.9, 1.0]:
            for spm in [2.0, 4.0, 6.0, 8.0]:
                for eff in [0.5, 0.7, 0.9]:
                    risks = model.calculate_risks(
                        fillage=fillage,
                        efficiency=eff,
                        spm=spm,
                        stroke_length_m=3.0,
                        pump_load_max_kn=200,
                        pump_load_min_kn=50
                    )
                    
                    assert 0.0 <= risks["rod_float_risk"] <= 1.0
                    assert 0.0 <= risks["impact_loading_risk"] <= 1.0
                    assert 0.0 <= risks["gas_lock_risk"] <= 1.0

    def test_dynamometer_calculation(self, well_config):
        model = SRPModel(well_config)
        
        pump_load = {
            "polished_rod_load_max_kn": 200,
            "polished_rod_load_min_kn": 50
        }
        
        card = model.calculate_dynamometer_card(
            viscosity_cp=5000,
            spm=5.0,
            stroke_length_m=3.0,
            pump_load=pump_load
        )
        
        assert "load_max_kn" in card
        assert "load_min_kn" in card
        assert "stroke_length_m" in card
        assert "spm" in card
        assert "card_area_kn_m" in card
        assert card["load_max_kn"] == 200
        assert card["load_min_kn"] == 50
        assert card["stroke_length_m"] == 3.0
        assert card["spm"] == 5.0


class TestPipelineEngine:
    def test_run_simulation_completes(self, well_config, css_params, srp_params):
        engine = PipelineEngine(well_config)
        state = engine.run_simulation(css_params, srp_params, day_in_cycle=5, cycle_num=1)
        
        assert state is not None
        assert state.well_id == "BW-001"
        assert state.data_source == "SYNTHETIC"

    def test_returned_state_contains_expected_fields(self, well_config, css_params, srp_params):
        engine = PipelineEngine(well_config)
        state = engine.run_simulation(css_params, srp_params, day_in_cycle=5, cycle_num=1)
        
        required_fields = [
            "well_id", "timestamp", "temperature_c", "viscosity_cp",
            "production_rate_stb_d", "steam_rate_m3_d", "steam_pressure_kpa",
            "css_cycle", "srp_spm", "stroke_length_m", "pump_load_kn",
            "fillage", "pump_efficiency", "vfd_frequency_hz",
            "rod_float_risk", "impact_loading_risk", "data_source"
        ]
        
        for field in required_fields:
            assert hasattr(state, field), f"Missing field: {field}"

    def test_temperature_viscosity_relationship_preserved(self, well_config, css_params, srp_params):
        engine = PipelineEngine(well_config)
        
        css_cold = CSSCycle(cycle_num=1, steam_rate_m3_d=100, steam_quality=0.8,
                            injection_days=10, soak_days=5, production_days=90)
        css_hot = CSSCycle(cycle_num=1, steam_rate_m3_d=300, steam_quality=0.8,
                           injection_days=10, soak_days=5, production_days=90)
        
        state_cold = engine.run_simulation(css_cold, srp_params, day_in_cycle=5, cycle_num=1)
        state_hot = engine.run_simulation(css_hot, srp_params, day_in_cycle=5, cycle_num=1)
        
        assert state_hot.temperature_c > state_cold.temperature_c
        assert state_cold.viscosity_cp > state_hot.viscosity_cp

    def test_production_non_negative(self, well_config, css_params, srp_params):
        engine = PipelineEngine(well_config)
        
        for day in [0, 5, 15, 50, 100]:
            css = CSSCycle(cycle_num=1, steam_rate_m3_d=200, steam_quality=0.8,
                           injection_days=10, soak_days=5, production_days=90)
            state = engine.run_simulation(css, srp_params, day_in_cycle=day, cycle_num=1)
            assert state.production_rate_stb_d >= 0

    def test_fillage_efficiency_risk_bounded(self, well_config, css_params, srp_params):
        engine = PipelineEngine(well_config)
        state = engine.run_simulation(css_params, srp_params, day_in_cycle=5, cycle_num=1)
        
        assert 0.0 <= state.fillage <= 1.0
        assert 0.0 <= state.pump_efficiency <= 1.0
        assert 0.0 <= state.rod_float_risk <= 1.0
        assert 0.0 <= state.impact_loading_risk <= 1.0

    def test_run_scenario_works(self, well_config, css_params, srp_params):
        engine = PipelineEngine(well_config)
        states = engine.run_scenario(css_params, srp_params, days=5)
        
        assert len(states) == 5
        for state in states:
            assert state.well_id == "BW-001"
            assert state.data_source == "SYNTHETIC"
            assert state.production_rate_stb_d >= 0


class TestCausalChainIntegration:
    def test_full_causal_chain_css_to_risk(self, well_config, srp_params):
        engine = PipelineEngine(well_config)
        
        css_low_steam = CSSCycle(cycle_num=1, steam_rate_m3_d=100, steam_quality=0.7,
                                 injection_days=10, soak_days=5, production_days=90)
        css_high_steam = CSSCycle(cycle_num=1, steam_rate_m3_d=300, steam_quality=0.85,
                                  injection_days=10, soak_days=5, production_days=90)
        
        state_low = engine.run_simulation(css_low_steam, srp_params, day_in_cycle=5, cycle_num=1)
        state_high = engine.run_simulation(css_high_steam, srp_params, day_in_cycle=5, cycle_num=1)
        
        assert state_high.temperature_c > state_low.temperature_c
        assert state_low.viscosity_cp > state_high.viscosity_cp
        assert state_high.production_rate_stb_d >= state_low.production_rate_stb_d
        
        assert 0.0 <= state_low.rod_float_risk <= 1.0
        assert 0.0 <= state_high.rod_float_risk <= 1.0
        assert 0.0 <= state_low.impact_loading_risk <= 1.0
        assert 0.0 <= state_high.impact_loading_risk <= 1.0

    def test_cycle_decay_affects_entire_chain(self, well_config, srp_params):
        engine = PipelineEngine(well_config)
        css = CSSCycle(cycle_num=1, steam_rate_m3_d=200, steam_quality=0.8,
                       injection_days=10, soak_days=5, production_days=90)
        
        state_c1 = engine.run_simulation(css, srp_params, day_in_cycle=5, cycle_num=1)
        state_c5 = engine.run_simulation(css, srp_params, day_in_cycle=5, cycle_num=5)
        
        assert state_c1.temperature_c > state_c5.temperature_c
        assert state_c1.viscosity_cp < state_c5.viscosity_cp
        assert state_c1.production_rate_stb_d >= state_c5.production_rate_stb_d

    def test_srp_params_affect_pump_load_and_risk(self, well_config, css_params):
        engine = PipelineEngine(well_config)
        
        srp_low = {"spm": 3.0, "stroke_length_m": 2.5, "vfd_frequency_hz": 30}
        srp_high = {"spm": 7.0, "stroke_length_m": 3.5, "vfd_frequency_hz": 50}
        
        state_low = engine.run_simulation(css_params, srp_low, day_in_cycle=5, cycle_num=1)
        state_high = engine.run_simulation(css_params, srp_high, day_in_cycle=5, cycle_num=1)
        
        assert state_high.pump_load_kn >= state_low.pump_load_kn
        assert state_high.impact_loading_risk >= state_low.impact_loading_risk