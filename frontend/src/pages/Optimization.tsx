import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Play, Loader2, TrendingUp, TrendingDown, Minus, Settings, CheckCircle, XCircle } from 'lucide-react';
import { apiClient } from '../api';
import { Card, CardGrid } from '../components/common/Card';
import { Badge, StatusBadge } from '../components/common/Badge';
import { Loading, SkeletonCard } from '../components/common/Loading';
import { ErrorDisplay, AlertBanner } from '../components/common/Error';
import { formatNumber, formatInteger, formatPercent, formatChange, formatTimestamp } from '../utils/format';
import type { OptimizationResponse, OptimizationRequest, WellConfig } from '../types/api';
import { clsx } from 'clsx';
import { useWellsContext } from '../contexts/WellsContext';

const DEFAULT_OPTIMIZATION_PARAMS = {
  grid_resolution: 1,
  day_in_cycle: 5.0,
  cycle_num: 1,
  wellhead_pressure_kpa: 500.0,
  random_seed: 42,
};

export function OptimizationPage() {
  const { wells, selectedWell } = useWellsContext();
  const wellId = selectedWell || 'BW-001';
  const [params, setParams] = useState(DEFAULT_OPTIMIZATION_PARAMS);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const optimizationQuery = useQuery<OptimizationResponse, Error>({
    queryKey: ['optimization', wellId, params],
    queryFn: () => apiClient.runOptimization({
      well_id: wellId,
      ...params,
    }),
    enabled: !!wellId,
    staleTime: 120000,
    retry: 1,
  });

  const manualOptimizationMutation = useMutation({
    mutationFn: (request: OptimizationRequest) => apiClient.runOptimization(request),
    onSuccess: (data) => {
      queryClient.setQueryData(['optimization', wellId, params], data);
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const handleParamChange = (field: keyof typeof params, value: number) => {
    setParams((prev) => ({ ...prev, [field]: value }));
  };

  const handleOptimize = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    manualOptimizationMutation.mutate({
      well_id: wellId,
      ...params,
    });
  };

  if (optimizationQuery.isLoading && !optimizationQuery.data) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Constrained Optimization</h1>
            <p className="text-gray-500 mt-1">Find optimal CSS & SRP parameters using grid search</p>
          </div>
          <span className="px-3 py-1 bg-amber-50 border border-amber-200 rounded-lg text-sm font-medium text-amber-800">
            Synthetic/Demo Data
          </span>
        </div>
        <CardGrid columns={2}>
          <SkeletonCard lines={6} />
          <SkeletonCard lines={6} />
        </CardGrid>
        <CardGrid columns={2}>
          <SkeletonCard lines={8} />
          <SkeletonCard lines={8} />
        </CardGrid>
      </div>
    );
  }

  if (optimizationQuery.isError && !optimizationQuery.data) {
    return (
      <ErrorDisplay
        message={optimizationQuery.error?.message || 'Failed to load optimization'}
        title="Optimization Error"
        onRetry={() => optimizationQuery.refetch()}
        variant="card"
      />
    );
  }

  const opt = optimizationQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Constrained Optimization</h1>
          <p className="text-gray-500 mt-1">Find optimal CSS & SRP parameters using deterministic grid search</p>
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

      <CardGrid columns={2}>
        <Card title="Optimization Parameters" subtitle="Configure search space and constraints">
          <form onSubmit={handleOptimize} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="grid_resolution" className="block text-sm font-medium text-gray-700 mb-1">
                  Grid Resolution
                </label>
                <input
                  id="grid_resolution"
                  type="number"
                  min="1"
                  max="5"
                  step="1"
                  value={params.grid_resolution}
                  onChange={(e) => handleParamChange('grid_resolution', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="mt-1 text-xs text-gray-500">1 = 256 evals, 2 = 4096 evals</p>
              </div>
              <div>
                <label htmlFor="random_seed" className="block text-sm font-medium text-gray-700 mb-1">
                  Random Seed
                </label>
                <input
                  id="random_seed"
                  type="number"
                  min="0"
                  max="999999"
                  step="1"
                  value={params.random_seed}
                  onChange={(e) => handleParamChange('random_seed', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="day_in_cycle" className="block text-sm font-medium text-gray-700 mb-1">
                  Day in Cycle
                </label>
                <input
                  id="day_in_cycle"
                  type="number"
                  min="0"
                  step="0.5"
                  value={params.day_in_cycle}
                  onChange={(e) => handleParamChange('day_in_cycle', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label htmlFor="cycle_num" className="block text-sm font-medium text-gray-700 mb-1">
                  Cycle Number
                </label>
                <input
                  id="cycle_num"
                  type="number"
                  min="1"
                  max="20"
                  step="1"
                  value={params.cycle_num}
                  onChange={(e) => handleParamChange('cycle_num', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <label htmlFor="wellhead_pressure" className="block text-sm font-medium text-gray-700 mb-1">
                Wellhead Pressure (kPa)
              </label>
              <input
                id="wellhead_pressure"
                type="number"
                min="0"
                max="5000"
                step="50"
                value={params.wellhead_pressure_kpa}
                onChange={(e) => handleParamChange('wellhead_pressure_kpa', Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div className="pt-4 border-t border-gray-200">
              <button
                type="submit"
                disabled={manualOptimizationMutation.isPending || optimizationQuery.isFetching}
                className="w-full py-3 px-6 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {manualOptimizationMutation.isPending || optimizationQuery.isFetching ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" aria-hidden="true" />
                    Running Optimization...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" aria-hidden="true" />
                    Run Optimization
                  </>
                )}
              </button>
            </div>
          </form>
        </Card>

        <Card title="Default Constraints & Weights" subtitle="Reference values used by optimizer">
          <div className="space-y-6">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Parameter Bounds (DEMO)</h4>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-900">Steam Rate</p>
                  <p className="text-gray-600">100 – 350 m³/d</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-900">Steam Quality</p>
                  <p className="text-gray-600">0.65 – 0.90</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-900">Injection Days</p>
                  <p className="text-gray-600">5 – 20 days</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-900">Soak Days</p>
                  <p className="text-gray-600">1 – 10 days</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-900">Production Days</p>
                  <p className="text-gray-600">30 – 150 days</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-900">SPM</p>
                  <p className="text-gray-600">2.0 – 8.0</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-900">Stroke Length</p>
                  <p className="text-gray-600">1.5 – 4.0 m</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-900">VFD Frequency</p>
                  <p className="text-gray-600">20 – 55 Hz</p>
                </div>
              </div>
            </div>

            <div className="border-t border-gray-200 pt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Objective Weights (PROTOTYPE)</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Production Weight</span>
                  <span className="font-medium text-gray-900">1.0</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Steam Penalty Weight</span>
                  <span className="font-medium text-gray-900">0.3</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Risk Penalty Weight</span>
                  <span className="font-medium text-gray-900">0.5</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Operating Cost Weight</span>
                  <span className="font-medium text-gray-900">0.2</span>
                </div>
              </div>
            </div>

            <div className="border-t border-gray-200 pt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Risk & Performance Limits</h4>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-900">Max Rod Float Risk</p>
                  <p className="text-gray-600">0.70</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-900">Max Impact Loading Risk</p>
                  <p className="text-gray-600">0.70</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-900">Min Fillage</p>
                  <p className="text-gray-600">0.30</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-900">Min Pump Efficiency</p>
                  <p className="text-gray-600">0.40</p>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </CardGrid>

      {opt && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <h2 className="text-xl font-semibold text-gray-900">Optimization Results</h2>
            <div className="flex items-center gap-3">
              <StatusBadge status={opt.recommendation.constraints_satisfied.length === 12 ? 'ok' : 'warning'} />
              <span className="text-sm text-gray-500">Completed: {formatTimestamp(new Date().toISOString())}</span>
            </div>
          </div>

          <CardGrid columns={4}>
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <p className="text-sm font-medium text-gray-500">Total Evaluated</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{opt.total_evaluated.toLocaleString()}</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <p className="text-sm font-medium text-gray-500">Feasible Candidates</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{opt.feasible_count.toLocaleString()}</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <p className="text-sm font-medium text-gray-500">Execution Time</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{opt.execution_time_seconds.toFixed(1)}s</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <p className="text-sm font-medium text-gray-500">Best Objective</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{opt.recommendation.objective_score.toFixed(4)}</p>
            </div>
          </CardGrid>

          <CardGrid columns={2}>
            <Card title="Recommended CSS Parameters" subtitle="Optimal steam operating conditions">
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">Steam Rate</p>
                    <p className="text-xl font-bold text-gray-900">{formatNumber(opt.recommendation.recommended_css.steam_rate_m3_d)} m³/d</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">Steam Quality</p>
                    <p className="text-xl font-bold text-gray-900">{opt.recommendation.recommended_css.steam_quality.toFixed(2)}</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">Injection Days</p>
                    <p className="text-xl font-bold text-gray-900">{formatNumber(opt.recommendation.recommended_css.injection_days)} d</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">Soak Days</p>
                    <p className="text-xl font-bold text-gray-900">{formatNumber(opt.recommendation.recommended_css.soak_days)} d</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg col-span-2">
                    <p className="text-sm text-gray-500">Production Days</p>
                    <p className="text-xl font-bold text-gray-900">{formatNumber(opt.recommendation.recommended_css.production_days)} d</p>
                  </div>
                </div>
              </div>
            </Card>

            <Card title="Recommended SRP Parameters" subtitle="Optimal pump operating conditions">
              <div className="space-y-3">
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">SPM</p>
                    <p className="text-xl font-bold text-gray-900">{opt.recommendation.recommended_srp.spm}</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">Stroke Length</p>
                    <p className="text-xl font-bold text-gray-900">{opt.recommendation.recommended_srp.stroke_length_m} m</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">VFD Frequency</p>
                    <p className="text-xl font-bold text-gray-900">{opt.recommendation.recommended_srp.vfd_frequency_hz} Hz</p>
                  </div>
                </div>
              </div>
            </Card>
          </CardGrid>

          <Card title="Baseline vs Optimized Comparison" subtitle="Honest comparison — negative changes shown in red">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b border-gray-200">
                    <th className="pb-3 font-medium w-1/3">Metric</th>
                    <th className="pb-3 font-medium text-right w-1/3">Baseline</th>
                    <th className="pb-3 font-medium text-right w-1/3">Optimized</th>
                    <th className="pb-3 font-medium text-right w-1/3">Change</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <ComparisonRow
                    label="Production"
                    baseline={opt.baseline_comparison.baseline_production_stb_d}
                    optimized={opt.baseline_comparison.optimized_production_stb_d}
                    format={formatNumber}
                    unit="STB/d"
                    higherIsBetter={true}
                  />
                  <ComparisonRow
                    label="Steam Rate"
                    baseline={opt.baseline_comparison.baseline_steam_m3_d}
                    optimized={opt.baseline_comparison.optimized_steam_m3_d}
                    format={formatNumber}
                    unit="m³/d"
                    higherIsBetter={false}
                  />
                  <ComparisonRow
                    label="Rod Float Risk"
                    baseline={opt.baseline_comparison.baseline_rod_float_risk}
                    optimized={opt.baseline_comparison.optimized_rod_float_risk}
                    format={(v) => formatPercent(v * 100)}
                    unit=""
                    higherIsBetter={false}
                  />
                  <ComparisonRow
                    label="Impact Loading Risk"
                    baseline={opt.baseline_comparison.baseline_impact_loading_risk}
                    optimized={opt.baseline_comparison.optimized_impact_loading_risk}
                    format={(v) => formatPercent(v * 100)}
                    unit=""
                    higherIsBetter={false}
                  />
                  <ComparisonRow
                    label="Objective Score"
                    baseline={opt.baseline_comparison.baseline_objective_score}
                    optimized={opt.baseline_comparison.optimized_objective_score}
                    format={(v) => v.toFixed(4)}
                    unit=""
                    higherIsBetter={true}
                  />
                </tbody>
              </table>
            </div>
            </Card>

            <Card title="Optimization Explanation" subtitle="Why this candidate was selected">
              <div className="prose prose-sm max-w-none text-gray-700">
                <p>{opt.recommendation.explanation}</p>
              </div>
            </Card>

            <Card title="Constraint Satisfaction" subtitle="All constraints evaluated for best candidate">
              <div className="flex flex-wrap gap-2">
                {opt.recommendation.constraints_satisfied.map((constraint, i) => (
                  <Badge key={i} variant="success" size="sm">
                    <CheckCircle className="w-3 h-3 mr-1" aria-hidden="true" />
                    {constraint.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </Badge>
                ))}
              </div>
            </Card>

            <Card title="Best Candidate Details" subtitle="Full candidate evaluation data">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <tbody className="divide-y divide-gray-100">
                    <tr>
                      <td className="py-2 text-gray-600">CSS Steam Rate</td>
                      <td className="py-2 text-right font-mono text-gray-900">{formatNumber(opt.best_candidate.css_params.steam_rate_m3_d)} m³/d</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">CSS Steam Quality</td>
                      <td className="py-2 text-right font-mono text-gray-900">{opt.best_candidate.css_params.steam_quality.toFixed(2)}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">CSS Injection Days</td>
                      <td className="py-2 text-right font-mono text-gray-900">{formatNumber(opt.best_candidate.css_params.injection_days)} d</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">CSS Soak Days</td>
                      <td className="py-2 text-right font-mono text-gray-900">{formatNumber(opt.best_candidate.css_params.soak_days)} d</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">CSS Production Days</td>
                      <td className="py-2 text-right font-mono text-gray-900">{formatNumber(opt.best_candidate.css_params.production_days)} d</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">SRP SPM</td>
                      <td className="py-2 text-right font-mono text-gray-900">{opt.best_candidate.srp_params.spm}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">SRP Stroke Length</td>
                      <td className="py-2 text-right font-mono text-gray-900">{opt.best_candidate.srp_params.stroke_length_m} m</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">SRP VFD Frequency</td>
                      <td className="py-2 text-right font-mono text-gray-900">{opt.best_candidate.srp_params.vfd_frequency_hz} Hz</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Predicted Production</td>
                      <td className="py-2 text-right font-mono text-gray-900">{formatNumber(opt.best_candidate.predicted_production_stb_d)} STB/d</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Predicted Rod Float Risk</td>
                      <td className="py-2 text-right font-mono text-gray-900">{formatPercent(opt.best_candidate.predicted_rod_float_risk * 100)}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Predicted Impact Loading Risk</td>
                      <td className="py-2 text-right font-mono text-gray-900">{formatPercent(opt.best_candidate.predicted_impact_loading_risk * 100)}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Steam Usage</td>
                      <td className="py-2 text-right font-mono text-gray-900">{formatNumber(opt.best_candidate.steam_usage_m3_d)} m³/d</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Steam Intensity</td>
                      <td className="py-2 text-right font-mono text-gray-900">{opt.best_candidate.steam_intensity.toFixed(3)}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Objective Score</td>
                      <td className="py-2 text-right font-mono text-gray-900">{opt.best_candidate.objective_score.toFixed(4)}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Feasible</td>
                      <td className="py-2 text-right font-mono text-gray-900">{opt.best_candidate.is_feasible ? 'Yes' : 'No'}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Constraint Violations</td>
                      <td className="py-2 text-right font-mono text-gray-900">{opt.best_candidate.constraint_violations.length > 0 ? opt.best_candidate.constraint_violations.join(', ') : 'None'}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="mt-4 text-xs text-gray-500 italic">{opt.disclaimer}</p>
            </Card>
          </div>
        )}

      {!opt && !manualOptimizationMutation.isPending && !optimizationQuery.isFetching && (
        <Card>
          <Loading label="Configure parameters and click Run Optimization to see results" />
        </Card>
      )}
    </div>
  );
}

interface ComparisonRowProps {
  label: string;
  baseline: number;
  optimized: number;
  format: (v: number) => string;
  unit: string;
  higherIsBetter: boolean;
}

function ComparisonRow({ label, baseline, optimized, format, unit, higherIsBetter }: ComparisonRowProps) {
  const change = formatChange(optimized, baseline);
  const isImprovement = higherIsBetter ? change.isPositive : !change.isPositive;

  return (
    <tr>
      <td className="py-3 text-gray-700 font-medium">{label}</td>
      <td className="py-3 text-right font-mono text-gray-900">{format(baseline)} {unit}</td>
      <td className="py-3 text-right font-mono text-gray-900">{format(optimized)} {unit}</td>
      <td className="py-3 text-right">
        <span className={clsx('font-medium', isImprovement ? 'text-green-600' : 'text-red-600')}>
          {change.value}
        </span>
      </td>
    </tr>
  );
}