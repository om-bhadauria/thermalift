import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { clsx } from 'clsx';
import { apiClient } from '../api';
import { MetricCard, RiskMetricCard } from '../components/dashboard/MetricCard';
import { Card, CardGrid } from '../components/common/Card';
import { Loading, SkeletonCard } from '../components/common/Loading';
import { ErrorDisplay } from '../components/common/Error';
import { formatNumber, formatInteger, formatPercent, formatChange, getRiskLevel, formatTimestamp } from '../utils/format';
import type { SimulationResponse, OptimizationResponse } from '../types/api';
import { useWellsContext } from '../contexts/WellsContext';

interface SimulationData extends SimulationResponse {
  wellhead_pressure_kpa?: number;
}

interface OptimizationData extends OptimizationResponse {}

function TrendIcon({ change }: { change: { value: string; isPositive: boolean } }) {
  if (change.value === '—') return <Minus className="w-4 h-4 text-gray-400" />;
  return change.isPositive ? (
    <TrendingUp className="w-4 h-4 text-green-600" />
  ) : (
    <TrendingDown className="w-4 h-4 text-red-600" />
  );
}

function SimulationDataFetcher({ wellId }: { wellId: string }) {
  return useQuery<SimulationData, Error>({
    queryKey: ['simulation', wellId],
    queryFn: () =>
      apiClient.runSimulation({
        well_id: wellId,
        css_params: {
          steam_rate_m3_d: 200,
          steam_quality: 0.8,
          injection_days: 10,
          soak_days: 5,
          production_days: 90,
        },
        srp_params: {
          spm: 5.0,
          stroke_length_m: 3.0,
          vfd_frequency_hz: 40.0,
        },
        day_in_cycle: 5.0,
        cycle_num: 1,
        wellhead_pressure_kpa: 500.0,
      }),
    enabled: !!wellId,
    staleTime: 30000,
    retry: 1,
  });
}

function OptimizationDataFetcher({ wellId }: { wellId: string }) {
  return useQuery<OptimizationData, Error>({
    queryKey: ['optimization', wellId],
    queryFn: () =>
      apiClient.runOptimization({
        well_id: wellId,
        grid_resolution: 1,
        day_in_cycle: 5.0,
        cycle_num: 1,
        wellhead_pressure_kpa: 500.0,
        random_seed: 42,
      }),
    enabled: !!wellId,
    staleTime: 60000,
    retry: 1,
  });
}

