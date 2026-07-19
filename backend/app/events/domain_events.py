"""Typed domain events for the in-process event bus (app/events/bus.py).

Each event is a frozen Pydantic model so subscribers can rely on its shape
and events are immutable once published (nothing downstream can mutate an
event another handler already received).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DomainEvent(BaseModel):
    """Base class for all domain events."""

    model_config = ConfigDict(frozen=True)

    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    occurred_at: datetime = Field(default_factory=_utcnow)
    organization_id: uuid.UUID


class CampaignCreated(DomainEvent):
    campaign_id: uuid.UUID
    client_id: uuid.UUID
    name: str


class PostGenerated(DomainEvent):
    post_id: uuid.UUID
    campaign_id: uuid.UUID
    ai_request_id: Optional[uuid.UUID] = None


class ApprovalRequested(DomainEvent):
    post_id: uuid.UUID
    stage: str
    requested_by_user_id: Optional[uuid.UUID] = None


class ApprovalReceived(DomainEvent):
    post_id: uuid.UUID
    approval_id: uuid.UUID
    status: str
    reviewer_user_id: Optional[uuid.UUID] = None


class MediaGenerated(DomainEvent):
    media_id: uuid.UUID
    post_id: Optional[uuid.UUID] = None


class Scheduled(DomainEvent):
    schedule_id: uuid.UUID
    post_id: uuid.UUID
    scheduled_at: datetime


class Published(DomainEvent):
    publish_job_id: uuid.UUID
    post_id: uuid.UUID
    platform: str
    external_post_id: str


class PublishFailed(DomainEvent):
    publish_job_id: uuid.UUID
    post_id: uuid.UUID
    platform: str
    error_message: str
    attempt_count: int


class AnalyticsUpdated(DomainEvent):
    post_id: uuid.UUID
    impressions: int
    likes: int
