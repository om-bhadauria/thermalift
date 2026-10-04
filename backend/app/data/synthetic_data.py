from datetime import datetime, timedelta
from typing import List, Optional
import numpy as np
import pandas as pd

from app.models.synthetic import (
    WellConfig, WellState, CSSCycle, SRPReading,
    viscosity_from_temperature, temperature_from_css_cycle
)


WELL_SEEDS = {
    "BW-001": 1001,
    "BW-002": 1002,
    "BW-003": 1003,
    "BW-004": 1004,
    "BW-005": 1005,
}


DEFAULT_WELL_CONFIGS = [
    WellConfig(
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
    ),
    WellConfig(
        well_id="BW-002",
        depth_m=1100,
        reservoir_temp_initial_c=105,
        oil_api=11.0,
        pay_thickness_m=22,
        permeability_md=800,
        pump_intake_depth_m=1020,
        tubing_id_inches=2.875,
        rod_diameter_inches=1.0,
        stroke_length_m=3.5,
        pump_diameter_mm=85
    ),
    WellConfig(
        well_id="BW-003",
        depth_m=850,
        reservoir_temp_initial_c=88,
        oil_api=14.0,
        pay_thickness_m=15,
        permeability_md=1500,
        pump_intake_depth_m=780,
        tubing_id_inches=2.375,
        rod_diameter_inches=0.75,
        stroke_length_m=2.5,
        pump_diameter_mm=65
    ),
    WellConfig(
        well_id="BW-004",
        depth_m=1200,
        reservoir_temp_initial_c=110,
        oil_api=10.5,
        pay_thickness_m=25,
        permeability_md=600,
        pump_intake_depth_m=1120,
        tubing_id_inches=3.5,
        rod_diameter_inches=1.125,
        stroke_length_m=3.8,
        pump_diameter_mm=95
    ),
    WellConfig(
        well_id="BW-005",
        depth_m=900,
        reservoir_temp_initial_c=92,
        oil_api=13.0,
        pay_thickness_m=20,
        permeability_md=1000,
        pump_intake_depth_m=830,
        tubing_id_inches=2.875,
        rod_diameter_inches=0.875,
        stroke_length_m=3.2,
        pump_diameter_mm=80
    ),
]


