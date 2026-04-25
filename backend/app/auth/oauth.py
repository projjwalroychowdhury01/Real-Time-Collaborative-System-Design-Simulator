"""
OAuth 2.0 routes — Google and GitHub social login.

Routes
------
GET  /auth/login/{provider}            → redirect to OAuth provider
GET  /auth/callback/{provider}         → handle provider callback, issue tokens
POST /auth/refresh                     → exchange refresh token for new access token
GET  /auth/me                          → return current user profile
POST /auth/logout                      → blacklist refresh token + clear cookie
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.auth.sessions import (
    create_token_pair,
    decode_token,
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
    """Exchange the authorisation code for tokens, upsert the user record,
    and redirect to the frontend.

    Improvement #1:
    - refresh_token → httpOnly, Secure, SameSite=Strict cookie (never exposed in URL)
    - access_token  → URL fragment (#access_token=...) which browsers never send to servers
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
        login_name = user_info.get("login", "")
        email      = user_info.get("email") or f"{login_name}@github.local"
        name       = login_name
        auth_id    = str(user_info.get("id", ""))

    if not email or not auth_id:
        raise HTTPException(status_code=400, detail="Could not retrieve email from provider")

    user = await get_or_create_user(
        db, email=email, username=name, provider=provider, auth_id=auth_id
    )
    tokens = create_token_pair(user.id, user.email)

    # Improvement #1: access_token in URL fragment (not sent to server by browsers)
    redirect_url = (
        f"{settings.FRONTEND_URL}/auth/callback"
        f"#access_token={tokens['access_token']}"
    )
    response = RedirectResponse(url=redirect_url)

    # Improvement #1: refresh_token in httpOnly cookie (inaccessible to JavaScript)
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=not settings.DEBUG,   # Secure=True in production (HTTPS only)
        samesite="lax",              # "lax" allows the initial redirect; use "strict" for APIs
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86_400,
        path="/auth",                # Scoped: only sent to /auth/* endpoints
    )
    return response


# ── Token refresh ─────────────────────────────────────────────────────────────

class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None   # fallback if cookie not available


@router.post("/refresh", summary="Refresh access token")
async def refresh(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a valid refresh token for a new access token.

    Priority: httpOnly cookie → JSON body field `refresh_token`.
    """
    # 1. Try the httpOnly cookie (primary path for browser clients)
    token: Optional[str] = request.cookies.get("refresh_token")

    # 2. Fall back to JSON body (for API / mobile clients)
    if not token:
        try:
            body = await request.json()
            token = body.get("refresh_token")
        except Exception:
            pass

    if not token:
        raise HTTPException(
            status_code=422,
            detail="refresh_token required (httpOnly cookie or JSON body field)",
        )
    return await refresh_access_token(token, db)


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
async def logout(request: Request):
    """Improvement #3: Blacklist the refresh token JTI in Redis, then clear the cookie.

    Reads the token from the httpOnly cookie.  If the client also sends it in
    the Authorization header, that access token is NOT blacklisted here — its
    short lifetime (60 min) is the security boundary for access tokens.
    """
    from app.redis_client import revoke_token

    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        try:
            token_payload = decode_token(refresh_token, expected_type="refresh")
            jti = token_payload.get("jti", "")
            exp = token_payload.get("exp", 0)
            remaining_ttl = max(0, exp - int(datetime.now(timezone.utc).timestamp()))
            if jti and remaining_ttl > 0:
                await revoke_token(jti, remaining_ttl)
        except HTTPException:
            pass  # Already invalid; logout proceeds regardless

    response = JSONResponse({"message": "Logged out successfully"})
    response.delete_cookie(key="refresh_token", path="/auth")
    return response
