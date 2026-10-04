from app.models.synthetic import (
    WellConfig, WellState, CSSCycle, SRPReading,
    viscosity_from_temperature, temperature_from_css_cycle
)
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta


class ThermalModel:
    """
    Thermal model for CSS wellbore temperature prediction.
    Uses analytical/semi-analytical heat transfer equations.
    """
    
    def __init__(self, well_config: WellConfig):
        self.config = well_config
    
    def predict_temperature(
        self,
        cycle_num: int,
        day_in_cycle: float,
        css_params: CSSCycle
    ) -> float:
        """Predict wellbore temperature at given cycle and day."""
        return temperature_from_css_cycle(
            base_temp=self.config.reservoir_temp_initial_c,
            cycle_num=cycle_num,
            day_in_cycle=day_in_cycle,
            injection_days=css_params.injection_days,
            soak_days=css_params.soak_days,
            production_days=css_params.production_days,
            steam_rate=css_params.steam_rate_m3_d,
            steam_quality=css_params.steam_quality
        )
    
    def predict_temperature_profile(
        self,
        css_schedule: List[CSSCycle],
        days: int = 90,
        freq_hours: int = 6
    ) -> List[Dict[str, Any]]:
        """Generate temperature profile over multiple days."""
        results = []
        start_date = datetime.now()
        
        for day_idx in range(days):
            for hour_idx in range(0, 24, freq_hours):
                ts = start_date + timedelta(days=day_idx, hours=hour_idx)
                day_in_cycle = day_idx % sum(c.injection_days + c.soak_days + c.production_days for c in css_schedule)
                
                cycle_num = 1
                cumulative = 0
                for i, cycle in enumerate(css_schedule):
                    cycle_duration = cycle.injection_days + cycle.soak_days + cycle.production_days
                    if day_idx < cumulative + cycle_duration:
                        cycle_num = i + 1
                        day_in_cycle = day_idx - cumulative
                        break
                    cumulative += cycle_duration
                
                css = css_schedule[cycle_num - 1] if cycle_num <= len(css_schedule) else css_schedule[-1]
                temp = self.predict_temperature(cycle_num, day_in_cycle, css)
                
                results.append({
                    "timestamp": ts.isoformat(),
                    "cycle_num": cycle_num,
                    "day_in_cycle": day_in_cycle,
                    "temperature_c": round(temp, 1)
                })
        
        return results


class ViscosityModel:
    """Oil viscosity prediction based on temperature and oil properties."""
    
    def __init__(self, well_config: WellConfig):
        self.config = well_config
    
    def predict_viscosity(self, temperature_c: float) -> float:
        """Predict oil viscosity at given temperature."""
        return viscosity_from_temperature(temperature_c, self.config.oil_api)
    
    def predict_viscosity_profile(
        self,
        temperatures: List[float]
    ) -> List[float]:
        """Predict viscosity for multiple temperatures."""
        return [self.predict_viscosity(t) for t in temperatures]


