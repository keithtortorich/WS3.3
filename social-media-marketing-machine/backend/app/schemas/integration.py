"""Pydantic v2 schemas for the WS3.3 -> SMM integration bridge.

The wire shapes here mirror INTEGRATION_PLAN.md's contract literally,
including its field names (``tenant_id`` / ``social_tenant_id`` rather than
this codebase's internal ``external_tenant_id`` / ``organization_id``). The
translation to internal names happens in
``app/services/integration_service.py``, deliberately — the contract is owned
by the integration boundary, not by SMM's model layer, and renaming it here
would make the plan and the code disagree.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.integration_mount import (
    EXTERNAL_SYSTEM_WEBSTAFFR,
    MOUNT_MODE_APPROVAL_REQUIRED,
    MOUNT_MODES,
)


class MountRequest(BaseModel):
    """Body of ``POST /integrations/social-media-marketing/mount``."""

    model_config = ConfigDict(extra="forbid")

    #: The external system's tenant identifier (WS3.3's public tenant slug).
    tenant_id: str = Field(min_length=1, max_length=255)
    #: The SMM org/Clerk identity this tenant maps onto. Must match the
    #: authenticated caller's org — see IntegrationService.create_mount.
    social_tenant_id: str = Field(min_length=1, max_length=255)
    platforms: list[str] = Field(default_factory=list)
    default_brand_id: Optional[uuid.UUID] = None
    #: The real Client campaigns from this tenant belong to. Optional so the
    #: plan's original body still validates, but supplying it is the difference
    #: between correctly-attributed campaigns and auto-created placeholders.
    default_client_id: Optional[uuid.UUID] = None
    mode: str = Field(default=MOUNT_MODE_APPROVAL_REQUIRED)
    #: Not in the plan's example body; defaulted so existing callers need no
    #: change, but explicit so a second external system can be mounted later.
    external_system: str = Field(default=EXTERNAL_SYSTEM_WEBSTAFFR, max_length=100)

    def validated_mode(self) -> str:
        return self.mode


class MountRead(BaseModel):
    """Representation of a mount (used by tests/diagnostics; the contract's
    mount endpoint itself returns 204 + Location, not a body)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    external_system: str
    external_tenant_id: str
    platforms: Optional[list[str]]
    default_brand_id: Optional[uuid.UUID]
    default_client_id: Optional[uuid.UUID]
    mode: str
    created_at: datetime
    updated_at: datetime


class CampaignIntent(BaseModel):
    """The ``campaign_intent`` block of the intent contract."""

    model_config = ConfigDict(extra="forbid")

    objective: str = Field(min_length=1, max_length=1000)
    budget_cents: Optional[int] = Field(default=None, ge=0)
    platforms: list[str] = Field(default_factory=list)
    start: Optional[date] = None
    end: Optional[date] = None
    brand_id: Optional[uuid.UUID] = None


class PostDraft(BaseModel):
    """The ``post_draft`` block of the intent contract."""

    model_config = ConfigDict(extra="forbid")

    headline: str = Field(default="", max_length=500)
    body: str = Field(default="")
    media_refs: list[str] = Field(default_factory=list)


class IntentRequest(BaseModel):
    """Body of ``POST /integrations/social-media-marketing/mount/{id}/intent``."""

    model_config = ConfigDict(extra="forbid")

    campaign_intent: CampaignIntent
    post_draft: PostDraft


class IntentResponse(BaseModel):
    """Contract response: ``{status, workflow_instance_id, approval_url}``."""

    status: str
    workflow_instance_id: str
    approval_url: str
    #: Extra, additive fields — the contract's three keys are always present,
    #: and WS3.3's client ignores unknown keys (it maps by name).
    campaign_id: uuid.UUID
    post_ids: list[uuid.UUID]


__all__ = [
    "MOUNT_MODES",
    "MountRequest",
    "MountRead",
    "CampaignIntent",
    "PostDraft",
    "IntentRequest",
    "IntentResponse",
]
