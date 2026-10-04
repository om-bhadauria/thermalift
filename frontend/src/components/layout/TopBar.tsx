import { clsx } from 'clsx';
import { Wifi, WifiOff, AlertTriangle, Shield } from 'lucide-react';

interface TopBarProps {
  selectedWell?: string;
  apiStatus: 'connected' | 'disconnected' | 'connecting' | 'error';
  className?: string;
}

export function TopBar({ selectedWell, apiStatus = 'connected', className }: TopBarProps) {
  const statusConfigs = {
    connected: { label: 'API Connected', icon: Wifi, className: 'text-green-600', bg: 'bg-green-100' },
    disconnected: { label: 'API Disconnected', icon: WifiOff, className: 'text-red-600', bg: 'bg-red-100' },
    connecting: { label: 'Connecting...', icon: Wifi, className: 'text-blue-600 animate-pulse', bg: 'bg-blue-100' },
    error: { label: 'Connection Error', icon: WifiOff, className: 'text-red-600', bg: 'bg-red-100' },
  };

  const config = statusConfigs[apiStatus];

  return (
    <header
      className={clsx(
        'sticky top-0 z-30 h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6',
        className
      )}
      role="banner"
    >
      <div className="flex items-center gap-4">
        {selectedWell && (
          <div className="px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg">
            <span className="text-sm font-medium text-blue-700">Well: {selectedWell}</span>
          </div>
        )}
        <div className={clsx('flex items-center gap-2 px-3 py-1.5 rounded-lg', config.bg)}>
          <config.icon className={clsx('w-4 h-4', config.className)} aria-hidden="true" />
          <span className={clsx('text-sm font-medium', config.className)}>{config.label}</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className={clsx('flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-lg')}>
          <AlertTriangle className="w-4 h-4 text-amber-600" aria-hidden="true" />
          <span className="text-sm font-medium text-amber-800">Synthetic/Demo Data</span>
        </div>
        <div className={clsx('flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg')}>
          <Shield className="w-4 h-4 text-blue-600" aria-hidden="true" />
          <span className="text-sm font-medium text-blue-800">Prototype</span>
        </div>
      </div>
    </header>
  );
}