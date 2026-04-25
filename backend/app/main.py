"""
FastAPI application entry point.

Startup sequence
----------------
1. Authlib session middleware is mounted first (required for OAuth state).
2. CORS middleware runs second so pre-flight OPTIONS are handled properly.
3. `init_db()` runs inside the lifespan to create tables if they don't exist.
   In production you would run Alembic migrations instead.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database.session import init_db
from app.api import designs, checkpoints, collaborate
from app.api import simulation as sim_router
from app.auth import oauth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup / shutdown logic."""
    # ── Startup ─────────────────────────────────────────────────
    await init_db()
    yield
    # ── Shutdown ────────────────────────────────────────────────
    # Nothing to tear down for now; connection pools are GC'd by SQLAlchemy.


app = FastAPI(
    title="System Design Simulator API",
    version="1.0.0",
    description="Real-Time Collaborative System Design Simulator",
    lifespan=lifespan,
)

# ── Starlette session middleware (required by Authlib's OAuth client) ────────
# Must be added BEFORE CORS so the session cookie is readable on every request.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET_KEY,
    session_cookie="sds_session",
    max_age=3600,          # 1 hour
    https_only=False,      # Set True in production behind HTTPS
    same_site="lax",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(oauth.router,       prefix="/auth",       tags=["auth"])
app.include_router(designs.router,     prefix="/designs",    tags=["designs"])
app.include_router(checkpoints.router, prefix="/designs",    tags=["checkpoints"])
app.include_router(collaborate.router, prefix="/collaborate", tags=["collaborate"])
app.include_router(sim_router.router,  prefix="",            tags=["simulation"])


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": app.version}
