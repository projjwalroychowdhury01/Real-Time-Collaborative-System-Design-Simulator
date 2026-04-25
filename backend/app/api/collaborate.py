"""
Collaboration session routes.
"""
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.sessions import get_current_user
from app.database.models import CollaborationSession, Design, User
from app.database.session import get_db
from app.websocket.manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()


@router.post("/invite")
async def create_invite(
    design_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a shareable collaboration session token."""
    result = await db.execute(select(Design).where(Design.id == design_id))
    design = result.scalar_one_or_none()
    if not design or design.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Design not found")

    token = secrets.token_urlsafe(32)
    session = CollaborationSession(
        design_id=design_id,
        session_token=token,
        creator_id=current_user.id,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(session)
    await db.commit()
    return {"session_token": token}


@router.websocket("/join/{session_token}")
async def join_session(websocket: WebSocket, session_token: str, db: AsyncSession = Depends(get_db)):
    """WebSocket endpoint — CRDT sync hub."""
    result = await db.execute(
        select(CollaborationSession).where(CollaborationSession.session_token == session_token)
    )
    session = result.scalar_one_or_none()
    if not session or (session.expires_at and session.expires_at < datetime.utcnow()):
        await websocket.close(code=4004)
        return

    await manager.connect(websocket, session_token)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(session_token, data, sender=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_token)


@router.post("/leave")
async def leave_session():
    return {"message": "Left session"}
