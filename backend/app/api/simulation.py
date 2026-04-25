"""
Simulation API route — thin adapter between HTTP and the simulation engine.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio

from simulation.engine import run_simulation

router = APIRouter()


class TrafficProfile(BaseModel):
    requests_per_sec: float = 100
    pattern: str = "steady"   # "steady" | "spike" | "gradual"
    duration_sec: int = 60


class SimulateRequest(BaseModel):
    design_json: dict
    traffic_profile: TrafficProfile


@router.post("/simulate")
async def simulate(payload: SimulateRequest):
    """
    Submit a design + traffic profile and receive simulation results.
    Hard timeout: 10 seconds.
    """
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                run_simulation,
                payload.design_json,
                payload.traffic_profile.model_dump(),
            ),
            timeout=10.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Simulation timed out (>10s)")
    return result
