import { useQuery } from '@tanstack/react-query';
import { Database, CheckCircle, XCircle, Zap, BarChart2, AlertTriangle, Loader2 } from 'lucide-react';
import { apiClient } from '../api';
import { Card, CardGrid } from '../components/common/Card';
import { Badge, StatusBadge } from '../components/common/Badge';
import { Loading, SkeletonCard } from '../components/common/Loading';
import { ErrorDisplay } from '../components/common/Error';
import { formatNumber, formatPercent } from '../utils/format';
import type { ModelStatusResponse, PredictionResponse } from '../types/api';
import { useWellsContext } from '../contexts/WellsContext';

export function ModelsPage() {
  const { selectedWell } = useWellsContext();
  const wellId = selectedWell || 'BW-001';
  
  const modelStatusQuery = useQuery<ModelStatusResponse, Error>({
    queryKey: ['modelStatus'],
    queryFn: () => apiClient.getModelStatus(),
    staleTime: 60000,
    retry: 1,
  });

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
      },
    }),
    enabled: !!wellId,
    staleTime: 60000,
    retry: 1,
  });

  if (modelStatusQuery.isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Model Status</h1>
          <span className="px-3 py-1 bg-amber-50 border border-amber-200 rounded-lg text-sm font-medium text-amber-800">
            Synthetic/Demo Data
          </span>
        </div>
        <CardGrid columns={3}>
          <SkeletonCard lines={4} />
          <SkeletonCard lines={4} />
          <SkeletonCard lines={4} />
        </CardGrid>
      </div>
    );
  }

  if (modelStatusQuery.isError) {
    return (
      <ErrorDisplay
        message={modelStatusQuery.error?.message || 'Failed to load model status'}
        title="Model Status Error"
        onRetry={() => modelStatusQuery.refetch()}
        variant="card"
      />
    );
  }

  const status = modelStatusQuery.data;
  const pred = predictionQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Model Status</h1>
        <div className="flex items-center gap-3">
          <StatusBadge status={status?.initialized ? 'ok' : 'warning'} />
          <span className="px-3 py-1 bg-amber-50 border border-amber-200 rounded-lg text-sm font-medium text-amber-800">
            Synthetic/Demo Data
          </span>
        </div>
      </div>

      <CardGrid columns={3}>
        <Card title="Production Forecaster" subtitle="RandomForestRegressor">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center">
                <Zap className="w-6 h-6 text-blue-600" aria-hidden="true" />
              </div>
              <div>
                <StatusBadge status={status?.production_forecaster ? 'ok' : 'error'} />
                <p className="text-sm text-gray-500">RandomForestRegressor</p>
              </div>
            </div>
            {pred && (
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-500">Estimators</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.production_model.n_estimators}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Features</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.production_model.features}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Train R²</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.production_model.training_metrics.train_r2?.toFixed(4) || 'N/A'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Train MAE</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.production_model.training_metrics.train_mae?.toFixed(4) || 'N/A'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Train Samples</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.production_model.training_metrics.n_samples?.toLocaleString() || 'N/A'}</dd>
                </div>
              </dl>
            )}
          </div>
        </Card>

        <Card title="Rod Float Risk Predictor" subtitle="RandomForestRegressor">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg bg-red-100 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600" aria-hidden="true" />
              </div>
              <div>
                <StatusBadge status={status?.rod_float_predictor ? 'ok' : 'error'} />
                <p className="text-sm text-gray-500">RandomForestRegressor</p>
              </div>
            </div>
            {pred && (
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-500">Estimators</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.rod_float_risk_model.n_estimators}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Features</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.rod_float_risk_model.features}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Train R²</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.rod_float_risk_model.training_metrics.train_r2?.toFixed(4) || 'N/A'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Train MAE</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.rod_float_risk_model.training_metrics.train_mae?.toFixed(4) || 'N/A'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Target</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.rod_float_risk_model.training_metrics.risk_target || 'N/A'}</dd>
                </div>
              </dl>
            )}
          </div>
        </Card>

        <Card title="Impact Loading Risk Predictor" subtitle="RandomForestRegressor">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg bg-orange-100 flex items-center justify-center">
                <BarChart2 className="w-6 h-6 text-orange-600" aria-hidden="true" />
              </div>
              <div>
                <StatusBadge status={status?.impact_loading_predictor ? 'ok' : 'error'} />
                <p className="text-sm text-gray-500">RandomForestRegressor</p>
              </div>
            </div>
            {pred && (
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-500">Estimators</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.impact_loading_risk_model.n_estimators}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Features</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.impact_loading_risk_model.features}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Train R²</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.impact_loading_risk_model.training_metrics.train_r2?.toFixed(4) || 'N/A'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Train MAE</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.impact_loading_risk_model.training_metrics.train_mae?.toFixed(4) || 'N/A'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Target</dt>
                  <dd className="font-medium text-gray-900">{pred.model_info.impact_loading_risk_model.training_metrics.risk_target || 'N/A'}</dd>
                </div>
              </dl>
            )}
          </div>
        </Card>
      </CardGrid>

      {pred && (
        <Card title="Current Predictions (Sample)" subtitle="Based on default input state">
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-500">Production</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{formatNumber(pred.predicted_production_stb_d)} STB/d</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-500">Rod Float Risk</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{formatPercent(pred.predicted_rod_float_risk * 100)}</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-500">Impact Loading Risk</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{formatPercent(pred.predicted_impact_loading_risk * 100)}</p>
            </div>
          </div>
        </Card>
      )}

      <Card title="Data Policy" className="bg-amber-50 border-amber-200">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div className="prose prose-sm max-w-none text-amber-800">
            <p className="font-medium mb-2">Synthetic/Demo Data Only</p>
            <p>All models are trained on physics-informed synthetic/demo data. Predictions are prototype outputs and are <strong>not validated against real Baghewala/OIL field operations</strong>.</p>
            <p className="mt-2">Do not use these results for actual field decisions.</p>
          </div>
        </div>
      </Card>
    </div>
  );
}