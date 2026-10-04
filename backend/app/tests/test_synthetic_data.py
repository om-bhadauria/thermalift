import pytest
import numpy as np
import pandas as pd
from datetime import datetime

from app.data.synthetic_data import SyntheticDataGenerator, DEFAULT_WELL_CONFIGS
from app.data.validation import SyntheticDataValidator, check_causal_relationships
from app.models.synthetic import WellConfig, WellState, viscosity_from_temperature, temperature_from_css_cycle


class TestViscosityModel:
    def test_viscosity_decreases_with_temperature(self):
        oil_api = 12.0
        viscosities = [viscosity_from_temperature(t, oil_api) for t in [60, 100, 140, 180, 220]]
        for i in range(len(viscosities) - 1):
            assert viscosities[i] > viscosities[i + 1], f"Viscosity should decrease with temperature: {viscosities}"

    def test_viscosity_heavier_oil_higher(self):
        vis_10 = viscosity_from_temperature(100, 10.0)
        vis_15 = viscosity_from_temperature(100, 15.0)
        assert vis_10 > vis_15, "Heavier oil (lower API) should have higher viscosity"

    def test_viscosity_reasonable_range(self):
        for api in [8, 10, 12, 15, 20]:
            for temp in [60, 100, 140, 180, 220]:
                vis = viscosity_from_temperature(temp, api)
                assert 0.1 < vis <= 100000, f"Viscosity out of range: {vis} at {temp}°C, {api}°API"


class TestTemperatureModel:
    def test_temperature_rises_during_injection(self):
        base = 90
        temp_inj = temperature_from_css_cycle(base, 1, 5, 10, 5, 90, 200, 0.8)
        temp_prod = temperature_from_css_cycle(base, 1, 50, 10, 5, 90, 200, 0.8)
        assert temp_inj > temp_prod, "Temperature should be higher during injection than late production"

    def test_temperature_decays_over_cycles(self):
        temp_c1 = temperature_from_css_cycle(90, 1, 5, 10, 5, 90, 200, 0.8)
        temp_c5 = temperature_from_css_cycle(90, 5, 5, 10, 5, 90, 200, 0.8)
        assert temp_c1 > temp_c5, "Temperature response should decay over cycles"

    def test_higher_steam_rate_higher_temp(self):
        temp_low = temperature_from_css_cycle(90, 1, 5, 10, 5, 90, 100, 0.8)
        temp_high = temperature_from_css_cycle(90, 1, 5, 10, 5, 90, 300, 0.8)
        assert temp_high > temp_low, "Higher steam rate should give higher temperature"


