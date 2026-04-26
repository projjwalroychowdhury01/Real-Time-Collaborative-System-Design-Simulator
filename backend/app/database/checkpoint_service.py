"""
Auto-checkpointing service.

Runs on a background task every 60 seconds to save design state.
Each checkpoint stores design_json and timestamp, with auto-incrementing checkpoint_number.
"""
import asyncio
import logging
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Checkpoint, Design, Base
from app.config import settings

logger = logging.getLogger(__name__)

_checkpoint_task = None
_engine = None
_async_session_factory = None


async def init_checkpoint_service():
    """Initialize checkpoint service engine and session factory."""
    global _engine, _async_session_factory

    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        _async_session_factory = sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )


async def get_checkpoint_session() -> AsyncSession:
    """Get a session for checkpoint operations."""
    global _async_session_factory
    if _async_session_factory is None:
        await init_checkpoint_service()
    return _async_session_factory()


async def create_checkpoint_for_design(design_id: int, session: AsyncSession) -> Checkpoint | None:
    """
    Create a checkpoint for a design.

    Returns the checkpoint record, or None if design not found.
    """
    # Fetch the design
    result = await session.execute(select(Design).where(Design.id == design_id))
    design = result.scalar_one_or_none()

    if not design:
        return None

    # Get next checkpoint number
    cp_result = await session.execute(
        select(func.max(Checkpoint.checkpoint_number))
        .where(Checkpoint.design_id == design_id)
    )
    max_cp_num = cp_result.scalar() or 0

    # Create checkpoint
    checkpoint = Checkpoint(
        design_id=design_id,
        checkpoint_number=max_cp_num + 1,
        design_json=design.design_json,
        checkpoint_meta={
            "auto_checkpoint": True,
            "checkpoint_reason": "automatic",
        },
    )
    session.add(checkpoint)
    await session.commit()
    await session.refresh(checkpoint)

    return checkpoint


async def checkpoint_loop():
    """
    Background loop that creates checkpoints every 60 seconds.
    Runs indefinitely until cancelled.
    """
    await init_checkpoint_service()

    while True:
        try:
            await asyncio.sleep(60)  # Wait 60 seconds before first checkpoint

            session = await get_checkpoint_session()
            try:
                # Fetch all designs
                result = await session.execute(select(Design))
                designs = result.scalars().all()

                for design in designs:
                    try:
                        await create_checkpoint_for_design(design.id, session)
                    except Exception as e:
                        logger.error(f"Failed to checkpoint design {design.id}: {e}")

                logger.debug(f"Auto-checkpoint: created checkpoints for {len(designs)} designs")
            finally:
                await session.close()
        except asyncio.CancelledError:
            logger.info("Checkpoint loop cancelled")
            break
        except Exception as e:
            logger.error(f"Checkpoint loop error: {e}", exc_info=True)
            # Continue after error to avoid stopping the service


def start_checkpoint_service() -> asyncio.Task:
    """Start the background checkpoint task. Returns the task handle."""
    global _checkpoint_task
    _checkpoint_task = asyncio.create_task(checkpoint_loop())
    return _checkpoint_task


async def stop_checkpoint_service():
    """Stop the background checkpoint task gracefully."""
    global _checkpoint_task, _engine

    if _checkpoint_task:
        _checkpoint_task.cancel()
        try:
            await _checkpoint_task
        except asyncio.CancelledError:
            pass

    if _engine:
        await _engine.dispose()
