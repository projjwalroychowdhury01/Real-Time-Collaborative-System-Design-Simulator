"""
OAuth 2.0 routes — Google and GitHub social login.

Routes
------
GET  /auth/login/{provider}            → redirect to OAuth provider
GET  /auth/callback/{provider}         → handle provider callback, issue tokens
POST /auth/refresh                     → exchange refresh token for new access token
GET  /auth/me                          → return current user profile
POST /auth/logout                      → client-side token removal hint
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.auth.sessions import (
    create_token_pair,
    refresh_access_token,
    get_or_create_user,
    get_current_user,
)
from app.database.models import User
from app.database.session import get_db

router = APIRouter()

# ── Authlib OAuth client registry ────────────────────────────────────────────
oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

oauth.register(
    name="github",
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)


# ── Login — redirect to provider ─────────────────────────────────────────────

@router.get("/login/{provider}", summary="Initiate OAuth login flow")
async def login(provider: str, request: Request):
    """Redirect the browser to the chosen OAuth provider's authorisation page."""
    if provider not in ("google", "github"):
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    client = oauth.create_client(provider)
    redirect_uri = str(request.url_for("auth_callback", provider=provider))
    return await client.authorize_redirect(request, redirect_uri)


# ── Callback — handle provider response ──────────────────────────────────────

@router.get("/callback/{provider}", name="auth_callback", summary="Handle OAuth callback")
async def callback(provider: str, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Exchange the authorisation code for tokens, upsert the user record,
    and redirect to the frontend with both JWT tokens as query params.

    Note: In production, store the refresh token in an httpOnly cookie instead
    of a query parameter.
    """
    if provider not in ("google", "github"):
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    client = oauth.create_client(provider)

    try:
        token = await client.authorize_access_token(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"OAuth error: {exc}") from exc

    if provider == "google":
        user_info = token.get("userinfo") or {}
        email   = user_info.get("email", "")
        name    = user_info.get("name") or email.split("@")[0]
        auth_id = user_info.get("sub", "")
    else:  # github
        resp = await client.get("user", token=token)
        user_info = resp.json()
        login    = user_info.get("login", "")
        email    = user_info.get("email") or f"{login}@github.local"
        name     = login
        auth_id  = str(user_info.get("id", ""))

    if not email or not auth_id:
        raise HTTPException(status_code=400, detail="Could not retrieve email from provider")

    user = await get_or_create_user(
        db, email=email, username=name, provider=provider, auth_id=auth_id
    )
    tokens = create_token_pair(user.id, user.email)

    redirect_url = (
        f"{settings.FRONTEND_URL}/auth/callback"
        f"?access_token={tokens['access_token']}"
        f"&refresh_token={tokens['refresh_token']}"
    )
    return RedirectResponse(url=redirect_url)


# ── Token refresh ─────────────────────────────────────────────────────────────

class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", summary="Refresh access token")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a new access token."""
    return await refresh_access_token(payload.refresh_token, db)


# ── Current user profile ──────────────────────────────────────────────────────

@router.get("/me", summary="Get current user profile")
async def me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return {
        "id":            current_user.id,
        "email":         current_user.email,
        "username":      current_user.username,
        "auth_provider": current_user.auth_provider,
        "created_at":    current_user.created_at,
    }


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout", summary="Logout")
async def logout():
    """
    Signal the client to discard its tokens.

    Server-side token blacklisting (via Redis) can be added here in Phase 2.
    """
    return {"message": "Logged out successfully"}