class WellboreModel:
    """
    Wellbore fluid flow model.
    Calculates pressure drops, flow regimes, and fluid state.
    """
    
    def __init__(self, well_config: WellConfig):
        self.config = well_config
        self.g = 9.81  # m/s^2
        self.rho_oil_base = 950  # kg/m^3 at reference
        self.rho_water = 1000  # kg/m^3
    
    def calculate_bottomhole_pressure(
        self,
        wellhead_pressure_kpa: float,
        temperature_c: float,
        viscosity_cp: float,
        production_rate_stb_d: float,
        water_cut: float = 0.3
    ) -> float:
        """Calculate bottomhole pressure from wellhead pressure."""
        # Simplified wellbore pressure drop calculation
        # ΔP = ρ*g*h + friction losses
        
        depth = self.config.pump_intake_depth_m
        rho_mix = self.rho_oil_base * (1 - water_cut) + self.rho_water * water_cut
        
        # Hydrostatic head
        hydrostatic = rho_mix * self.g * depth / 1000  # kPa
        
        # Friction loss (simplified Darcy-Weisbach)
        tubing_area = np.pi * (self.config.tubing_id_inches * 0.0254 / 2) ** 2
        velocity = (production_rate_stb_d * 0.159 / 86400) / tubing_area  # m/s
        
        # Friction factor (simplified)
        re = rho_mix * velocity * self.config.tubing_id_inches * 0.0254 / (viscosity_cp * 0.001)
        if re > 4000:
            f = 0.316 / (re ** 0.25)  # Blasius for turbulent
        else:
            f = 64 / max(re, 1)  # Laminar
        
        friction = f * (depth / (self.config.tubing_id_inches * 0.0254)) * (rho_mix * velocity ** 2 / 2) / 1000
        
        return wellhead_pressure_kpa + hydrostatic + friction
    
    def calculate_flow_regime(
        self,
        production_rate_stb_d: float,
        viscosity_cp: float,
        water_cut: float = 0.3
    ) -> str:
        """Determine flow regime in tubing."""
        tubing_area = np.pi * (self.config.tubing_id_inches * 0.0254 / 2) ** 2
        velocity = (production_rate_stb_d * 0.159 / 86400) / tubing_area
        
        rho_mix = self.rho_oil_base * (1 - water_cut) + self.rho_water * water_cut
        re = rho_mix * velocity * self.config.tubing_id_inches * 0.0254 / (viscosity_cp * 0.001)
        
        if re < 2000:
            return "laminar"
        elif re < 4000:
            return "transitional"
        else:
            return "turbulent"


class SRPModel:
    """
    Sucker Rod Pump dynamics model.
    Calculates pump load, fillage, efficiency, and dynamometer card parameters.
    """
    
    def __init__(self, well_config: WellConfig, random_seed: int = None):
        self.config = well_config
        self.g = 9.81  # m/s^2
        self.rod_weight_per_m = 7850 * np.pi * (self.config.rod_diameter_inches * 0.0254 / 2) ** 2  # kg/m
        self.rod_modulus = 200e9  # Pa
        self.rng = np.random.default_rng(random_seed) if random_seed is not None else np.random.default_rng()
    
    def calculate_pump_load(
        self,
        viscosity_cp: float,
        spm: float,
        stroke_length_m: float,
        pump_diameter_mm: float,
        bottomhole_pressure_kpa: float,
        wellhead_pressure_kpa: float
    ) -> Dict[str, float]:
        """Calculate polished rod loads and pump parameters."""
        
        pump_area = np.pi * (pump_diameter_mm / 1000 / 2) ** 2
        
        # Pressure differential across pump
        dp = bottomhole_pressure_kpa - wellhead_pressure_kpa  # kPa
        
        # Pump displacement volume per stroke
        displacement = pump_area * stroke_length_m  # m^3/stroke
        
        # Theoretical production
        theo_production = displacement * spm * 60 * 24 / 0.159  # STB/d (approximate)
        
        # Viscosity effect on pump efficiency
        visc_factor = max(0.3, min(1.5, 1000 / max(viscosity_cp, 100)))
        
        # Load calculations
        fluid_load = dp * 1000 * pump_area  # N
        rod_weight = self.rod_weight_per_m * self.config.pump_intake_depth_m * self.g  # N
        
        # Dynamic loads
        acceleration = 4 * np.pi ** 2 * spm / 60 * stroke_length_m / 2  # m/s^2
        rod_mass = self.rod_weight_per_m * self.config.pump_intake_depth_m
        dynamic_load = rod_mass * acceleration
        
        max_load = fluid_load + rod_weight + dynamic_load
        min_load = rod_weight - dynamic_load * 0.5  # Simplified
        
        # Fillage calculation
        fillage = min(1.0, max(0.3, visc_factor * 0.95 * (5.0 / max(spm, 1)) * (3.0 / max(stroke_length_m, 1))))
        
        # Pump efficiency
        efficiency = fillage * 0.92 * max(0.7, 1.0 - (spm - 5.0) * 0.03)
        efficiency = min(1.0, efficiency)
        
        return {
            "polished_rod_load_max_kn": round(max_load / 1000, 1),
            "polished_rod_load_min_kn": round(max(min_load / 1000, 5), 1),
            "fillage": round(fillage, 3),
            "pump_efficiency": round(efficiency, 3),
            "fluid_load_kn": round(fluid_load / 1000, 1),
            "theoretical_production_stb_d": round(theo_production, 1)
        }
    
    def calculate_dynamometer_card(
        self,
        viscosity_cp: float,
        spm: float,
        stroke_length_m: float,
        pump_load: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate simplified dynamometer card data."""
        # Simplified card - returns key points
        return {
            "load_max_kn": pump_load["polished_rod_load_max_kn"],
            "load_min_kn": pump_load["polished_rod_load_min_kn"],
            "stroke_length_m": stroke_length_m,
            "spm": spm,
            "card_area_kn_m": round((pump_load["polished_rod_load_max_kn"] - pump_load["polished_rod_load_min_kn"]) * stroke_length_m * 0.8, 2)
        }
    
    def calculate_risks(
        self,
        fillage: float,
        efficiency: float,
        spm: float,
        stroke_length_m: float,
        pump_load_max_kn: float,
        pump_load_min_kn: float
    ) -> Dict[str, float]:
        """Calculate rod float and impact loading risks."""
        
        # Rod float risk: increases with low fillage, high SPM, low efficiency
        rod_float = max(0.0, 
            0.4 - fillage * 0.5 + 0.3 * (spm / 8.0) - 0.2 * efficiency
        )
        rod_float = max(0.0, min(1.0, rod_float + self.rng.normal(0, 0.02)))
        
        # Impact loading risk: increases with high SPM, low fillage, low efficiency
        impact_risk = max(0.0,
            0.2 + 0.5 * (spm / 8.0) + 0.3 * (1 - fillage) - 0.2 * efficiency
        )
        impact_risk = max(0.0, min(1.0, impact_risk + self.rng.normal(0, 0.02)))
        
        # Gas lock risk (proxy)
        gas_lock = max(0.0, 0.3 - fillage * 0.4 + 0.2 * (1 - efficiency))
        gas_lock = max(0.0, min(1.0, gas_lock))
        
        return {
            "rod_float_risk": round(rod_float, 3),
            "impact_loading_risk": round(impact_risk, 3),
            "gas_lock_risk": round(gas_lock, 3)
        }


class PipelineEngine:
    """
    Main pipeline engine that couples all models together.
    """
    
    def __init__(self, well_config: WellConfig, random_seed: int = None):
        self.config = well_config
        self.thermal = ThermalModel(well_config)
        self.viscosity = ViscosityModel(well_config)
        self.wellbore = WellboreModel(well_config)
        self.srp = SRPModel(well_config, random_seed=random_seed)
    
    def run_simulation(
        self,
        css_params: CSSCycle,
        srp_params: Dict[str, float],
        day_in_cycle: float = 0,
        cycle_num: int = 1,
        wellhead_pressure_kpa: float = 500
    ) -> WellState:
        """Run complete simulation pipeline for given parameters."""
        
        # 1. Thermal model
        temperature = self.thermal.predict_temperature(
            cycle_num=cycle_num,
            day_in_cycle=day_in_cycle,
            css_params=css_params
        )
        
        # 2. Viscosity model
        viscosity = self.viscosity.predict_viscosity(temperature)
        
        # 3. Wellbore model
        bhp = self.wellbore.calculate_bottomhole_pressure(
            wellhead_pressure_kpa=wellhead_pressure_kpa,
            temperature_c=temperature,
            viscosity_cp=viscosity,
            production_rate_stb_d=0  # Initial guess
        )
        
        # 4. SRP model
        srp_results = self.srp.calculate_pump_load(
            viscosity_cp=viscosity,
            spm=srp_params["spm"],
            stroke_length_m=srp_params["stroke_length_m"],
            pump_diameter_mm=self.config.pump_diameter_mm,
            bottomhole_pressure_kpa=bhp,
            wellhead_pressure_kpa=wellhead_pressure_kpa
        )
        
        # 5. Production forecast
        prod_base = self.config.permeability_md * self.config.pay_thickness_m * 0.02
        temp_factor = 1 + 0.015 * max(0, temperature - self.config.reservoir_temp_initial_c)
        viscosity_factor = max(0.1, 1000 / max(viscosity, 100))
        production_rate = prod_base * temp_factor * viscosity_factor * srp_results["pump_efficiency"]
        
        # Recalculate BHP with estimated production
        bhp = self.wellbore.calculate_bottomhole_pressure(
            wellhead_pressure_kpa=wellhead_pressure_kpa,
            temperature_c=temperature,
            viscosity_cp=viscosity,
            production_rate_stb_d=production_rate
        )
        
        # Recalculate SRP with updated BHP
        srp_results = self.srp.calculate_pump_load(
            viscosity_cp=viscosity,
            spm=srp_params["spm"],
            stroke_length_m=srp_params["stroke_length_m"],
            pump_diameter_mm=self.config.pump_diameter_mm,
            bottomhole_pressure_kpa=bhp,
            wellhead_pressure_kpa=wellhead_pressure_kpa
        )
        
        # 6. Risk model
        risks = self.srp.calculate_risks(
            fillage=srp_results["fillage"],
            efficiency=srp_results["pump_efficiency"],
            spm=srp_params["spm"],
            stroke_length_m=srp_params["stroke_length_m"],
            pump_load_max_kn=srp_results["polished_rod_load_max_kn"],
            pump_load_min_kn=srp_results["polished_rod_load_min_kn"]
        )
        
        # 7. Dynamometer card
        dyno_card = self.srp.calculate_dynamometer_card(
            viscosity_cp=viscosity,
            spm=srp_params["spm"],
            stroke_length_m=srp_params["stroke_length_m"],
            pump_load=srp_results
        )
        
        # Calculate steam-oil ratio
        steam_rate = css_params.steam_rate_m3_d if day_in_cycle < css_params.injection_days else 0
        sor = steam_rate / max(production_rate, 0.1) if steam_rate > 0 else 0
        
        return WellState(
            well_id=self.config.well_id,
            timestamp=datetime.now(),
            temperature_c=round(temperature, 1),
            viscosity_cp=round(viscosity, 1),
            production_rate_stb_d=round(production_rate, 1),
            steam_rate_m3_d=round(steam_rate, 1),
            steam_pressure_kpa=round(4500 if steam_rate > 0 else 0, 1),
            css_cycle=cycle_num,
            srp_spm=srp_params["spm"],
            stroke_length_m=srp_params["stroke_length_m"],
            pump_load_kn=round((srp_results["polished_rod_load_max_kn"] + srp_results["polished_rod_load_min_kn"]) / 2, 1),
            fillage=srp_results["fillage"],
            pump_efficiency=srp_results["pump_efficiency"],
            vfd_frequency_hz=srp_params.get("vfd_frequency_hz", 40),
            rod_float_risk=risks["rod_float_risk"],
            impact_loading_risk=risks["impact_loading_risk"],
            data_source="SYNTHETIC"
        )
    
    def run_scenario(
        self,
        css_params: CSSCycle,
        srp_params: Dict[str, float],
        days: int = 30,
        wellhead_pressure_kpa: float = 500
    ) -> List[WellState]:
        """Run simulation over multiple days."""
        results = []
        
        for day in range(days):
            state = self.run_simulation(
                css_params=css_params,
                srp_params=srp_params,
                day_in_cycle=day % (css_params.injection_days + css_params.soak_days + css_params.production_days),
                cycle_num=1 + day // (css_params.injection_days + css_params.soak_days + css_params.production_days),
                wellhead_pressure_kpa=wellhead_pressure_kpa
            )
            results.append(state)
        
        return results