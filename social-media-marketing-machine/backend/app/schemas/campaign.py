"""Pydantic request/response schemas for the Campaign resource."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CampaignStatus


class CampaignBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    goal: Optional[str] = Field(default=None, max_length=1000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget_cents: Optional[int] = Field(default=None, ge=0)


class CampaignCreate(CampaignBase):
    client_id: uuid.UUID
    brand_id: Optional[uuid.UUID] = None
    status: CampaignStatus = CampaignStatus.DRAFT


class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    goal: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[CampaignStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget_cents: Optional[int] = Field(default=None, ge=0)
    brand_id: Optional[uuid.UUID] = None


class CampaignRead(CampaignBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    client_id: uuid.UUID
    brand_id: Optional[uuid.UUID]
    status: CampaignStatus
    created_at: datetime
    updated_at: datetime
