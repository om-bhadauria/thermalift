import { type ReactNode } from 'react';
import { clsx } from 'clsx';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'neutral';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const variantClasses = {
  default: 'bg-gray-100 text-gray-700',
  success: 'bg-green-100 text-green-700',
  warning: 'bg-yellow-100 text-yellow-700',
  danger: 'bg-red-100 text-red-700',
  info: 'bg-blue-100 text-blue-700',
  neutral: 'bg-slate-100 text-slate-700',
};

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
  lg: 'px-3 py-1 text-base',
};

export function Badge({ children, variant = 'default', size = 'md', className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center font-medium rounded-full',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
    >
      {children}
    </span>
  );
}

interface StatusBadgeProps {
  status: 'ok' | 'error' | 'loading' | 'warning';
  label?: string;
}

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const configs = {
    ok: { variant: 'success' as const, icon: '●', defaultLabel: 'Connected' },
    error: { variant: 'danger' as const, icon: '●', defaultLabel: 'Disconnected' },
    loading: { variant: 'info' as const, icon: '◐', defaultLabel: 'Connecting...' },
    warning: { variant: 'warning' as const, icon: '◑', defaultLabel: 'Warning' },
  };

  const config = configs[status];
  return (
    <Badge variant={config.variant} size="sm">
      <span className="mr-1.5" aria-hidden="true">{config.icon}</span>
      {label || config.defaultLabel}
    </Badge>
  );
}