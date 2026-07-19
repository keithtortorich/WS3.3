"""Pydantic request/response schemas for the Brand resource."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BrandBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    voice: Optional[str] = Field(default=None, max_length=2000)
    audience: Optional[str] = Field(default=None, max_length=2000)
    keywords: Optional[list[str]] = None
    logo_url: Optional[str] = Field(default=None, max_length=1024)
    brand_colors: Optional[dict] = None
    guidelines: Optional[str] = Field(default=None, max_length=8000)


class BrandCreate(BrandBase):
    client_id: uuid.UUID


class BrandUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    voice: Optional[str] = Field(default=None, max_length=2000)
    audience: Optional[str] = Field(default=None, max_length=2000)
    keywords: Optional[list[str]] = None
    logo_url: Optional[str] = Field(default=None, max_length=1024)
    brand_colors: Optional[dict] = None
    guidelines: Optional[str] = Field(default=None, max_length=8000)


class BrandRead(BrandBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    client_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
