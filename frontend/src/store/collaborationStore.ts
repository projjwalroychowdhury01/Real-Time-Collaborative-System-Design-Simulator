import { create } from 'zustand';
import type { CollaboratorCursor } from '@/types/collaboration';

interface CollaborationState {
  sessionToken: string | null;
  collaborators: Record<string, CollaboratorCursor>;

  setSession: (token: string) => void;
  upsertCursor: (cursor: CollaboratorCursor) => void;
  removeCursor: (userId: string) => void;
}

export const useCollaborationStore = create<CollaborationState>()((set) => ({
  sessionToken: null,
  collaborators: {},

  setSession(token) {
    set({ sessionToken: token });
  },

  upsertCursor(cursor) {
    set((s) => ({
      collaborators: { ...s.collaborators, [cursor.userId]: cursor },
    }));
  },

  removeCursor(userId) {
    set((s) => {
      const next = { ...s.collaborators };
      delete next[userId];
      return { collaborators: next };
    });
  },
}));
