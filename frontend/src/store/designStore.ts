import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import type { DesignComponent, DesignEdge, DesignJSON } from '@/types/design';
import { v4 as uuidv4 } from 'uuid';

interface DesignState {
  designId: number | null;
  components: DesignComponent[];
  edges: DesignEdge[];
  selectedId: string | null;

  // Actions
  setDesign: (id: number, json: DesignJSON) => void;
  addComponent: (component: Omit<DesignComponent, 'id'>) => void;
  updateComponent: (id: string, patch: Partial<DesignComponent>) => void;
  removeComponent: (id: string) => void;
  addEdge: (edge: Omit<DesignEdge, 'id'>) => void;
  removeEdge: (id: string) => void;
  selectNode: (id: string | null) => void;
  toJSON: () => DesignJSON;
}

export const useDesignStore = create<DesignState>()(
  immer((set, get) => ({
    designId: null,
    components: [],
    edges: [],
    selectedId: null,

    setDesign(id, json) {
      set((s) => {
        s.designId = id;
        s.components = json.components;
        s.edges = json.edges;
      });
    },

    addComponent(component) {
      set((s) => {
        s.components.push({ ...component, id: uuidv4() });
      });
    },

    updateComponent(id, patch) {
      set((s) => {
        const idx = s.components.findIndex((c) => c.id === id);
        if (idx !== -1) Object.assign(s.components[idx], patch);
      });
    },

    removeComponent(id) {
      set((s) => {
        s.components = s.components.filter((c) => c.id !== id);
        s.edges = s.edges.filter((e) => e.from !== id && e.to !== id);
      });
    },

    addEdge(edge) {
      set((s) => {
        s.edges.push({ ...edge, id: uuidv4() });
      });
    },

    removeEdge(id) {
      set((s) => {
        s.edges = s.edges.filter((e) => e.id !== id);
      });
    },

    selectNode(id) {
      set((s) => { s.selectedId = id; });
    },

    toJSON() {
      const { components, edges } = get();
      return { components, edges };
    },
  })),
);
