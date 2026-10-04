import { clsx } from 'clsx';
import { formatNumber, formatInteger, formatRisk, getRiskColor, getRiskLevel } from '../../utils/format';

interface MetricCardProps {
  label: string;
  value: number | string;
  unit?: string;
  trend?: { value: string; isPositive: boolean };
  status?: 'normal' | 'warning' | 'critical';
  className?: string;
  icon?: React.ReactNode;
}

export function MetricCard({ label, value, unit, trend, status = 'normal', className, icon }: MetricCardProps) {
  const statusColors = {
    normal: 'text-gray-900',
    warning: 'text-yellow-700',
    critical: 'text-red-700',
  };

  const displayValue = typeof value === 'number' ? formatNumber(value) : value;

  return (
    <div className={clsx('bg-white rounded-lg border border-gray-200 p-5', className)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{label}</p>
          <div className="flex items-baseline gap-1 mt-1">
            <span className={clsx('text-2xl font-semibold', statusColors[status])}>
              {displayValue}
            </span>
            {unit && <span className="text-gray-500 mt-1">{unit}</span>}
          </div>
          {trend && (
            <div className={clsx('flex items-center gap-1 mt-2 text-sm', trend.isPositive ? 'text-green-600' : 'text-red-600')}>
              <span>{trend.value}</span>
              <span className="text-gray-400">vs baseline</span>
            </div>
          )}
        </div>
        {icon && <div className="text-gray-300">{icon}</div>}
      </div>
    </div>
  );
}

interface RiskMetricCardProps {
  label: string;
  risk: number;
  className?: string;
}

export function RiskMetricCard({ label, risk, className }: RiskMetricCardProps) {
  const level = getRiskLevel(risk);
  const colorClass = getRiskColor(risk);

  return (
    <div className={clsx('bg-white rounded-lg border border-gray-200 p-5', className)}>
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <div className="flex items-center justify-between mt-2">
        <div>
          <span className="text-3xl font-bold text-gray-900">{formatRisk(risk)}</span>
          <div className={clsx('mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium', colorClass)}>
            {level.charAt(0).toUpperCase() + level.slice(1)} Risk
          </div>
        </div>
        <div className="w-20 h-20 relative">
          <svg viewBox="0 0 80 80" className="w-full h-full transform -rotate-90">
            <circle
              cx="40"
              cy="40"
              r="32"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="6"
            />
            <circle
              cx="40"
              cy="40"
              r="32"
              fill="none"
              stroke={level === 'low' ? '#22c55e' : level === 'medium' ? '#eab308' : '#ef4444'}
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={`${(risk * 100).toFixed(0)} 100`}
              className="transition-all duration-500"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs font-medium text-gray-500">{Math.round(risk * 100)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}