class SyntheticDataGenerator:
    def __init__(self, seed: int = 42):
        self.global_rng = np.random.default_rng(seed)
        self.well_configs = {w.well_id: w for w in DEFAULT_WELL_CONFIGS}

    def get_well_config(self, well_id: str) -> WellConfig:
        return self.well_configs[well_id]

    def generate_css_history(
        self,
        well_id: str,
        n_cycles: int = 8,
        start_date: Optional[datetime] = None
    ) -> List[CSSCycle]:
        config = self.get_well_config(well_id)
        rng = np.random.default_rng(WELL_SEEDS[well_id] + 100)

        if start_date is None:
            start_date = datetime(2023, 1, 1)

        cycles = []
        current_date = start_date

        base_steam_rate = rng.normal(220, 20)
        base_steam_quality = rng.uniform(0.75, 0.85)
        base_injection = rng.uniform(10, 15)
        base_soak = rng.uniform(3, 7)
        base_production = rng.uniform(60, 120)

        for cycle_num in range(1, n_cycles + 1):
            steam_rate = max(150, rng.normal(base_steam_rate * (0.98 ** (cycle_num - 1)), 15))
            steam_quality = np.clip(rng.normal(base_steam_quality, 0.02), 0.65, 0.9)
            injection_days = max(5, rng.normal(base_injection, 1.5))
            soak_days = max(1, rng.normal(base_soak, 1.0))
            production_days = max(30, rng.normal(base_production * (0.95 ** (cycle_num - 1)), 10))

            cycles.append(CSSCycle(
                cycle_num=cycle_num,
                steam_rate_m3_d=round(steam_rate, 1),
                steam_quality=round(steam_quality, 3),
                injection_days=round(injection_days, 1),
                soak_days=round(soak_days, 1),
                production_days=round(production_days, 1)
            ))

            current_date += timedelta(days=injection_days + soak_days + production_days)

        return cycles

    def generate_srp_history(
        self,
        well_id: str,
        n_days: int = 365,
        start_date: Optional[datetime] = None
    ) -> List[SRPReading]:
        config = self.get_well_config(well_id)
        rng = np.random.default_rng(WELL_SEEDS[well_id] + 200)

        if start_date is None:
            start_date = datetime(2023, 1, 1)

        readings = []
        base_spm = rng.uniform(4.0, 6.0)
        base_stroke = config.stroke_length_m
        base_vfd = rng.uniform(30, 45)

        for day in range(n_days):
            spm = np.clip(rng.normal(base_spm, 0.3), 2.0, 8.0)
            stroke = base_stroke * np.clip(rng.normal(1.0, 0.02), 0.9, 1.1)
            vfd = np.clip(rng.normal(base_vfd, 2.0), 20, 55)

            load_base = 80 + 15 * (spm / 5.0) + 10 * (stroke / 3.0)
            load_max = np.clip(rng.normal(load_base, 8), 30, 350)
            load_min = np.clip(rng.normal(load_base * 0.3, 5), 5, 150)

            temp_factor = 1.0
            viscosity_factor = 1.0
            fillage = np.clip(
                0.85 + 0.1 * (1 - viscosity_factor) - 0.05 * (spm / 6.0) + rng.normal(0, 0.03),
                0.6, 1.0
            )
            efficiency = np.clip(fillage * rng.normal(0.95, 0.02), 0.8, 1.0)

            readings.append(SRPReading(
                timestamp=start_date + timedelta(days=day),
                spm=round(spm, 2),
                stroke_length_m=round(stroke, 2),
                polished_rod_load_max_kn=round(load_max, 1),
                polished_rod_load_min_kn=round(load_min, 1),
                fillage=round(fillage, 3),
                pump_efficiency=round(efficiency, 3),
                vfd_frequency_hz=round(vfd, 1)
            ))

        return readings

    def generate_well_states(
        self,
        well_id: str,
        n_days: int = 365,
        start_date: Optional[datetime] = None,
        freq_hours: int = 6
    ) -> List[WellState]:
        config = self.get_well_config(well_id)
        rng = np.random.default_rng(WELL_SEEDS[well_id] + 300)

        if start_date is None:
            start_date = datetime(2023, 1, 1)

        css_cycles = self.generate_css_history(well_id, n_cycles=8, start_date=start_date)
        srp_readings = self.generate_srp_history(well_id, n_days=n_days, start_date=start_date)

        states = []
        timestamps = pd.date_range(start_date, periods=n_days * (24 // freq_hours), freq=f"{freq_hours}h")

        for ts in timestamps:
            day_idx = (ts - start_date).days
            hour_idx = ts.hour // freq_hours

            cycle_info = self._get_cycle_info(ts, css_cycles, start_date)
            cycle_num = cycle_info["cycle_num"]
            day_in_cycle = cycle_info["day_in_cycle"]

            if cycle_num > 0 and cycle_num <= len(css_cycles):
                css = css_cycles[cycle_num - 1]
                temp_c = temperature_from_css_cycle(
                    base_temp=config.reservoir_temp_initial_c,
                    cycle_num=cycle_num,
                    day_in_cycle=day_in_cycle,
                    injection_days=css.injection_days,
                    soak_days=css.soak_days,
                    production_days=css.production_days,
                    steam_rate=css.steam_rate_m3_d,
                    steam_quality=css.steam_quality
                )
                temp_c += rng.normal(0, 2.0)
                steam_rate = css.steam_rate_m3_d if day_in_cycle < css.injection_days else 0
                steam_pressure = rng.normal(4500, 300) if steam_rate > 0 else 0
            else:
                temp_c = config.reservoir_temp_initial_c + rng.normal(0, 1.5)
                steam_rate = 0
                steam_pressure = 0
                cycle_num = 0

            temp_c = np.clip(temp_c, 30, 350)
            viscosity = viscosity_from_temperature(temp_c, config.oil_api)
            viscosity *= rng.lognormal(0, 0.05)
            viscosity = np.clip(viscosity, 0.5, 100000)

            srp_idx = min(day_idx, len(srp_readings) - 1)
            srp = srp_readings[srp_idx]

            prod_base = config.permeability_md * config.pay_thickness_m * 0.02
            prod_base *= (0.95 ** max(0, cycle_num - 1))
            temp_factor = 1 + 0.015 * max(0, temp_c - config.reservoir_temp_initial_c)
            viscosity_factor = max(0.1, 1000 / max(viscosity, 100))
            production_rate = prod_base * temp_factor * viscosity_factor * srp.pump_efficiency
            production_rate *= rng.lognormal(0, 0.08)
            production_rate = np.clip(production_rate, 0, 4000)

            pump_load = 50 + 200 * (viscosity / 10000) * (srp.spm / 5.0) * (srp.stroke_length_m / 3.0)
            pump_load += rng.normal(0, 10)
            pump_load = np.clip(pump_load, 10, 450)

            fillage = srp.fillage
            efficiency = srp.pump_efficiency

            rod_float = max(0.0, 0.4 - fillage * 0.5 + 0.3 * (srp.spm / 8.0) - 0.2 * efficiency)
            rod_float += rng.normal(0, 0.05)
            rod_float = np.clip(rod_float, 0.0, 1.0)

            impact_risk = max(0.0, 0.2 + 0.5 * (srp.spm / 8.0) + 0.3 * (1 - fillage) - 0.2 * efficiency)
            impact_risk += rng.normal(0, 0.05)
            impact_risk = np.clip(impact_risk, 0.0, 1.0)

            states.append(WellState(
                well_id=well_id,
                timestamp=ts.to_pydatetime(),
                temperature_c=round(temp_c, 1),
                viscosity_cp=round(viscosity, 1),
                production_rate_stb_d=round(production_rate, 1),
                steam_rate_m3_d=round(steam_rate, 1),
                steam_pressure_kpa=round(max(0, steam_pressure), 1),
                css_cycle=cycle_num,
                srp_spm=round(srp.spm, 2),
                stroke_length_m=round(srp.stroke_length_m, 2),
                pump_load_kn=round(pump_load, 1),
                fillage=round(fillage, 3),
                pump_efficiency=round(efficiency, 3),
                vfd_frequency_hz=round(srp.vfd_frequency_hz, 1),
                rod_float_risk=round(rod_float, 3),
                impact_loading_risk=round(impact_risk, 3)
            ))

        return states

    def _get_cycle_info(self, ts: datetime, cycles: List[CSSCycle], start_date: datetime) -> dict:
        days_elapsed = (ts - start_date).days
        cumulative = 0
        for i, cycle in enumerate(cycles):
            cycle_duration = cycle.injection_days + cycle.soak_days + cycle.production_days
            if days_elapsed < cumulative + cycle_duration:
                return {
                    "cycle_num": i + 1,
                    "day_in_cycle": days_elapsed - cumulative
                }
            cumulative += cycle_duration
        return {"cycle_num": len(cycles) + 1, "day_in_cycle": days_elapsed - cumulative}

    def generate_all_wells(
        self,
        n_days: int = 365,
        start_date: Optional[datetime] = None,
        freq_hours: int = 6
    ) -> dict:
        all_states = {}
        for well_id in WELL_SEEDS.keys():
            all_states[well_id] = self.generate_well_states(
                well_id, n_days, start_date, freq_hours
            )
        return all_states

    def to_dataframe(self, states: List[WellState]) -> pd.DataFrame:
        records = [s.model_dump() for s in states]
        return pd.DataFrame(records)

    def save_parquet(self, states: List[WellState], path: str) -> None:
        df = self.to_dataframe(states)
        df.to_parquet(path, index=False)

    def save_csv(self, states: List[WellState], path: str) -> None:
        df = self.to_dataframe(states)
        df.to_csv(path, index=False)