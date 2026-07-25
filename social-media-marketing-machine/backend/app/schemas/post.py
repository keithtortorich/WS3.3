"""Pydantic request/response schemas for the Post resource."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PostStatus


class PostBase(BaseModel):
    platform: str = Field(min_length=1, max_length=50)
    post_type: str = Field(default="standard", max_length=50)
    caption: str = Field(default="")
    hashtags: Optional[list[str]] = None


class PostCreate(PostBase):
    campaign_id: uuid.UUID


class PostUpdate(BaseModel):
    """Content-editing update. Does NOT change ``status`` — status
    transitions must go through the approval state machine endpoints
    (see ``app/routers/approvals.py`` / task #8) so that version history
    and audit logs are always recorded consistently.
    """

    caption: Optional[str] = None
    hashtags: Optional[list[str]] = None
    change_summary: Optional[str] = Field(default=None, max_length=1000)


class PostRead(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    campaign_id: uuid.UUID
    status: PostStatus
    created_by_user_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime
