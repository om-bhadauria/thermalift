export interface WellConfig {
  well_id: string;
  depth_m: number;
  reservoir_temp_initial_c: number;
  oil_api: number;
  pay_thickness_m: number;
  permeability_md: number;
  pump_intake_depth_m: number;
  tubing_id_inches: number;
  rod_diameter_inches: number;
  stroke_length_m: number;
  pump_diameter_mm: number;
}

export interface CSSParams {
  steam_rate_m3_d: number;
  steam_quality: number;
  injection_days: number;
  soak_days: number;
  production_days: number;
}

export interface SRPParams {
  spm: number;
  stroke_length_m: number;
  vfd_frequency_hz: number;
}

export interface SimulationRequest {
  well_id: string;
  css_params: CSSParams;
  srp_params: SRPParams;
  day_in_cycle?: number;
  cycle_num?: number;
  wellhead_pressure_kpa?: number;
}

export interface SimulationResponse {
  well_id: string;
  timestamp: string;
  temperature_c: number;
  viscosity_cp: number;
  production_rate_stb_d: number;
  steam_rate_m3_d: number;
  steam_pressure_kpa: number;
  css_cycle: number;
  srp_spm: number;
  stroke_length_m: number;
  pump_load_kn: number;
  fillage: number;
  pump_efficiency: number;
  vfd_frequency_hz: number;
  rod_float_risk: number;
  impact_loading_risk: number;
  data_source: string;
  disclaimer: string;
}

export interface WellsResponse {
  wells: WellConfig[];
  data_source: string;
  disclaimer: string;
}

export interface PredictionRequest {
  well_id: string;
  state: Record<string, number | string>;
}

export interface ModelInfo {
  production_model: {
    type: string;
    n_estimators: number;
    features: number;
    training_metrics: Record<string, number>;
  };
  rod_float_risk_model: {
    type: string;
    n_estimators: number;
    features: number;
    training_metrics: Record<string, number>;
  };
  impact_loading_risk_model: {
    type: string;
    n_estimators: number;
    features: number;
    training_metrics: Record<string, number>;
  };
}

export interface PredictionResponse {
  well_id: string;
  predicted_production_stb_d: number;
  predicted_rod_float_risk: number;
  predicted_impact_loading_risk: number;
  model_info: ModelInfo;
  data_source: string;
  disclaimer: string;
}

export interface ModelStatusResponse {
  initialized: boolean;
  production_forecaster: boolean;
  rod_float_predictor: boolean;
  impact_loading_predictor: boolean;
  data_source: string;
}

export interface OptimizationConstraints {
  steam_rate_min: number;
  steam_rate_max: number;
  steam_quality_min: number;
  steam_quality_max: number;
  injection_days_min: number;
  injection_days_max: number;
  soak_days_min: number;
  soak_days_max: number;
  production_days_min: number;
  production_days_max: number;
  spm_min: number;
  spm_max: number;
  stroke_length_min: number;
  stroke_length_max: number;
  vfd_frequency_min: number;
  vfd_frequency_max: number;
  max_rod_float_risk: number;
  max_impact_loading_risk: number;
  min_production_stb_d: number;
  min_fill_age: number;
  min_pump_efficiency: number;
}

export interface ObjectiveWeights {
  production_weight: number;
  steam_weight: number;
  risk_weight: number;
  operating_weight: number;
}

export interface OptimizationRequest {
  well_id: string;
  grid_resolution?: number;
  day_in_cycle?: number;
  cycle_num?: number;
  wellhead_pressure_kpa?: number;
  constraints?: Partial<OptimizationConstraints>;
  weights?: Partial<ObjectiveWeights>;
  random_seed?: number;
}

export interface BaselineComparison {
  baseline_production_stb_d: number;
  optimized_production_stb_d: number;
  production_change_pct: number;
  baseline_steam_m3_d: number;
  optimized_steam_m3_d: number;
  steam_change_pct: number;
  baseline_rod_float_risk: number;
  optimized_rod_float_risk: number;
  baseline_impact_loading_risk: number;
  optimized_impact_loading_risk: number;
  baseline_objective_score: number;
  optimized_objective_score: number;
  objective_improvement: number;
}

export interface OptimizationRecommendation {
  recommended_css: CSSParams;
  recommended_srp: SRPParams;
  predicted_production_stb_d: number;
  predicted_rod_float_risk: number;
  predicted_impact_loading_risk: number;
  objective_score: number;
  constraints_satisfied: string[];
  explanation: string;
}

export interface BestCandidate {
  css_params: CSSParams;
  srp_params: SRPParams;
  predicted_production_stb_d: number;
  predicted_rod_float_risk: number;
  predicted_impact_loading_risk: number;
  steam_usage_m3_d: number;
  steam_intensity: number;
  objective_score: number;
  is_feasible: boolean;
  constraint_violations: string[];
}

export interface OptimizationResponse {
  well_id: string;
  best_candidate: BestCandidate;
  baseline_comparison: BaselineComparison;
  recommendation: OptimizationRecommendation;
  total_evaluated: number;
  feasible_count: number;
  execution_time_seconds: number;
  data_source: string;
  disclaimer: string;
}

export interface DefaultConstraintsResponse {
  constraints: OptimizationConstraints;
  description: string;
}

export interface DefaultWeightsResponse {
  weights: ObjectiveWeights;
  description: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  data_policy: string;
  version: string;
}

export interface ApiError {
  detail: string;
}