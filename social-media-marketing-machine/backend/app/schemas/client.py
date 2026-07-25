"""Pydantic request/response schemas for the Client resource."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClientBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    industry: Optional[str] = Field(default=None, max_length=255)
    website_url: Optional[str] = Field(default=None, max_length=1024)
    contact_name: Optional[str] = Field(default=None, max_length=255)
    contact_email: Optional[str] = Field(default=None, max_length=320)
    notes: Optional[str] = Field(default=None, max_length=4000)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    industry: Optional[str] = Field(default=None, max_length=255)
    website_url: Optional[str] = Field(default=None, max_length=1024)
    contact_name: Optional[str] = Field(default=None, max_length=255)
    contact_email: Optional[str] = Field(default=None, max_length=320)
    notes: Optional[str] = Field(default=None, max_length=4000)
    is_active: Optional[bool] = None


class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
