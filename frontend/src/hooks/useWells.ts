import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api';
import type { WellsResponse } from '../types/api';

export function useWells() {
  return useQuery<WellsResponse, Error>({
    queryKey: ['wells'],
    queryFn: () => apiClient.getWells(),
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

export function useWell(wellId: string) {
  return useQuery({
    queryKey: ['well', wellId],
    queryFn: async () => {
      const response = await apiClient.getWells();
      return response.wells.find((w) => w.well_id === wellId);
    },
    enabled: !!wellId,
    staleTime: 5 * 60 * 1000,
  });
}