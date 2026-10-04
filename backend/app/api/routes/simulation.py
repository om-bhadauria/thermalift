"""
Simulation endpoint for THERMALIFT API.
Runs the existing physics simulation pipeline.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.models.synthetic import WellConfig, CSSCycle
from app.services.physics_models import PipelineEngine
from app.core.config import settings
from app.data.synthetic_data import DEFAULT_WELL_CONFIGS


router = APIRouter()


# Request/Response Models
class SimulationRequest(BaseModel):
    """Request model for physics simulation."""
    well_id: str = Field(..., description="Well identifier (e.g., BW-001)")
    css_params: dict = Field(..., description="CSS cycle parameters")
    srp_params: dict = Field(..., description="SRP operating parameters")
    day_in_cycle: float = Field(default=5.0, description="Day within the CSS cycle")
    cycle_num: int = Field(default=1, description="CSS cycle number")
    wellhead_pressure_kpa: float = Field(default=500.0, description="Wellhead pressure in kPa")


class SimulationResponse(BaseModel):
    """Response model for physics simulation."""
    well_id: str
    timestamp: str
    temperature_c: float
    viscosity_cp: float
    production_rate_stb_d: float
    steam_rate_m3_d: float
    steam_pressure_kpa: float
    css_cycle: int
    srp_spm: float
    stroke_length_m: float
    pump_load_kn: float
    fillage: float
    pump_efficiency: float
    vfd_frequency_hz: float
    rod_float_risk: float
    impact_loading_risk: float
    data_source: str
    disclaimer: str = "Simulation results are based on synthetic/demo data and are not validated against real Baghewala/OIL field operations."


def get_well_config(well_id: str) -> WellConfig:
    """Get well configuration by ID."""
    for config in DEFAULT_WELL_CONFIGS:
        if config.well_id == well_id:
            return config
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Well configuration not found for well_id: {well_id}"
    )


def validate_css_params(css_params: dict) -> CSSCycle:
    """Validate and convert CSS parameters."""
    try:
        return CSSCycle(
            cycle_num=css_params.get("cycle_num", 1),
            steam_rate_m3_d=css_params.get("steam_rate_m3_d", 200),
            steam_quality=css_params.get("steam_quality", 0.8),
            injection_days=css_params.get("injection_days", 10),
            soak_days=css_params.get("soak_days", 5),
            production_days=css_params.get("production_days", 90)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSS parameters: {str(e)}"
        )


def validate_srp_params(srp_params: dict) -> dict:
    """Validate SRP parameters."""
    required = ["spm", "stroke_length_m", "vfd_frequency_hz"]
    for key in required:
        if key not in srp_params:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required SRP parameter: {key}"
            )
    return {
        "spm": float(srp_params["spm"]),
        "stroke_length_m": float(srp_params["stroke_length_m"]),
        "vfd_frequency_hz": float(srp_params["vfd_frequency_hz"])
    }


@router.post("/simulation", response_model=SimulationResponse)
async def run_simulation(request: SimulationRequest):
    """
    Run physics simulation for given well and operating parameters.
    
    Uses the existing PipelineEngine to simulate:
    - Thermal model (temperature prediction)
    - Viscosity model
    - Wellbore model (pressure drops)
    - SRP model (pump load, fillage, efficiency, risks)
    
    All results are based on synthetic/demo data.
    """
    try:
        # Get well configuration
        well_config = get_well_config(request.well_id)
        
        # Validate parameters
        css_cycle = validate_css_params(request.css_params)
        srp_params = validate_srp_params(request.srp_params)
        
        # Run simulation through existing pipeline
        engine = PipelineEngine(well_config)
        state = engine.run_simulation(
            css_params=css_cycle,
            srp_params=srp_params,
            day_in_cycle=request.day_in_cycle,
            cycle_num=request.cycle_num,
            wellhead_pressure_kpa=request.wellhead_pressure_kpa
        )
        
        # Return response
        return SimulationResponse(
            well_id=state.well_id,
            timestamp=state.timestamp.isoformat(),
            temperature_c=state.temperature_c,
            viscosity_cp=state.viscosity_cp,
            production_rate_stb_d=state.production_rate_stb_d,
            steam_rate_m3_d=state.steam_rate_m3_d,
            steam_pressure_kpa=state.steam_pressure_kpa,
            css_cycle=state.css_cycle,
            srp_spm=state.srp_spm,
            stroke_length_m=state.stroke_length_m,
            pump_load_kn=state.pump_load_kn,
            fillage=state.fillage,
            pump_efficiency=state.pump_efficiency,
            vfd_frequency_hz=state.vfd_frequency_hz,
            rod_float_risk=state.rod_float_risk,
            impact_loading_risk=state.impact_loading_risk,
            data_source=state.data_source
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {str(e)}"
        )


@router.get("/simulation/wells")
async def list_wells():
    """List available well configurations."""
    return {
        "wells": [
            {
                "well_id": config.well_id,
                "depth_m": config.depth_m,
                "reservoir_temp_initial_c": config.reservoir_temp_initial_c,
                "oil_api": config.oil_api,
                "pay_thickness_m": config.pay_thickness_m,
                "permeability_md": config.permeability_md
            }
            for config in DEFAULT_WELL_CONFIGS
        ],
        "data_source": "SYNTHETIC",
        "disclaimer": "Well configurations are synthetic/demo data."
    }