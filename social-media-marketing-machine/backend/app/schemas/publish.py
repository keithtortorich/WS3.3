"""Pydantic schemas for publish-job operations."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PublishJobStatus


class PublishRequest(BaseModel):
    """Immediately enqueue a publish attempt for a Post on a PlatformAccount."""

    post_id: uuid.UUID
    platform_account_id: uuid.UUID


class ScheduleRequest(BaseModel):
    """Schedule a future publish attempt."""

    post_id: uuid.UUID
    platform_account_id: uuid.UUID
    scheduled_at: datetime


class PublishJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    post_id: uuid.UUID
    platform_account_id: uuid.UUID
    status: PublishJobStatus
    attempt_count: int
    max_attempts: int
    last_error: Optional[str]
    external_post_id: Optional[str]
    next_attempt_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
