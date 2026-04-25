// TypeScript types for real-time collaboration

export interface CollaboratorCursor {
  userId: string;
  username: string;
  x: number;
  y: number;
  color: string;
}

export interface CRDTDelta {
  type: 'crdt_delta';
  session_id: string;
  user_id: string;
  operations: unknown[];
  timestamp: string;
}

export interface PresenceUpdate {
  type: 'presence';
  session_id: string;
  user_id: string;
  username: string;
  cursor_x: number;
  cursor_y: number;
}

export type WSMessage = CRDTDelta | PresenceUpdate;
