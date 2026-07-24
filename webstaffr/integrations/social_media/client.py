"""Social media marketing client surface.

This is a thin seam, not a full SMM implementation. Platform calls stay
in the SMM product; WS3.3 only needs mount/intent read/write behavior.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .sync import SocialMediaSync

class SocialMediaClientError(RuntimeError):
    """Raised when social media integration config or calls fail."""


SocialMediaHTTPError = SocialMediaClientError
SocialMediaConfigError = SocialMediaClientError


@dataclass(frozen=True)
class SocialMediaMount:
    mount_id: int
    tenant_id: str
    social_tenant_id: str
    platforms: list[str]
    default_brand_id: Optional[str]
    mode: str
    created_at: str


@dataclass(frozen=True)
class SocialMediaIntent:
    intent_id: int
    mount_id: int
    campaign_intent: dict[str, Any]
    post_draft: dict[str, Any]
    status: str
    workflow_instance_id: Optional[str]
    approval_url: Optional[str]
    created_at: str


class SocialMediaClient:
    """Thin wrapper around SocialMediaSync so routers can swap this
    for an HTTP-backed client later without changing handler code.
    """

    def __init__(self, conn: Any) -> None:
        self._sync = SocialMediaSync(conn)

    def mount(
        self,
        *,
        tenant_id: str,
        social_tenant_id: str,
        platforms: list[str],
        default_brand_id: Optional[str],
        mode: str,
    ) -> SocialMediaMount:
        return self._sync.mount(
            tenant_id=tenant_id,
            social_tenant_id=social_tenant_id,
            platforms=platforms,
            default_brand_id=default_brand_id,
            mode=mode,
        )

    def create_intent(
        self,
        *,
        mount_id: int,
        campaign_intent: dict[str, Any],
        post_draft: dict[str, Any],
    ) -> SocialMediaIntent:
        return self._sync.create_intent(
            mount_id=mount_id,
            campaign_intent=campaign_intent,
            post_draft=post_draft,
        )

    def get_intent(self, *, intent_id: int) -> SocialMediaIntent:
        return self._sync.get_intent(intent_id=intent_id)
