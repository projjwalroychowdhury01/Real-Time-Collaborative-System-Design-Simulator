"""
Design CRUD API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.auth.sessions import get_current_user
from app.database.models import Design, User
from app.database.session import get_db

router = APIRouter()


class DesignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    design_json: Optional[dict] = None


class DesignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    design_json: Optional[dict] = None
    is_public: Optional[bool] = None


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_design(
    payload: DesignCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    design = Design(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        design_json=payload.design_json or {},
    )
    db.add(design)
    await db.commit()
    await db.refresh(design)
    return design


@router.get("")
async def list_designs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Design).where(Design.user_id == current_user.id))
    return result.scalars().all()


@router.get("/{design_id}")
async def get_design(
    design_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Design).where(Design.id == design_id))
    design = result.scalar_one_or_none()
    if not design:
        raise HTTPException(status_code=404, detail="Design not found")
    if design.user_id != current_user.id and not design.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    return design


@router.put("/{design_id}")
async def update_design(
    design_id: int,
    payload: DesignUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Design).where(Design.id == design_id))
    design = result.scalar_one_or_none()
    if not design:
        raise HTTPException(status_code=404, detail="Design not found")
    if design.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(design, field, value)

    await db.commit()
    await db.refresh(design)
    return design


@router.delete("/{design_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_design(
    design_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Design).where(Design.id == design_id))
    design = result.scalar_one_or_none()
    if not design:
        raise HTTPException(status_code=404, detail="Design not found")
    if design.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    await db.delete(design)
    await db.commit()