class TestSyntheticDataGenerator:
    @pytest.fixture
    def generator(self):
        return SyntheticDataGenerator(seed=42)

    def test_well_configs_loaded(self, generator):
        assert len(generator.well_configs) == 5
        for well_id in ["BW-001", "BW-002", "BW-003", "BW-004", "BW-005"]:
            assert well_id in generator.well_configs

    def test_generate_css_history(self, generator):
        cycles = generator.generate_css_history("BW-001", n_cycles=4)
        assert len(cycles) == 4
        for i, c in enumerate(cycles):
            assert c.cycle_num == i + 1
            assert c.steam_rate_m3_d > 0
            assert 0.6 <= c.steam_quality <= 0.9
            assert c.injection_days > 0
            assert c.soak_days >= 0
            assert c.production_days > 0
            assert c.data_source == "SYNTHETIC"

    def test_generate_srp_history(self, generator):
        readings = generator.generate_srp_history("BW-001", n_days=30)
        assert len(readings) == 30
        for r in readings:
            assert 2.0 <= r.spm <= 8.0
            assert 0.5 <= r.fillage <= 1.0
            assert 0.8 <= r.pump_efficiency <= 1.0
            assert r.polished_rod_load_max_kn > r.polished_rod_load_min_kn
            assert r.data_source == "SYNTHETIC"

    def test_generate_well_states(self, generator):
        states = generator.generate_well_states("BW-001", n_days=7, freq_hours=6)
        assert len(states) == 7 * 4
        for s in states:
            assert s.well_id == "BW-001"
            assert s.data_source == "SYNTHETIC"
            assert 20 <= s.temperature_c <= 350
            assert 0.1 <= s.viscosity_cp <= 100000
            assert 0 <= s.production_rate_stb_d <= 5000
            assert 0 <= s.rod_float_risk <= 1.0
            assert 0 <= s.impact_loading_risk <= 1.0

    def test_deterministic_generation(self, generator):
        states1 = generator.generate_well_states("BW-001", n_days=5, freq_hours=12)
        gen2 = SyntheticDataGenerator(seed=42)
        states2 = gen2.generate_well_states("BW-001", n_days=5, freq_hours=12)

        for s1, s2 in zip(states1, states2):
            assert s1.temperature_c == s2.temperature_c
            assert s1.viscosity_cp == s2.viscosity_cp
            assert s1.production_rate_stb_d == s2.production_rate_stb_d
            assert s1.pump_load_kn == s2.pump_load_kn

    def test_different_wells_different_data(self, generator):
        states_001 = generator.generate_well_states("BW-001", n_days=10, freq_hours=24)
        states_002 = generator.generate_well_states("BW-002", n_days=10, freq_hours=24)

        temps_001 = [s.temperature_c for s in states_001]
        temps_002 = [s.temperature_c for s in states_002]
        assert temps_001 != temps_002

    def test_generate_all_wells(self, generator):
        all_states = generator.generate_all_wells(n_days=5, freq_hours=12)
        assert len(all_states) == 5
        for well_id, states in all_states.items():
            assert len(states) == 5 * 2
            for s in states:
                assert s.well_id == well_id

    def test_to_dataframe(self, generator):
        states = generator.generate_well_states("BW-001", n_days=3, freq_hours=12)
        df = generator.to_dataframe(states)
        assert len(df) == len(states)
        assert "well_id" in df.columns
        assert "temperature_c" in df.columns
        assert "viscosity_cp" in df.columns
        assert all(df["data_source"] == "SYNTHETIC")


class TestValidation:
    @pytest.fixture
    def generator(self):
        return SyntheticDataGenerator(seed=42)

    @pytest.fixture
    def states(self, generator):
        return generator.generate_well_states("BW-001", n_days=30, freq_hours=6)

    @pytest.fixture
    def config(self):
        return DEFAULT_WELL_CONFIGS[0]

    def test_all_states_pass_validation(self, states, config):
        validator = SyntheticDataValidator()
        for s in states:
            assert validator.validate_well_state(s, config), f"Validation failed: {validator.errors}"

    def test_dataset_validation(self, states, config):
        ok, errors, warnings = SyntheticDataValidator().validate_dataset(states, {"BW-001": config})
        assert ok, f"Dataset validation errors: {errors}"
        print(f"Warnings: {len(warnings)}")

    def test_synthetic_label_enforced(self):
        with pytest.raises(ValueError):
            WellState(
                well_id="BW-001",
                timestamp=datetime.now(),
                temperature_c=100,
                viscosity_cp=1000,
                production_rate_stb_d=100,
                steam_rate_m3_d=0,
                steam_pressure_kpa=0,
                css_cycle=1,
                srp_spm=5,
                stroke_length_m=3,
                pump_load_kn=100,
                fillage=0.9,
                pump_efficiency=0.85,
                vfd_frequency_hz=40,
                rod_float_risk=0.1,
                impact_loading_risk=0.1,
                data_source="REAL"
            )

    def test_causal_relationships(self, states):
        df = pd.DataFrame([s.model_dump() for s in states])
        results = check_causal_relationships(df)

        for key, val in results.items():
            if "correlation" in key and isinstance(val, float):
                assert not np.isnan(val), f"{key} is NaN"

        assert results["temp_viscosity_expected_negative"], \
            f"Temp-viscosity correlation should be negative: {results['temp_viscosity_correlation']}"
        assert results["viscosity_load_expected_positive"], \
            f"Viscosity-load correlation should be positive: {results['viscosity_load_correlation']}"
        assert results["temp_production_expected_positive"], \
            f"Temp-production correlation should be positive: {results['temp_production_correlation']}"
        assert results["spm_impact_risk_expected_positive"], \
            f"SPM-impact risk correlation should be positive: {results['spm_impact_risk_correlation']}"
        assert results["fillage_efficiency_expected_positive"], \
            f"Fillage-efficiency correlation should be positive: {results['fillage_efficiency_correlation']}"
        assert results["steam_heating_expected_positive"], \
            f"Steam heating effect should be positive: {results['steam_heating_effect']}"

    def test_no_nan_values(self, states):
        df = pd.DataFrame([s.model_dump() for s in states])
        assert not df.isnull().any().any(), "Dataset contains NaN values"

    def test_all_wells_valid(self, generator):
        all_states = generator.generate_all_wells(n_days=10, freq_hours=12)
        for well_id, states in all_states.items():
            config = generator.get_well_config(well_id)
            validator = SyntheticDataValidator()
            for s in states:
                assert validator.validate_well_state(s, config), f"{well_id}: {validator.errors}"


