import { type ReactNode } from 'react';
import { clsx } from 'clsx';
import { AlertCircle, RefreshCw, XCircle } from 'lucide-react';
import { Card } from './Card';

interface ErrorDisplayProps {
  message: string;
  title?: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
  variant?: 'inline' | 'card' | 'fullscreen';
}

export function ErrorDisplay({
  message,
  title = 'Error',
  onRetry,
  onDismiss,
  className,
  variant = 'card',
}: ErrorDisplayProps) {
  const icon = onRetry ? RefreshCw : XCircle;

  const content = (
    <div className={clsx('flex flex-col items-center text-center gap-3', className)}>
      <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
        <AlertCircle className="w-6 h-6 text-red-600" aria-hidden="true" />
      </div>
      <div>
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <p className="text-gray-600 mt-1 max-w-md">{message}</p>
      </div>
      <div className="flex gap-3 mt-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" aria-hidden="true" />
            Retry
          </button>
        )}
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <XCircle className="w-4 h-4" aria-hidden="true" />
            Dismiss
          </button>
        )}
      </div>
    </div>
  );

  switch (variant) {
    case 'inline':
      return <div className="p-4 bg-red-50 border border-red-200 rounded-lg">{content}</div>;
    case 'fullscreen':
      return (
        <div className="fixed inset-0 bg-white flex items-center justify-center z-50 p-4">
          <div className="max-w-md w-full">{content}</div>
        </div>
      );
    default:
      return (
        <Card className={clsx('border-red-200 bg-red-50', className)}>
          {content}
        </Card>
      );
  }
}

interface AlertBannerProps {
  message: string;
  type?: 'error' | 'warning' | 'info' | 'success';
  onDismiss?: () => void;
}

export function AlertBanner({ message, type = 'error', onDismiss }: AlertBannerProps) {
  const configs = {
    error: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', icon: AlertCircle, iconColor: 'text-red-600' },
    warning: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-700', icon: AlertCircle, iconColor: 'text-yellow-600' },
    info: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', icon: AlertCircle, iconColor: 'text-blue-600' },
    success: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700', icon: AlertCircle, iconColor: 'text-green-600' },
  };

  const config = configs[type];

  return (
    <div className={clsx('flex items-start gap-3 p-4 rounded-lg', config.bg, config.border)} role="alert">
      <config.icon className={clsx('w-5 h-5 flex-shrink-0 mt-0.5', config.iconColor)} aria-hidden="true" />
      <p className={clsx('flex-1 text-sm', config.text)}>{message}</p>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Dismiss"
        >
          <XCircle className="w-5 h-5" aria-hidden="true" />
        </button>
      )}
    </div>
  );
}