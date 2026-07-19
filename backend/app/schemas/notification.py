"""Pydantic schemas for the Notification resource."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import NotificationType


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    notification_type: NotificationType
    title: str
    body: Optional[str]
    link_url: Optional[str]
    is_read: bool
    created_at: datetime


class NotificationMarkReadRequest(BaseModel):
    is_read: bool = True
