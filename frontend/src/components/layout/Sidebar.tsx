import { NavLink, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  LayoutDashboard,
  FlaskConical,
  BarChart2,
  Settings,
  Info,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useState } from 'react';

interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/simulation', label: 'Well Simulation', icon: FlaskConical },
  { path: '/prediction', label: 'Prediction', icon: BarChart2 },
  { path: '/optimization', label: 'Optimization', icon: Settings },
  { path: '/models', label: 'Model Status', icon: Info },
  { path: '/about', label: 'Data Policy', icon: AlertTriangle },
];

interface SidebarProps {
  onWellChange?: (wellId: string) => void;
  selectedWell?: string;
  wells?: Array<{ well_id: string }>;
}

export function Sidebar({ onWellChange, selectedWell, wells = [] }: SidebarProps) {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={clsx(
        'fixed left-0 top-0 z-40 h-full bg-white border-r border-gray-200 transition-all duration-300',
        collapsed ? 'w-20' : 'w-64'
      )}
      aria-label="Main navigation"
    >
      <div className="flex flex-col h-full">
        <div className={clsx('flex items-center justify-between h-16 px-4 border-b border-gray-200', collapsed && 'justify-center')}>
          {!collapsed && (
            <NavLink to="/" className="flex items-center gap-2" aria-label="THERMALIFT Home">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
                <span className="text-white font-bold text-lg">T</span>
              </div>
              <span className="font-semibold text-gray-900">THERMALIFT</span>
            </NavLink>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className={clsx('p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors', collapsed && 'ml-auto')}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-expanded={!collapsed}
          >
            {collapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
          </button>
        </div>

        {!collapsed && wells.length > 0 && (
          <div className="p-4 border-b border-gray-200">
            <label htmlFor="well-select" className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
              Active Well
            </label>
            <select
              id="well-select"
              value={selectedWell || ''}
              onChange={(e) => onWellChange?.(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              aria-label="Select well"
            >
              <option value="">Select a well</option>
              {wells.map((well) => (
                <option key={well.well_id} value={well.well_id}>
                  {well.well_id}
                </option>
              ))}
            </select>
          </div>
        )}

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto" aria-label="Navigation">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive: active }) => clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  active
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
                  collapsed && 'justify-center px-2'
                )}
                aria-current={isActive ? 'page' : undefined}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                {!collapsed && <span>{item.label}</span>}
              </NavLink>
            );
          })}
        </nav>

        <div className={clsx('p-4 border-t border-gray-200', collapsed && 'hidden')}>
          <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 rounded-full bg-green-500" aria-hidden="true" />
            <span className="text-xs text-gray-500">API Connected</span>
          </div>
          <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-xs text-amber-800">
              <strong>Synthetic/Demo Data</strong> — Not validated against real field operations.
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}