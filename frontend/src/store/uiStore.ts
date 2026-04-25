import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { SimulationResult } from '@/types/simulation';

interface UIState {
  sidebarOpen: boolean;
  simPanelOpen: boolean;
  simulationResult: SimulationResult | null;
  isSimulating: boolean;

  toggleSidebar: () => void;
  toggleSimPanel: () => void;
  setSimulationResult: (result: SimulationResult | null) => void;
  setSimulating: (v: boolean) => void;
}

export const useUIStore = create<UIState>()((set) => ({
  sidebarOpen: true,
  simPanelOpen: false,
  simulationResult: null,
  isSimulating: false,

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  toggleSimPanel: () => set((s) => ({ simPanelOpen: !s.simPanelOpen })),
  setSimulationResult: (result) => set({ simulationResult: result }),
  setSimulating: (v) => set({ isSimulating: v }),
}));

// ── Auth store (persisted) ────────────────────────────────────
interface AuthState {
  token: string | null;
  setToken: (token: string | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      setToken: (token) => set({ token }),
    }),
    { name: 'auth-token' },
  ),
);
