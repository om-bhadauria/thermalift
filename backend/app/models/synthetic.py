from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
import numpy as np


class WellConfig(BaseModel):
    well_id: str = Field(..., pattern=r"^BW-\d{3}$")
    field: str = "Baghewala"
    depth_m: float = Field(..., ge=500, le=2000)
    reservoir_temp_initial_c: float = Field(..., ge=50, le=150)
    oil_api: float = Field(..., ge=8, le=20)
    pay_thickness_m: float = Field(..., ge=5, le=50)
    permeability_md: float = Field(..., ge=100, le=5000)
    pump_intake_depth_m: float = Field(..., ge=400, le=1800)
    tubing_id_inches: float = Field(..., ge=2.0, le=4.5)
    rod_diameter_inches: float = Field(..., ge=0.75, le=1.125)
    stroke_length_m: float = Field(..., ge=1.5, le=4.0)
    pump_diameter_mm: float = Field(..., ge=50, le=120)
    data_source: Literal["SYNTHETIC"] = "SYNTHETIC"

    @field_validator("pump_intake_depth_m")
    @classmethod
    def pump_above_bottom(cls, v, info):
        if "depth_m" in info.data and v >= info.data["depth_m"]:
            raise ValueError("pump_intake_depth_m must be less than well depth_m")
        return v


class WellState(BaseModel):
    well_id: str
    timestamp: datetime
    temperature_c: float = Field(..., ge=20, le=350)
    viscosity_cp: float = Field(..., ge=0.1, le=100000)
    production_rate_stb_d: float = Field(..., ge=0, le=5000)
    steam_rate_m3_d: float = Field(..., ge=0, le=500)
    steam_pressure_kpa: float = Field(..., ge=0, le=10000)
    css_cycle: int = Field(..., ge=0, le=20)
    srp_spm: float = Field(..., ge=0, le=30)
    stroke_length_m: float = Field(..., ge=0.5, le=5.0)
    pump_load_kn: float = Field(..., ge=0, le=500)
    fillage: float = Field(..., ge=0.0, le=1.0)
    pump_efficiency: float = Field(..., ge=0.0, le=1.0)
    vfd_frequency_hz: float = Field(..., ge=0, le=60)
    rod_float_risk: float = Field(..., ge=0.0, le=1.0)
    impact_loading_risk: float = Field(..., ge=0.0, le=1.0)
    data_source: Literal["SYNTHETIC"] = "SYNTHETIC"

    @field_validator("data_source")
    @classmethod
    def check_synthetic(cls, v):
        if v != "SYNTHETIC":
            raise ValueError("Only SYNTHETIC data source allowed in this prototype")
        return v


class CSSCycle(BaseModel):
    cycle_num: int
    steam_rate_m3_d: float
    steam_quality: float
    injection_days: float
    soak_days: float
    production_days: float
    data_source: Literal["SYNTHETIC"] = "SYNTHETIC"


class SRPReading(BaseModel):
    timestamp: datetime
    spm: float
    stroke_length_m: float
    polished_rod_load_max_kn: float
    polished_rod_load_min_kn: float
    fillage: float
    pump_efficiency: float
    vfd_frequency_hz: float
    data_source: Literal["SYNTHETIC"] = "SYNTHETIC"


def viscosity_from_temperature(temp_c: float, oil_api: float, a: float = None, b: float = None, c: float = None) -> float:
    if a is None or b is None or c is None:
        a = 10**(2.5 - 0.03 * oil_api)
        b = 1500 + 30 * (20 - oil_api)
        c = -30
    temp_k = temp_c + 273.15
    vis = a * np.exp(b / (temp_k + c))
    return np.clip(vis, 0.5, 100000)


def temperature_from_css_cycle(
    base_temp: float,
    cycle_num: int,
    day_in_cycle: float,
    injection_days: float,
    soak_days: float,
    production_days: float,
    steam_rate: float,
    steam_quality: float
) -> float:
    total_cycle = injection_days + soak_days + production_days
    phase = day_in_cycle / total_cycle

    if phase < injection_days / total_cycle:
        heat_factor = 0.8 + 0.2 * (phase / (injection_days / total_cycle))
        temp_rise = 80 * heat_factor * (steam_rate / 200) * steam_quality
    elif phase < (injection_days + soak_days) / total_cycle:
        soak_phase = (phase - injection_days / total_cycle) / (soak_days / total_cycle)
        temp_rise = 80 * (1 - 0.3 * soak_phase) * (steam_rate / 200) * steam_quality
    else:
        prod_phase = (phase - (injection_days + soak_days) / total_cycle) / (production_days / total_cycle)
        temp_rise = 80 * (0.7 - 0.4 * prod_phase) * (steam_rate / 200) * steam_quality

    return base_temp + temp_rise * (0.95 ** cycle_num)