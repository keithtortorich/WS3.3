"""Pydantic schemas for the Media resource."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MediaType


class MediaCreate(BaseModel):
    """Registers a media asset that was already uploaded to object storage
    (the upload itself happens via a pre-signed URL flow, not this JSON body)."""

    post_id: Optional[uuid.UUID] = None
    media_type: MediaType
    storage_key: str = Field(min_length=1, max_length=1024)
    url: str = Field(min_length=1, max_length=2048)
    mime_type: Optional[str] = Field(default=None, max_length=255)
    size_bytes: Optional[int] = Field(default=None, ge=0)
    width: Optional[int] = Field(default=None, ge=0)
    height: Optional[int] = Field(default=None, ge=0)
    alt_text: Optional[str] = Field(default=None, max_length=1000)
    ai_generated: bool = False


class MediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    post_id: Optional[uuid.UUID]
    media_type: MediaType
    url: str
    mime_type: Optional[str]
    size_bytes: Optional[int]
    width: Optional[int]
    height: Optional[int]
    alt_text: Optional[str]
    ai_generated: bool
    created_at: datetime
