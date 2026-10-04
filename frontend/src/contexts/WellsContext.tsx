import { createContext, useContext, useState, type ReactNode } from 'react';
import { useWells } from '../hooks/useWells';

interface WellsContextType {
  wells: Array<{ well_id: string }>;
  selectedWell: string;
  setSelectedWell: (wellId: string) => void;
  isLoading: boolean;
}

const WellsContext = createContext<WellsContextType | undefined>(undefined);

export function WellsProvider({ children }: { children: ReactNode }) {
  const { data: wellsResponse, isLoading } = useWells();
  const [selectedWell, setSelectedWell] = useState<string>('');

  const wells = wellsResponse?.wells || [];

  return (
    <WellsContext.Provider value={{ wells, selectedWell, setSelectedWell, isLoading }}>
      {children}
    </WellsContext.Provider>
  );
}

export function useWellsContext() {
  const context = useContext(WellsContext);
  if (!context) {
    throw new Error('useWellsContext must be used within a WellsProvider');
  }
  return context;
}