export function Dashboard() {
  const { wells, selectedWell } = useWellsContext();
  const wellId = selectedWell || 'BW-001';
  const [error, setError] = useState<string | null>(null);

  const simulationQuery = SimulationDataFetcher({ wellId });
  const optimizationQuery = OptimizationDataFetcher({ wellId });

  if (simulationQuery.isLoading || optimizationQuery.isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <span className="px-3 py-1 bg-amber-50 border border-amber-200 rounded-lg text-sm font-medium text-amber-800">
            Synthetic/Demo Data
          </span>
        </div>
        <CardGrid columns={4}>
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </CardGrid>
        <CardGrid columns={2}>
          <SkeletonCard lines={4} />
          <SkeletonCard lines={4} />
        </CardGrid>
        <CardGrid columns={2}>
          <SkeletonCard lines={4} />
          <SkeletonCard lines={4} />
        </CardGrid>
      </div>
    );
  }

  if (simulationQuery.isError || optimizationQuery.isError) {
    const errMsg = simulationQuery.error?.message || optimizationQuery.error?.message || 'Failed to load dashboard data';
    return (
      <ErrorDisplay
        message={errMsg}
        title="Dashboard Error"
        onRetry={() => {
          simulationQuery.refetch();
          optimizationQuery.refetch();
        }}
        variant="card"
      />
    );
  }

  const sim = simulationQuery.data;
  const opt = optimizationQuery.data;

  if (!sim || !opt) {
    return (
      <ErrorDisplay
        message="No data available for this well"
        title="No Data"
        variant="card"
      />
    );
  }

  const prodChange = formatChange(sim.production_rate_stb_d, opt.baseline_comparison.baseline_production_stb_d);
  const steamChange = formatChange(sim.steam_rate_m3_d, opt.baseline_comparison.baseline_steam_m3_d);
  const rodFloatChange = formatChange(sim.rod_float_risk, opt.baseline_comparison.baseline_rod_float_risk);
  const impactChange = formatChange(sim.impact_loading_risk, opt.baseline_comparison.baseline_impact_loading_risk);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Well {wellId} — Real-time Physics Simulation & Optimization Overview</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-3 py-1 bg-amber-50 border border-amber-200 rounded-lg text-sm font-medium text-amber-800">
            Synthetic/Demo Data
          </span>
          <span className="px-3 py-1 bg-blue-50 border border-blue-200 rounded-lg text-sm font-medium text-blue-800">
            Prototype
          </span>
        </div>
      </div>

      <CardGrid columns={4}>
        <MetricCard
          label="Temperature"
          value={sim.temperature_c}
          unit="°C"
          trend={prodChange}
          icon={<TrendingUp className="w-6 h-6 text-gray-300" />}
        />
        <MetricCard
          label="Viscosity"
          value={sim.viscosity_cp}
          unit="cP"
        />
        <MetricCard
          label="Production"
          value={sim.production_rate_stb_d}
          unit="STB/d"
          trend={prodChange}
        />
        <MetricCard
          label="Steam Rate"
          value={sim.steam_rate_m3_d}
          unit="m³/d"
          trend={steamChange}
        />
      </CardGrid>

      <CardGrid columns={4}>
        <MetricCard
          label="Pump Load"
          value={sim.pump_load_kn}
          unit="kN"
        />
        <MetricCard
          label="Fillage"
          value={sim.fillage * 100}
          unit="%"
        />
        <MetricCard
          label="Pump Efficiency"
          value={sim.pump_efficiency * 100}
          unit="%"
        />
        <MetricCard
          label="SPM / Stroke"
          value={`${sim.srp_spm} / ${sim.stroke_length_m}`}
        />
      </CardGrid>

      <CardGrid columns={2}>
        <Card title="Risk Indicators" subtitle="SRP Failure Risk Assessment">
          <div className="space-y-4">
            <RiskMetricCard label="Rod Float Risk" risk={sim.rod_float_risk} />
            <RiskMetricCard label="Impact Loading Risk" risk={sim.impact_loading_risk} />
            <div className="pt-2 border-t border-gray-200">
              <p className="text-sm text-gray-500 mb-2">{'Risk Levels: Low (<30%) • Medium (30-60%) • High (>60%)'}</p>
              <div className="flex flex-wrap gap-2">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                  <span className="w-2 h-2 rounded-full bg-green-500" aria-hidden="true"></span>
                  Low
                </span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700">
                  <span className="w-2 h-2 rounded-full bg-yellow-500" aria-hidden="true"></span>
                  Medium
                </span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
                  <span className="w-2 h-2 rounded-full bg-red-500" aria-hidden="true"></span>
                  High
                </span>
              </div>
            </div>
          </div>
        </Card>

        <Card title="Optimization Summary" subtitle="Best Feasible Candidate vs Baseline">
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-gray-500">Objective Score</p>
                <p className="text-2xl font-bold text-gray-900">{opt.recommendation.objective_score.toFixed(4)}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500">Improvement</p>
                <p className={clsx('text-2xl font-bold', opt.baseline_comparison.objective_improvement >= 0 ? 'text-green-600' : 'text-red-600')}>
                  {formatPercent(opt.baseline_comparison.objective_improvement * 100, 2)}
                </p>
              </div>
            </div>

            <div className="border-t border-gray-200 pt-4">
              <p className="text-sm font-medium text-gray-500 mb-2">Baseline vs Optimized</p>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Production</span>
                  <span className="font-medium text-gray-900">
                    {formatNumber(opt.baseline_comparison.baseline_production_stb_d)} → {formatNumber(opt.baseline_comparison.optimized_production_stb_d)} STB/d
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Steam Rate</span>
                  <span className="font-medium text-gray-900">
                    {formatNumber(opt.baseline_comparison.baseline_steam_m3_d)} → {formatNumber(opt.baseline_comparison.optimized_steam_m3_d)} m³/d
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Rod Float Risk</span>
                  <span className="font-medium text-gray-900">
                    {formatPercent(opt.baseline_comparison.baseline_rod_float_risk * 100)} → {formatPercent(opt.baseline_comparison.optimized_rod_float_risk * 100)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Impact Loading Risk</span>
                  <span className="font-medium text-gray-900">
                    {formatPercent(opt.baseline_comparison.baseline_impact_loading_risk * 100)} → {formatPercent(opt.baseline_comparison.optimized_impact_loading_risk * 100)}
                  </span>
                </div>
              </div>
            </div>

            <div className="border-t border-gray-200 pt-4">
              <p className="text-sm font-medium text-gray-500 mb-2">Constraints Satisfied</p>
              <div className="flex flex-wrap gap-1.5">
                {opt.recommendation.constraints_satisfied.map((constraint, i) => (
                  <span key={i} className="px-2 py-1 bg-green-50 text-green-700 text-xs rounded border border-green-200">
                    {constraint.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </Card>
      </CardGrid>

      <Card title="Simulation Details" subtitle={formatTimestamp(sim.timestamp)}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-200">
                <th className="pb-2 font-medium">Parameter</th>
                <th className="pb-2 font-medium text-right">Value</th>
                <th className="pb-2 font-medium text-right">Unit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              <tr>
                <td className="py-2 text-gray-600">Well ID</td>
                <td className="py-2 text-right font-mono text-gray-900">{sim.well_id}</td>
                <td className="py-2 text-right">—</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">CSS Cycle</td>
                <td className="py-2 text-right font-mono text-gray-900">{sim.css_cycle}</td>
                <td className="py-2 text-right">—</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Temperature</td>
                <td className="py-2 text-right font-mono text-gray-900">{formatNumber(sim.temperature_c)}</td>
                <td className="py-2 text-right">°C</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Viscosity</td>
                <td className="py-2 text-right font-mono text-gray-900">{formatInteger(sim.viscosity_cp)}</td>
                <td className="py-2 text-right">cP</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Production Rate</td>
                <td className="py-2 text-right font-mono text-gray-900">{formatNumber(sim.production_rate_stb_d)}</td>
                <td className="py-2 text-right">STB/d</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Steam Rate</td>
                <td className="py-2 text-right font-mono text-gray-900">{formatNumber(sim.steam_rate_m3_d)}</td>
                <td className="py-2 text-right">m³/d</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Steam Pressure</td>
                <td className="py-2 text-right font-mono text-gray-900">{formatInteger(sim.steam_pressure_kpa)}</td>
                <td className="py-2 text-right">kPa</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Pump Load</td>
                <td className="py-2 text-right font-mono text-gray-900">{formatNumber(sim.pump_load_kn)}</td>
                <td className="py-2 text-right">kN</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Fillage</td>
                <td className="py-2 text-right font-mono text-gray-900">{(sim.fillage * 100).toFixed(1)}</td>
                <td className="py-2 text-right">%</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Pump Efficiency</td>
                <td className="py-2 text-right font-mono text-gray-900">{(sim.pump_efficiency * 100).toFixed(1)}</td>
                <td className="py-2 text-right">%</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">SPM</td>
                <td className="py-2 text-right font-mono text-gray-900">{sim.srp_spm}</td>
                <td className="py-2 text-right">strokes/min</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Stroke Length</td>
                <td className="py-2 text-right font-mono text-gray-900">{sim.stroke_length_m}</td>
                <td className="py-2 text-right">m</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">VFD Frequency</td>
                <td className="py-2 text-right font-mono text-gray-900">{sim.vfd_frequency_hz}</td>
                <td className="py-2 text-right">Hz</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Rod Float Risk</td>
                <td className="py-2 text-right font-mono text-gray-900">{formatPercent(sim.rod_float_risk * 100)}</td>
                <td className="py-2 text-right">—</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Impact Loading Risk</td>
                <td className="py-2 text-right font-mono text-gray-900">{formatPercent(sim.impact_loading_risk * 100)}</td>
                <td className="py-2 text-right">—</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Data Source</td>
                <td className="py-2 text-right font-mono text-gray-900">{sim.data_source}</td>
                <td className="py-2 text-right">—</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="mt-4 text-xs text-gray-500 italic">{sim.disclaimer}</p>
      </Card>
    </div>
  );
}