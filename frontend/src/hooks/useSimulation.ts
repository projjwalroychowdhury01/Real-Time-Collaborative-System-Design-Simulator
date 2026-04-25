import { useCallback } from 'react';
import api from '@/utils/api';
import { useUIStore } from '@/store/uiStore';
import { useDesignStore } from '@/store/designStore';
import type { TrafficProfile } from '@/types/simulation';

export function useSimulation() {
  const { setSimulating, setSimulationResult } = useUIStore();
  const toJSON = useDesignStore((s) => s.toJSON);

  const runSimulation = useCallback(
    async (profile: TrafficProfile) => {
      setSimulating(true);
      setSimulationResult(null);
      try {
        const { data } = await api.post('/simulate', {
          design_json: toJSON(),
          traffic_profile: profile,
        });
        setSimulationResult(data);
        return data;
      } finally {
        setSimulating(false);
      }
    },
    [setSimulating, setSimulationResult, toJSON],
  );

  return { runSimulation };
}
