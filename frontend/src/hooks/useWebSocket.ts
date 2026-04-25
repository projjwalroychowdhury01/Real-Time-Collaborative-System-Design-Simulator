import { useEffect, useRef, useCallback } from 'react';
import type { WSMessage } from '@/types/collaboration';
import { useCollaborationStore } from '@/store/collaborationStore';

const WS_BASE = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000';

export function useWebSocket(sessionToken: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const { upsertCursor, removeCursor } = useCollaborationStore();

  useEffect(() => {
    if (!sessionToken) return;

    const ws = new WebSocket(`${WS_BASE}/collaborate/join/${sessionToken}`);
    wsRef.current = ws;

    ws.onmessage = (evt) => {
      const msg: WSMessage = JSON.parse(evt.data);
      if (msg.type === 'presence') {
        upsertCursor({
          userId: msg.user_id,
          username: msg.username,
          x: msg.cursor_x,
          y: msg.cursor_y,
          color: hashColor(msg.user_id),
        });
      }
    };

    ws.onclose = () => console.info('[WS] disconnected');
    ws.onerror = (e) => console.error('[WS] error', e);

    return () => ws.close();
  }, [sessionToken]);

  const send = useCallback((data: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return { send };
}

function hashColor(str: string): string {
  let hash = 0;
  for (const ch of str) hash = ch.charCodeAt(0) + ((hash << 5) - hash);
  return `hsl(${hash % 360}, 70%, 60%)`;
}
