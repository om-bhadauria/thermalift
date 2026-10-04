import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Play, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { apiClient } from '../api';
import { Card, CardGrid } from '../components/common/Card';
import { Loading } from '../components/common/Loading';
import { ErrorDisplay, AlertBanner } from '../components/common/Error';
import { MetricCard } from '../components/dashboard/MetricCard';
import { formatNumber, formatInteger, formatPercent, formatTimestamp } from '../utils/format';
import type { SimulationRequest, SimulationResponse, WellConfig } from '../types/api';
import { useWellsContext } from '../contexts/WellsContext';

const DEFAULT_CSS_PARAMS = {
  steam_rate_m3_d: 200,
  steam_quality: 0.8,
  injection_days: 10,
  soak_days: 5,
  production_days: 90,
};

const DEFAULT_SRP_PARAMS = {
  spm: 5.0,
  stroke_length_m: 3.0,
  vfd_frequency_hz: 40.0,
};

export function SimulationPage() {
  const { wells, selectedWell } = useWellsContext();
  const wellId = selectedWell || 'BW-001';
  const [cssParams, setCssParams] = useState(DEFAULT_CSS_PARAMS);
  const [srpParams, setSrpParams] = useState(DEFAULT_SRP_PARAMS);
  const [dayInCycle, setDayInCycle] = useState(5.0);
  const [cycleNum, setCycleNum] = useState(1);
  const [wellheadPressure, setWellheadPressure] = useState(500.0);
  const [lastResult, setLastResult] = useState<SimulationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const simulationMutation = useMutation({
    mutationFn: (request: SimulationRequest) => apiClient.runSimulation(request),
    onSuccess: (data) => {
      setLastResult(data);
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message);
      setLastResult(null);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    simulationMutation.mutate({
      well_id: wellId,
      css_params: cssParams,
      srp_params: srpParams,
      day_in_cycle: dayInCycle,
      cycle_num: cycleNum,
      wellhead_pressure_kpa: wellheadPressure,
    });
  };

  const handleCssChange = (field: keyof typeof cssParams, value: number) => {
    setCssParams((prev) => ({ ...prev, [field]: value }));
  };

  const handleSrpChange = (field: keyof typeof srpParams, value: number) => {
    setSrpParams((prev) => ({ ...prev, [field]: value }));
  };

  const currentWell = wells.find((w) => w.well_id === wellId);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Well Simulation</h1>
          <p className="text-gray-500 mt-1">Run physics-based simulation for CSS & SRP operating parameters</p>
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
        <Card title="CSS Steam Parameters" subtitle="Cyclic Steam Stimulation operating parameters">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="steam_rate" className="block text-sm font-medium text-gray-700 mb-1">
                  Steam Rate (m³/d)
                </label>
                <input
                  id="steam_rate"
                  type="number"
                  min="100"
                  max="350"
                  step="10"
                  value={cssParams.steam_rate_m3_d}
                  onChange={(e) => handleCssChange('steam_rate_m3_d', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label htmlFor="steam_quality" className="block text-sm font-medium text-gray-700 mb-1">
                  Steam Quality
                </label>
                <input
                  id="steam_quality"
                  type="number"
                  min="0.65"
                  max="0.9"
                  step="0.01"
                  value={cssParams.steam_quality}
                  onChange={(e) => handleCssChange('steam_quality', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label htmlFor="injection_days" className="block text-sm font-medium text-gray-700 mb-1">
                  Injection Days
                </label>
                <input
                  id="injection_days"
                  type="number"
                  min="5"
                  max="20"
                  step="1"
                  value={cssParams.injection_days}
                  onChange={(e) => handleCssChange('injection_days', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label htmlFor="soak_days" className="block text-sm font-medium text-gray-700 mb-1">
                  Soak Days
                </label>
                <input
                  id="soak_days"
                  type="number"
                  min="1"
                  max="10"
                  step="1"
                  value={cssParams.soak_days}
                  onChange={(e) => handleCssChange('soak_days', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label htmlFor="production_days" className="block text-sm font-medium text-gray-700 mb-1">
                  Production Days
                </label>
                <input
                  id="production_days"
                  type="number"
                  min="30"
                  max="150"
                  step="5"
                  value={cssParams.production_days}
                  onChange={(e) => handleCssChange('production_days', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </form>
        </Card>

        <Card title="SRP Parameters" subtitle="Sucker Rod Pump operating parameters">
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label htmlFor="spm" className="block text-sm font-medium text-gray-700 mb-1">
                  SPM (strokes/min)
                </label>
                <input
                  id="spm"
                  type="number"
                  min="2"
                  max="8"
                  step="0.1"
                  value={srpParams.spm}
                  onChange={(e) => handleSrpChange('spm', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label htmlFor="stroke_length" className="block text-sm font-medium text-gray-700 mb-1">
                  Stroke Length (m)
                </label>
                <input
                  id="stroke_length"
                  type="number"
                  min="1.5"
                  max="4.0"
                  step="0.1"
                  value={srpParams.stroke_length_m}
                  onChange={(e) => handleSrpChange('stroke_length_m', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label htmlFor="vfd_frequency" className="block text-sm font-medium text-gray-700 mb-1">
                  VFD Frequency (Hz)
                </label>
                <input
                  id="vfd_frequency"
                  type="number"
                  min="20"
                  max="55"
                  step="1"
                  value={srpParams.vfd_frequency_hz}
                  onChange={(e) => handleSrpChange('vfd_frequency_hz', Number(e.target.value))}
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
                  value={dayInCycle}
                  onChange={(e) => setDayInCycle(Number(e.target.value))}
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
                  value={cycleNum}
                  onChange={(e) => setCycleNum(Number(e.target.value))}
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
                value={wellheadPressure}
                onChange={(e) => setWellheadPressure(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div className="pt-4 border-t border-gray-200">
              <button
                type="submit"
                form="simulation-form"
                disabled={simulationMutation.isPending}
                className="w-full py-3 px-6 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {simulationMutation.isPending ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" aria-hidden="true" />
                    Running Simulation...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" aria-hidden="true" />
                    Run Simulation
                  </>
                )}
              </button>
            </div>
          </div>
        </Card>
      </CardGrid>

      <form id="simulation-form" onSubmit={handleSubmit} className="hidden">
        {/* Hidden form for button submission */}
      </form>

      {lastResult && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Simulation Results</h2>
            <span className="text-sm text-gray-500">Completed: {formatTimestamp(lastResult.timestamp)}</span>
          </div>

          <CardGrid columns={4}>
            <MetricCard label="Temperature" value={lastResult.temperature_c} unit="°C" />
            <MetricCard label="Viscosity" value={lastResult.viscosity_cp} unit="cP" />
            <MetricCard label="Production" value={lastResult.production_rate_stb_d} unit="STB/d" />
            <MetricCard label="Steam Rate" value={lastResult.steam_rate_m3_d} unit="m³/d" />
          </CardGrid>

          <CardGrid columns={4}>
            <MetricCard label="Pump Load" value={lastResult.pump_load_kn} unit="kN" />
            <MetricCard label="Fillage" value={lastResult.fillage * 100} unit="%" />
            <MetricCard label="Pump Efficiency" value={lastResult.pump_efficiency * 100} unit="%" />
            <MetricCard label="SPM" value={lastResult.srp_spm} unit="strokes/min" />
          </CardGrid>

          <CardGrid columns={2}>
            <Card title="Risk Assessment" subtitle="SRP failure risk indicators">
              <div className="space-y-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Rod Float Risk</p>
                  <div className="mt-1 flex items-center gap-3">
                    <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-red-500 rounded-full transition-all duration-500"
                        style={{ width: `${lastResult.rod_float_risk * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-900 w-16 text-right">
                      {formatPercent(lastResult.rod_float_risk * 100)}
                    </span>
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Impact Loading Risk</p>
                  <div className="mt-1 flex items-center gap-3">
                    <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-orange-500 rounded-full transition-all duration-500"
                        style={{ width: `${lastResult.impact_loading_risk * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-900 w-16 text-right">
                      {formatPercent(lastResult.impact_loading_risk * 100)}
                    </span>
                  </div>
                </div>
              </div>
            </Card>

            <Card title="Full Simulation Output" subtitle={formatTimestamp(lastResult.timestamp)}>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <tbody className="divide-y divide-gray-100">
                    <tr>
                      <td className="py-2 text-gray-600">Well ID</td>
                      <td className="py-2 text-right font-mono text-gray-900">{lastResult.well_id}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">CSS Cycle</td>
                      <td className="py-2 text-right font-mono text-gray-900">{lastResult.css_cycle}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Day in Cycle</td>
                      <td className="py-2 text-right font-mono text-gray-900">{dayInCycle}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Temperature</td>
                      <td className="py-2 text-right font-mono text-gray-900">{formatNumber(lastResult.temperature_c)} °C</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Viscosity</td>
                      <td className="py-2 text-right font-mono text-gray-900">{formatInteger(lastResult.viscosity_cp)} cP</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Production Rate</td>
                      <td className="py-2 text-right font-mono text-gray-900">{formatNumber(lastResult.production_rate_stb_d)} STB/d</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Steam Rate</td>
                      <td className="py-2 text-right font-mono text-gray-900">{formatNumber(lastResult.steam_rate_m3_d)} m³/d</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Steam Pressure</td>
                      <td className="py-2 text-right font-mono text-gray-900">{formatInteger(lastResult.steam_pressure_kpa)} kPa</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Pump Load</td>
                      <td className="py-2 text-right font-mono text-gray-900">{formatNumber(lastResult.pump_load_kn)} kN</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Fillage</td>
                      <td className="py-2 text-right font-mono text-gray-900">{(lastResult.fillage * 100).toFixed(1)}%</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Pump Efficiency</td>
                      <td className="py-2 text-right font-mono text-gray-900">{(lastResult.pump_efficiency * 100).toFixed(1)}%</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">SPM</td>
                      <td className="py-2 text-right font-mono text-gray-900">{lastResult.srp_spm}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Stroke Length</td>
                      <td className="py-2 text-right font-mono text-gray-900">{lastResult.stroke_length_m} m</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">VFD Frequency</td>
                      <td className="py-2 text-right font-mono text-gray-900">{lastResult.vfd_frequency_hz} Hz</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Rod Float Risk</td>
                      <td className="py-2 text-right font-mono text-gray-900">{formatPercent(lastResult.rod_float_risk * 100)}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Impact Loading Risk</td>
                      <td className="py-2 text-right font-mono text-gray-900">{formatPercent(lastResult.impact_loading_risk * 100)}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-gray-600">Data Source</td>
                      <td className="py-2 text-right font-mono text-gray-900">{lastResult.data_source}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="mt-4 text-xs text-gray-500 italic">{lastResult.disclaimer}</p>
            </Card>
          </CardGrid>
        </div>
      )}

      {!lastResult && !simulationMutation.isPending && (
        <Card>
          <Loading label="Configure parameters and click Run Simulation to see results" />
        </Card>
      )}
    </div>
  );
}