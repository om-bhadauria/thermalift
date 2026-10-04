import { AlertTriangle, Database, FlaskConical, Shield, Zap, BarChart2 } from 'lucide-react';
import { Card } from '../components/common/Card';

const features = [
  {
    icon: FlaskConical,
    title: 'Physics-Informed Simulation',
    description: 'Analytical thermal models coupled with SRP dynamics for realistic wellbore simulation.',
  },
  {
    icon: Zap,
    title: 'ML Forecasting & Risk',
    description: 'RandomForest models trained on synthetic data for production forecasting and failure risk prediction.',
  },
  {
    icon: Database,
    title: 'Constrained Optimization',
    description: 'Deterministic grid search over CSS & SRP parameters with explicit constraint validation.',
  },
  {
    icon: BarChart2,
    title: 'Transparent Objectives',
    description: 'Multi-objective scoring with documented weights — production, steam, risk, operating cost.',
  },
  {
    icon: Shield,
    title: 'Explicit Constraints',
    description: 'All parameter bounds, risk limits, and performance thresholds clearly defined and enforced.',
  },
  {
    icon: AlertTriangle,
    title: 'Synthetic Data Only',
    description: 'All results based on synthetic/demo data — not real Baghewala/OIL field measurements.',
  },
];

export function AboutPage() {
  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-blue-600 mb-6">
          <span className="text-3xl font-bold text-white">T</span>
        </div>
        <h1 className="text-4xl font-bold text-gray-900">THERMALIFT</h1>
        <p className="mt-3 text-lg text-gray-600">AI-Driven Digital Twin for CSS & SRP Optimization</p>
        <p className="mt-2 text-sm text-gray-500">Version 1.0.0 — Prototype</p>
      </div>

      <Card className="bg-amber-50 border-amber-200">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div className="prose prose-lg max-w-none text-amber-800">
            <h3 className="font-semibold mb-3">Critical Data Policy Notice</h3>
            <p className="mb-3">
              <strong>This prototype uses physics-informed synthetic/demo data exclusively.</strong>
              No real Baghewala field measurements or Oil India operational data have been used.
            </p>
            <p className="mb-3">
              All physics models, ML predictions, optimization results, and recommendations are
              <strong>prototype outputs generated from synthetic data</strong>. They are not validated
              against real field operations and must not be used for actual field decisions.
            </p>
            <p>
              The optimization weights, constraint bounds, and parameter ranges are
              <strong>DEMO/PROTOTYPE assumptions</strong>, not calibrated to real field economics
              or actual operating limits.
            </p>
          </div>
        </div>
      </Card>

      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">System Capabilities</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <Card key={i} className="h-full">
              <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center mb-4">
                <feature.icon className="w-6 h-6 text-blue-600" aria-hidden="true" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-gray-600">{feature.description}</p>
            </Card>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Architecture</h2>
        <Card>
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Backend (FastAPI)</h3>
              <ul className="space-y-2 text-gray-700">
                <li><strong>/api/v1/health</strong> — Service health and data policy</li>
                <li><strong>/api/v1/simulation</strong> — Physics simulation (PipelineEngine)</li>
                <li><strong>/api/v1/prediction</strong> — ML production & risk forecasts</li>
                <li><strong>/api/v1/optimization</strong> — Constrained grid search optimizer</li>
                <li><strong>/api/v1/models/status</strong> — ML model status and metrics</li>
              </ul>
            </div>
            <div className="border-t border-gray-200 pt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Frontend (React + TypeScript)</h3>
              <ul className="space-y-2 text-gray-700">
                <li>Dashboard — Real-time simulation & optimization overview</li>
                <li>Well Simulation — Interactive physics parameter configuration</li>
                <li>Prediction — ML forecasting with custom input states</li>
                <li>Optimization — Constrained parameter search with baseline comparison</li>
                <li>Model Status — ML model health and training metrics</li>
              </ul>
            </div>
            <div className="border-t border-gray-200 pt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Data Flow</h3>
              <p className="text-gray-700 mb-2">
                User inputs → FastAPI validation → Existing physics/ML services →
                Structured response with disclaimers → React visualization
              </p>
              <p className="text-gray-600 text-sm">
                The frontend contains no physics formulas, ML calculations, or optimization logic.
                All computations remain in the backend services.
              </p>
            </div>
          </div>
        </Card>
      </div>

      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Limitations & Known Issues</h2>
        <Card>
          <ul className="space-y-3 text-gray-700 list-disc list-inside">
            <li>All data is synthetic/demo — not real field data</li>
            <li>{'Optimization uses grid search; resolution >3 becomes slow'}</li>
            <li>Weights and constraints are prototype assumptions</li>
            <li>Prediction endpoint requires complete feature set (including targets)</li>
            <li>Physics model uses random noise; results vary between runs</li>
            <li>No authentication, rate limiting, or production hardening</li>
          </ul>
        </Card>
      </div>

      <div className="text-center py-8 border-t border-gray-200">
        <p className="text-gray-500">
          THERMALIFT Prototype — Built for SIH 2026
        </p>
        <p className="text-sm text-gray-400 mt-1">
          Synthetic/Demo Data — Not for production use
        </p>
      </div>
    </div>
  );
}