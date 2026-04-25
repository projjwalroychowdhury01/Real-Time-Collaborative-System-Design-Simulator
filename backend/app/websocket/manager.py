"""
WebSocket connection manager — tracks active connections per session,
broadcasts deltas, and delegates to Redis pub/sub for multi-instance setups.
"""
from __future__ import annotations

import json
from collections import defaultdict
from typing import Dict, List

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # session_token → list of connected WebSockets
        self._sessions: Dict[str, List[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, session_token: str) -> None:
        await websocket.accept()
        self._sessions[session_token].append(websocket)

    def disconnect(self, websocket: WebSocket, session_token: str) -> None:
        self._sessions[session_token].remove(websocket)
        if not self._sessions[session_token]:
            del self._sessions[session_token]

    async def broadcast(self, session_token: str, data: dict, sender: WebSocket) -> None:
        """Send a message to all clients in the session except the sender."""
        for connection in list(self._sessions.get(session_token, [])):
            if connection is not sender:
                try:
                    await connection.send_json(data)
                except Exception:
                    # Client disconnected mid-broadcast; remove silently
                    self.disconnect(connection, session_token)

    def active_users(self, session_token: str) -> int:
        return len(self._sessions.get(session_token, []))
