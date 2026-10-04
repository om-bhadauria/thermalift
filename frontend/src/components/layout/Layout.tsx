import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { clsx } from 'clsx';
import { useState, useEffect } from 'react';
import { apiClient } from '../../api';
import { useWellsContext } from '../../contexts/WellsContext';

export function Layout() {
  const location = useLocation();
  const [apiStatus, setApiStatus] = useState<'connected' | 'disconnected' | 'connecting' | 'error'>('connecting');
  const { wells, selectedWell, setSelectedWell, isLoading } = useWellsContext();

  useEffect(() => {
    checkApiHealth();
  }, []);

  useEffect(() => {
    if (wells.length > 0 && !selectedWell) {
      setSelectedWell(wells[0].well_id);
    }
  }, [wells, selectedWell, setSelectedWell]);

  const checkApiHealth = async () => {
    try {
      await apiClient.healthCheck();
      setApiStatus('connected');
    } catch {
      setApiStatus('disconnected');
    }
  };

  const handleWellChange = (wellId: string) => {
    setSelectedWell(wellId);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar
        onWellChange={handleWellChange}
        selectedWell={selectedWell}
        wells={wells}
      />
      <div className="transition-all duration-300 min-h-screen lg:pl-64">
        <TopBar selectedWell={selectedWell} apiStatus={apiStatus} />
        <main className="p-6" role="main" aria-label="Main content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}