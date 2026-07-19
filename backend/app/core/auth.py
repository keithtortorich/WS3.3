"""Clerk JWT verification + multi-tenant auth dependencies.

Flow:
1. Frontend (Next.js + @clerk/nextjs) attaches a Clerk session JWT as a
   Bearer token on every API request.
2. :func:`get_current_user` verifies the JWT against Clerk's JWKS (fetched
   once and cached in-process with a TTL — Clerk rotates signing keys
   infrequently, so we don't want to hit the JWKS endpoint on every
   request), then extracts identity + org claims.
3. :func:`get_current_org` resolves the ``org_id`` claim to ensure the
   caller is scoped to an organization (required for every tenant-scoped
   endpoint).
4. :func:`require_role` is a dependency *factory*: call it with the roles
   allowed to hit an endpoint, e.g. ``Depends(require_role(OrgRole.OWNER,
   OrgRole.ADMIN))``.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

import httpx
import jwt
from fastapi import Depends, Header
from jwt import PyJWKClient

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.models.enums import OrgRole

settings = get_settings()

_JWKS_CACHE_TTL_SECONDS = 3600


@dataclass
class AuthContext:
    """Decoded, verified identity for the current request."""

    user_id: str  # Clerk user id (external identity, `sub` claim)
    org_id: Optional[str]  # Clerk organization id (`org_id` claim)
    org_role: Optional[str]  # Clerk organization role (`org_role` claim)
    email: Optional[str]
    raw_claims: dict[str, Any]


class _CachedJWKClient:
    """Thin TTL-cache wrapper around ``PyJWKClient`` so we don't refetch
    Clerk's JWKS document on every single request."""

    def __init__(self, jwks_url: str, ttl_seconds: int = _JWKS_CACHE_TTL_SECONDS) -> None:
        self._jwks_url = jwks_url
        self._ttl_seconds = ttl_seconds
        self._client: Optional[PyJWKClient] = None
        self._fetched_at: float = 0.0

    def get_client(self) -> PyJWKClient:
        now = time.monotonic()
        if self._client is None or (now - self._fetched_at) > self._ttl_seconds:
            self._client = PyJWKClient(self._jwks_url)
            self._fetched_at = now
        return self._client

    def get_signing_key(self, token: str):
        return self.get_client().get_signing_key_from_jwt(token)


_jwk_client = _CachedJWKClient(settings.CLERK_JWKS_URL)


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Missing or malformed Authorization header.")
    return authorization.split(" ", 1)[1].strip()


def decode_clerk_jwt(token: str) -> dict[str, Any]:
    """Verify signature/exp/iss(/aud) of a Clerk-issued JWT and return claims.

    Raises :class:`UnauthorizedError` on any verification failure — callers
    should not need to know *why* verification failed beyond a 401.
    """
    try:
        signing_key = _jwk_client.get_signing_key(token)
        decode_kwargs: dict[str, Any] = {
            "key": signing_key.key,
            "algorithms": ["RS256"],
            "issuer": settings.CLERK_ISSUER,
        }
        if settings.CLERK_AUDIENCE:
            decode_kwargs["audience"] = settings.CLERK_AUDIENCE
        else:
            decode_kwargs["options"] = {"verify_aud": False}
        claims = jwt.decode(token, **decode_kwargs)
        return claims
    except jwt.PyJWTError as exc:
        raise UnauthorizedError(f"Invalid authentication token: {exc}") from exc
    except (httpx.HTTPError, Exception) as exc:  # JWKS fetch/network errors
        raise UnauthorizedError(f"Unable to verify authentication token: {exc}") from exc


async def get_current_user(authorization: Optional[str] = Header(default=None)) -> AuthContext:
    """FastAPI dependency: verify the bearer token and build an AuthContext."""
    token = _extract_bearer_token(authorization)
    claims = decode_clerk_jwt(token)
    return AuthContext(
        user_id=claims.get("sub", ""),
        org_id=claims.get("org_id"),
        org_role=claims.get("org_role"),
        email=claims.get("email"),
        raw_claims=claims,
    )


async def get_current_org(auth: AuthContext = Depends(get_current_user)) -> str:
    """FastAPI dependency: same as get_current_user, but asserts an org_id
    claim is present (every tenant-scoped endpoint needs this)."""
    if not auth.org_id:
        raise ForbiddenError("This endpoint requires an active organization context.")
    return auth.org_id


_ROLE_RANK = {
    OrgRole.CLIENT_VIEWER: 0,
    OrgRole.MEMBER: 1,
    OrgRole.ADMIN: 2,
    OrgRole.OWNER: 3,
}


def require_role(*allowed_roles: OrgRole) -> Callable[[AuthContext], AuthContext]:
    """Dependency factory for RBAC. Usage::

        @router.delete(..., dependencies=[Depends(require_role(OrgRole.OWNER, OrgRole.ADMIN))])
    """

    def _dependency(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
        role_value = auth.org_role or OrgRole.MEMBER.value
        # Clerk sends roles like "org:admin" by convention; normalize.
        normalized = role_value.split(":")[-1]
        try:
            role = OrgRole(normalized)
        except ValueError:
            role = OrgRole.MEMBER
        if role not in allowed_roles:
            raise ForbiddenError(
                f"Role '{role.value}' is not permitted to perform this action."
            )
        return auth

    return _dependency