class TestWellConfigValidation:
    def test_valid_config(self):
        config = WellConfig(
            well_id="BW-999",
            depth_m=1000,
            reservoir_temp_initial_c=100,
            oil_api=12,
            pay_thickness_m=20,
            permeability_md=1000,
            pump_intake_depth_m=900,
            tubing_id_inches=2.875,
            rod_diameter_inches=0.875,
            stroke_length_m=3.0,
            pump_diameter_mm=75
        )
        assert config.well_id == "BW-999"

    def test_invalid_well_id_pattern(self):
        with pytest.raises(ValueError):
            WellConfig(
                well_id="INVALID",
                depth_m=1000,
                reservoir_temp_initial_c=100,
                oil_api=12,
                pay_thickness_m=20,
                permeability_md=1000,
                pump_intake_depth_m=900,
                tubing_id_inches=2.875,
                rod_diameter_inches=0.875,
                stroke_length_m=3.0,
                pump_diameter_mm=75
            )

    def test_pump_depth_validation(self):
        with pytest.raises(ValueError):
            WellConfig(
                well_id="BW-999",
                depth_m=1000,
                reservoir_temp_initial_c=100,
                oil_api=12,
                pay_thickness_m=20,
                permeability_md=1000,
                pump_intake_depth_m=1000,
                tubing_id_inches=2.875,
                rod_diameter_inches=0.875,
                stroke_length_m=3.0,
                pump_diameter_mm=75
            )


class TestDataQuality:
    @pytest.fixture
    def generator(self):
        return SyntheticDataGenerator(seed=42)

    def test_temperature_range_realistic(self, generator):
        states = generator.generate_well_states("BW-001", n_days=60, freq_hours=6)
        temps = [s.temperature_c for s in states]
        assert min(temps) >= 30
        assert max(temps) <= 300
        assert np.mean(temps) > 80

    def test_viscosity_range_realistic(self, generator):
        states = generator.generate_well_states("BW-001", n_days=60, freq_hours=6)
        viscs = [s.viscosity_cp for s in states]
        assert min(viscs) >= 1
        assert max(viscs) <= 100000

    def test_production_rate_non_negative(self, generator):
        states = generator.generate_well_states("BW-001", n_days=60, freq_hours=6)
        rates = [s.production_rate_stb_d for s in states]
        assert all(r >= 0 for r in rates)

    def test_risk_scores_bounded(self, generator):
        states = generator.generate_well_states("BW-001", n_days=60, freq_hours=6)
        for s in states:
            assert 0 <= s.rod_float_risk <= 1
            assert 0 <= s.impact_loading_risk <= 1

    def test_fillage_efficiency_bounded(self, generator):
        states = generator.generate_well_states("BW-001", n_days=60, freq_hours=6)
        for s in states:
            assert 0 <= s.fillage <= 1
            assert 0 <= s.pump_efficiency <= 1