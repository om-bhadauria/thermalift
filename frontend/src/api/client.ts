import axios, { type AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import type {
  SimulationRequest,
  SimulationResponse,
  WellsResponse,
  PredictionRequest,
  PredictionResponse,
  ModelStatusResponse,
  OptimizationRequest,
  OptimizationResponse,
  DefaultConstraintsResponse,
  DefaultWeightsResponse,
  HealthResponse,
  ApiError,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const API_PREFIX = '/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 60000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        return config;
      },
      (error: AxiosError) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        const message = error.response?.data?.detail || error.message || 'Unknown error';
        return Promise.reject(new Error(message));
      }
    );
  }

  async healthCheck(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>(`${API_PREFIX}/health`);
    return response.data;
  }

  async getWells(): Promise<WellsResponse> {
    const response = await this.client.get<WellsResponse>(`${API_PREFIX}/simulation/wells`);
    return response.data;
  }

  async runSimulation(request: SimulationRequest): Promise<SimulationResponse> {
    const response = await this.client.post<SimulationResponse>(
      `${API_PREFIX}/simulation`,
      request
    );
    return response.data;
  }

  async runPrediction(request: PredictionRequest): Promise<PredictionResponse> {
    const response = await this.client.post<PredictionResponse>(
      `${API_PREFIX}/prediction`,
      request
    );
    return response.data;
  }

  async getModelStatus(): Promise<ModelStatusResponse> {
    const response = await this.client.get<ModelStatusResponse>(
      `${API_PREFIX}/prediction/models/status`
    );
    return response.data;
  }

  async runOptimization(request: OptimizationRequest): Promise<OptimizationResponse> {
    const response = await this.client.post<OptimizationResponse>(
      `${API_PREFIX}/optimization`,
      request
    );
    return response.data;
  }

  async getDefaultConstraints(): Promise<DefaultConstraintsResponse> {
    const response = await this.client.get<DefaultConstraintsResponse>(
      `${API_PREFIX}/optimization/constraints/default`
    );
    return response.data;
  }

  async getDefaultWeights(): Promise<DefaultWeightsResponse> {
    const response = await this.client.get<DefaultWeightsResponse>(
      `${API_PREFIX}/optimization/weights/default`
    );
    return response.data;
  }
}

export const apiClient = new ApiClient();