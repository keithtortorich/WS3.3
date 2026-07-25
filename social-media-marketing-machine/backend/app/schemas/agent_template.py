"""Pydantic request/response schemas for the AgentTemplate resource."""
from __future__ import annotations

import uuid
from typing import List
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentTemplateBase(BaseModel):
    name: str
    description: str | None = None
    template_body: str
    variables: List[str] | None = None
    category: str | None = None


class AgentTemplateCreate(AgentTemplateBase):
    slug: str
    version: int = 1


class AgentTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    template_body: str | None = None
    variables: List[str] | None = None
    category: str | None = None
    is_active: bool | None = None


class AgentTemplateRead(AgentTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    version: int
    is_active: bool
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
