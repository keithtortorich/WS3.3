"""Pydantic schemas for the calendar view (aggregated Schedule + Post data)."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CalendarEntry(BaseModel):
    """A single calendar cell: one scheduled Post on one PlatformAccount."""

    model_config = ConfigDict(from_attributes=True)

    schedule_id: uuid.UUID
    post_id: uuid.UUID
    platform_account_id: uuid.UUID
    scheduled_at: datetime
    platform: str
    post_status: str
    caption_preview: str


class CalendarQueryParams(BaseModel):
    start_date: date
    end_date: date
    campaign_id: Optional[uuid.UUID] = None
