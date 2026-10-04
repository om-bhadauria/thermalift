export function formatNumber(value: number, decimals = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '—';
  }
  return value.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatInteger(value: number): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '—';
  }
  return Math.round(value).toLocaleString();
}

export function formatPercent(value: number, decimals = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '—';
  }
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
}

export function formatRisk(value: number): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '—';
  }
  return `${(value * 100).toFixed(1)}%`;
}

export function getRiskLevel(risk: number): 'low' | 'medium' | 'high' {
  if (risk < 0.3) return 'low';
  if (risk < 0.6) return 'medium';
  return 'high';
}

export function getRiskColor(risk: number): string {
  const level = getRiskLevel(risk);
  switch (level) {
    case 'low':
      return 'text-green-600 bg-green-100';
    case 'medium':
      return 'text-yellow-700 bg-yellow-100';
    case 'high':
      return 'text-red-600 bg-red-100';
  }
}

export function getRiskBadgeClass(risk: number): string {
  const level = getRiskLevel(risk);
  switch (level) {
    case 'low':
      return 'bg-green-100 text-green-700';
    case 'medium':
      return 'bg-yellow-100 text-yellow-700';
    case 'high':
      return 'bg-red-100 text-red-700';
  }
}

export function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleString();
  } catch {
    return timestamp;
  }
}

export function formatChange(current: number, baseline: number): { value: string; isPositive: boolean } {
  if (baseline === 0) return { value: '—', isPositive: true };
  const change = ((current - baseline) / baseline) * 100;
  return {
    value: formatPercent(change),
    isPositive: change >= 0,
  };
}