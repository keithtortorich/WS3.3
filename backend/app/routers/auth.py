"""Auth router: session introspection + LinkedIn OAuth handshake endpoints.

Actual identity verification happens in ``app/core/auth.py`` (Clerk JWT).
This router exposes a thin ``/session`` endpoint the frontend can call to
confirm the current token resolves to a valid user/org, plus the LinkedIn
OAuth authorize/callback endpoints (LinkedIn is the fully-implemented
social platform — task #6).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.auth import AuthContext, get_current_user
from app.core.config import get_settings
from app.schemas.auth import OAuthAuthorizeResponse, OAuthCallbackRequest, SessionInfo
from app.social.platforms.linkedin import LinkedInAdapter

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
settings = get_settings()


@router.get("/session", response_model=SessionInfo)
async def get_session(auth: AuthContext = Depends(get_current_user)) -> SessionInfo:
    """Return the verified identity for the current bearer token."""
    return SessionInfo(
        user_id=auth.user_id,
        org_id=auth.org_id,
        org_role=auth.org_role,
        email=auth.email,
    )


@router.get("/linkedin/authorize", response_model=OAuthAuthorizeResponse)
async def linkedin_authorize(state: str) -> OAuthAuthorizeResponse:
    """Build the LinkedIn OAuth2 authorization URL for the connect-account flow."""
    adapter = LinkedInAdapter()
    url = adapter.build_authorization_url(state=state)
    return OAuthAuthorizeResponse(authorization_url=url, state=state)


@router.post("/linkedin/callback")
async def linkedin_callback(payload: OAuthCallbackRequest) -> dict:
    """Exchange the LinkedIn OAuth2 authorization code for tokens.

    In a full implementation this would persist a PlatformAccount row; the
    scaffold returns the exchanged token payload directly so the flow can
    be exercised/tested end-to-end without a database write dependency.
    """
    adapter = LinkedInAdapter()
    token_response = await adapter.exchange_code_for_token(payload.code)
    return {"status": "ok", "token": token_response.model_dump()}
