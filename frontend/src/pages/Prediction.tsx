import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Play, Loader2, BarChart2, Zap, AlertTriangle } from 'lucide-react';
import { apiClient } from '../api';
import { Card, CardGrid } from '../components/common/Card';
import { Loading, SkeletonCard } from '../components/common/Loading';
import { ErrorDisplay, AlertBanner } from '../components/common/Error';
import { RiskMetricCard } from '../components/dashboard/MetricCard';
import { formatNumber, formatInteger, formatPercent, formatTimestamp } from '../utils/format';
import type { PredictionResponse, WellConfig } from '../types/api';
import { useWellsContext } from '../contexts/WellsContext';

export function PredictionPage() {
  const { wells, selectedWell } = useWellsContext();
  const wellId = selectedWell || 'BW-001';
  const [customState, setCustomState] = useState<Record<string, number>>({});
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const currentWell = wells.find((w) => w.well_id === wellId);

  const predictionQuery = useQuery<PredictionResponse, Error>({
    queryKey: ['prediction', wellId],
    queryFn: () => apiClient.runPrediction({
      well_id: wellId,
      state: {
        temperature_c: 120,
        viscosity_cp: 5000,
        steam_rate_m3_d: 200,
        steam_pressure_kpa: 4500,
        css_cycle: 1,
        srp_spm: 5.0,
        stroke_length_m: 3.0,
        pump_load_kn: 150,
        fillage: 0.85,
        pump_efficiency: 0.88,
        vfd_frequency_hz: 40.0,
        ...customState,
      },
    }),
    enabled: !!wellId,
    staleTime: 60000,
    retry: 1,
  });

  const manualPredictionMutation = useMutation({
    mutationFn: (state: Record<string, number>) => apiClient.runPrediction({
      well_id: wellId,
      state: {
        temperature_c: 120,
        viscosity_cp: 5000,
        steam_rate_m3_d: 200,
        steam_pressure_kpa: 4500,
        css_cycle: 1,
        srp_spm: 5.0,
        stroke_length_m: 3.0,
        pump_load_kn: 150,
        fillage: 0.85,
        pump_efficiency: 0.88,
        vfd_frequency_hz: 40.0,
        ...state,
      },
    }),
    onSuccess: (data) => {
      queryClient.setQueryData(['prediction', wellId], data);
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const handleCustomPredict = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    manualPredictionMutation.mutate(customState);
  };

  if (predictionQuery.isLoading && !predictionQuery.data) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">ML Prediction</h1>
            <p className="text-gray-500 mt-1">Production forecasting and risk prediction using trained ML models</p>
          </div>
          <span className="px-3 py-1 bg-amber-50 border border-amber-200 rounded-lg text-sm font-medium text-amber-800">
            Synthetic/Demo Data
          </span>
        </div>
        <CardGrid columns={3}>
          <SkeletonCard lines={4} />
          <SkeletonCard lines={4} />
          <SkeletonCard lines={4} />
        </CardGrid>
        <CardGrid columns={2}>
          <SkeletonCard lines={5} />
          <SkeletonCard lines={5} />
        </CardGrid>
      </div>
    );
  }

  if (predictionQuery.isError && !predictionQuery.data) {
    return (
      <ErrorDisplay
        message={predictionQuery.error?.message || 'Failed to load prediction'}
        title="Prediction Error"
        onRetry={() => predictionQuery.refetch()}
        variant="card"
      />
    );
  }

  const pred = predictionQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">ML Prediction</h1>
          <p className="text-gray-500 mt-1">Production forecasting and risk prediction using trained ML models</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-3 py-1 bg-amber-50 border border-amber-200 rounded-lg text-sm font-medium text-amber-800">
            Synthetic/Demo Data
          </span>
        </div>
      </div>

      {error && (
        <AlertBanner
          message={error}
          type="error"
          onDismiss={() => setError(null)}
        />
      )}

      <CardGrid columns={3}>
        <Card title="Predicted Production" subtitle="RandomForestRegressor forecast">
          {pred ? (
            <>
              <div className="text-4xl font-bold text-gray-900 mb-2">{formatNumber(pred.predicted_production_stb_d)}</div>
              <div className="text-gray-500 text-sm">STB/d</div>
              <div className="mt-4 pt-4 border-t border-gray-200 flex items-center gap-2 text-sm text-gray-500">
                <BarChart2 className="w-4 h-4" aria-hidden="true" />
                <span>Model R²: {pred.model_info.production_model.training_metrics.train_r2?.toFixed(3) || 'N/A'}</span>
              </div>
            </>
          ) : (
            <Loading label="Generating prediction..." />
          )}
        </Card>

        <Card title="Rod Float Risk" subtitle="Continuous risk score [0, 1]">
          {pred ? (
            <RiskMetricCard label="Rod Float Risk" risk={pred.predicted_rod_float_risk} />
          ) : (
            <Loading />
          )}
        </Card>

        <Card title="Impact Loading Risk" subtitle="Continuous risk score [0, 1]">
          {pred ? (
            <RiskMetricCard label="Impact Loading Risk" risk={pred.predicted_impact_loading_risk} />
          ) : (
            <Loading />
          )}
        </Card>
      </CardGrid>

      <CardGrid columns={2}>
        <Card title="Custom Prediction Input" subtitle="Override default state parameters">
          <form onSubmit={handleCustomPredict} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="temperature_c" className="block text-sm font-medium text-gray-700 mb-1">
                  Temperature (°C)
                </label>
                <input
                  id="temperature_c"
                  type="number"
                  step="1"
                  value={customState.temperature_c || ''}
                  onChange={(e) => setCustomState({ ...customState, temperature_c: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="120"
                />
              </div>
              <div>
                <label htmlFor="viscosity_cp" className="block text-sm font-medium text-gray-700 mb-1">
                  Viscosity (cP)
                </label>
                <input
                  id="viscosity_cp"
                  type="number"
                  step="1"
                  value={customState.viscosity_cp || ''}
                  onChange={(e) => setCustomState({ ...customState, viscosity_cp: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="5000"
                />
              </div>
              <div>
                <label htmlFor="steam_rate_m3_d" className="block text-sm font-medium text-gray-700 mb-1">
                  Steam Rate (m³/d)
                </label>
                <input
                  id="steam_rate_m3_d"
                  type="number"
                  step="1"
                  value={customState.steam_rate_m3_d || ''}
                  onChange={(e) => setCustomState({ ...customState, steam_rate_m3_d: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="200"
                />
              </div>
              <div>
                <label htmlFor="steam_pressure_kpa" className="block text-sm font-medium text-gray-700 mb-1">
                  Steam Pressure (kPa)
                </label>
                <input
                  id="steam_pressure_kpa"
                  type="number"
                  step="1"
                  value={customState.steam_pressure_kpa || ''}
                  onChange={(e) => setCustomState({ ...customState, steam_pressure_kpa: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="4500"
                />
              </div>
              <div>
                <label htmlFor="css_cycle" className="block text-sm font-medium text-gray-700 mb-1">
                  CSS Cycle
                </label>
                <input
                  id="css_cycle"
                  type="number"
                  step="1"
                  value={customState.css_cycle || ''}
                  onChange={(e) => setCustomState({ ...customState, css_cycle: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="1"
                />
              </div>
              <div>
                <label htmlFor="srp_spm" className="block text-sm font-medium text-gray-700 mb-1">
                  SPM
                </label>
                <input
                  id="srp_spm"
                  type="number"
                  step="0.1"
                  value={customState.srp_spm || ''}
                  onChange={(e) => setCustomState({ ...customState, srp_spm: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="5.0"
                />
              </div>
              <div>
                <label htmlFor="stroke_length_m" className="block text-sm font-medium text-gray-700 mb-1">
                  Stroke Length (m)
                </label>
                <input
                  id="stroke_length_m"
                  type="number"
                  step="0.1"
                  value={customState.stroke_length_m || ''}
                  onChange={(e) => setCustomState({ ...customState, stroke_length_m: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="3.0"
                />
              </div>
              <div>
                <label htmlFor="pump_load_kn" className="block text-sm font-medium text-gray-700 mb-1">
                  Pump Load (kN)
                </label>
                <input
                  id="pump_load_kn"
                  type="number"
                  step="1"
                  value={customState.pump_load_kn || ''}
                  onChange={(e) => setCustomState({ ...customState, pump_load_kn: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="150"
                />
              </div>
              <div>
                <label htmlFor="fillage" className="block text-sm font-medium text-gray-700 mb-1">
                  Fillage
                </label>
                <input
                  id="fillage"
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={customState.fillage || ''}
                  onChange={(e) => setCustomState({ ...customState, fillage: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0.85"
                />
              </div>
              <div>
                <label htmlFor="pump_efficiency" className="block text-sm font-medium text-gray-700 mb-1">
                  Pump Efficiency
                </label>
                <input
                  id="pump_efficiency"
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={customState.pump_efficiency || ''}
                  onChange={(e) => setCustomState({ ...customState, pump_efficiency: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0.88"
                />
              </div>
              <div>
                <label htmlFor="vfd_frequency_hz" className="block text-sm font-medium text-gray-700 mb-1">
                  VFD Frequency (Hz)
                </label>
                <input
                  id="vfd_frequency_hz"
                  type="number"
                  step="1"
                  value={customState.vfd_frequency_hz || ''}
                  onChange={(e) => setCustomState({ ...customState, vfd_frequency_hz: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="40"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={manualPredictionMutation.isPending}
              className="w-full py-3 px-6 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {manualPredictionMutation.isPending ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" aria-hidden="true" />
                  Predicting...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" aria-hidden="true" />
                  Run Prediction
                </>
              )}
            </button>
          </form>
        </Card>

        <Card title="Model Information" subtitle="Training metrics and configuration">
          {pred ? (
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Production Forecaster</h4>
                <dl className="grid grid-cols-2 gap-2 text-sm">
                  <dt className="text-gray-500">Algorithm</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.production_model.type}</dd>
                  <dt className="text-gray-500">Estimators</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.production_model.n_estimators}</dd>
                  <dt className="text-gray-500">Features</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.production_model.features}</dd>
                  <dt className="text-gray-500">Train R²</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.production_model.training_metrics.train_r2?.toFixed(4) || 'N/A'}</dd>
                  <dt className="text-gray-500">Train MAE</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.production_model.training_metrics.train_mae?.toFixed(4) || 'N/A'}</dd>
                  <dt className="text-gray-500">Train RMSE</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.production_model.training_metrics.train_rmse?.toFixed(4) || 'N/A'}</dd>
                  <dt className="text-gray-500">Samples</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.production_model.training_metrics.n_samples || 'N/A'}</dd>
                </dl>
              </div>

              <div className="border-t border-gray-200 pt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Rod Float Risk Predictor</h4>
                <dl className="grid grid-cols-2 gap-2 text-sm">
                  <dt className="text-gray-500">Algorithm</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.rod_float_risk_model.type}</dd>
                  <dt className="text-gray-500">Estimators</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.rod_float_risk_model.n_estimators}</dd>
                  <dt className="text-gray-500">Features</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.rod_float_risk_model.features}</dd>
                  <dt className="text-gray-500">Train R²</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.rod_float_risk_model.training_metrics.train_r2?.toFixed(4) || 'N/A'}</dd>
                  <dt className="text-gray-500">Train MAE</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.rod_float_risk_model.training_metrics.train_mae?.toFixed(4) || 'N/A'}</dd>
                  <dt className="text-gray-500">Target</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.rod_float_risk_model.training_metrics.risk_target || 'N/A'}</dd>
                </dl>
              </div>

              <div className="border-t border-gray-200 pt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Impact Loading Risk Predictor</h4>
                <dl className="grid grid-cols-2 gap-2 text-sm">
                  <dt className="text-gray-500">Algorithm</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.impact_loading_risk_model.type}</dd>
                  <dt className="text-gray-500">Estimators</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.impact_loading_risk_model.n_estimators}</dd>
                  <dt className="text-gray-500">Features</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.impact_loading_risk_model.features}</dd>
                  <dt className="text-gray-500">Train R²</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.impact_loading_risk_model.training_metrics.train_r2?.toFixed(4) || 'N/A'}</dd>
                  <dt className="text-gray-500">Train MAE</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.impact_loading_risk_model.training_metrics.train_mae?.toFixed(4) || 'N/A'}</dd>
                  <dt className="text-gray-500">Target</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.impact_loading_risk_model.training_metrics.risk_target || 'N/A'}</dd>
                </dl>
              </div>
            </div>
          ) : (
            <Loading label="Loading model information..." />
          )}
        </Card>
      </CardGrid>

      {pred && (
        <Card title="Disclaimer" className="bg-amber-50 border-amber-200">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <p className="text-sm text-amber-800">{pred.disclaimer}</p>
          </div>
        </Card>
      )}
    </div>
  );
}