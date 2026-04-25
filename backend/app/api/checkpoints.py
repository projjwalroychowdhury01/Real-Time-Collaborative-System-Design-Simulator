"""
Checkpoint API routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.sessions import get_current_user
from app.database.models import Checkpoint, Design, User
from app.database.session import get_db

router = APIRouter()


@router.get("/{design_id}/checkpoints")
async def list_checkpoints(
    design_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all checkpoints for a design, ordered chronologically."""
    result = await db.execute(select(Design).where(Design.id == design_id))
    design = result.scalar_one_or_none()
    if not design or (design.user_id != current_user.id and not design.is_public):
        raise HTTPException(status_code=404, detail="Design not found")

    cp_result = await db.execute(
        select(Checkpoint)
        .where(Checkpoint.design_id == design_id)
        .order_by(Checkpoint.checkpoint_number)
    )
    return cp_result.scalars().all()


@router.get("/{design_id}/checkpoints/{cp_id}")
async def get_checkpoint(
    design_id: int,
    cp_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a single checkpoint by ID."""
    result = await db.execute(select(Design).where(Design.id == design_id))
    design = result.scalar_one_or_none()
    if not design or (design.user_id != current_user.id and not design.is_public):
        raise HTTPException(status_code=404, detail="Design not found")

    cp_result = await db.execute(
        select(Checkpoint).where(Checkpoint.id == cp_id, Checkpoint.design_id == design_id)
    )
    cp = cp_result.scalar_one_or_none()
    if not cp:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return cp
