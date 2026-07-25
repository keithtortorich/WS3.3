"""Auth-related schemas (session introspection, LinkedIn OAuth handshake)."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class SessionInfo(BaseModel):
    """What the frontend gets back from GET /api/v1/auth/session — a
    normalized view of the verified Clerk JWT claims."""

    user_id: str
    org_id: Optional[str]
    org_role: Optional[str]
    email: Optional[str]


class OAuthAuthorizeResponse(BaseModel):
    authorization_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str
