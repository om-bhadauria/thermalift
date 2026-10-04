import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WellsProvider } from './contexts/WellsContext';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { SimulationPage } from './pages/Simulation';
import { PredictionPage } from './pages/Prediction';
import { OptimizationPage } from './pages/Optimization';
import { ModelsPage } from './pages/Models';
import { AboutPage } from './pages/About';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="simulation" element={<SimulationPage />} />
        <Route path="prediction" element={<PredictionPage />} />
        <Route path="optimization" element={<OptimizationPage />} />
        <Route path="models" element={<ModelsPage />} />
        <Route path="about" element={<AboutPage />} />
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <WellsProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </WellsProvider>
    </QueryClientProvider>
  );
}

export default App;;