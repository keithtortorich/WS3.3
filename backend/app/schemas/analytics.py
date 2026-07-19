"""Pydantic schemas for the Analytics resource."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AnalyticsSnapshotCreate(BaseModel):
    post_id: uuid.UUID
    captured_at: datetime
    impressions: int = Field(default=0, ge=0)
    likes: int = Field(default=0, ge=0)
    comments_count: int = Field(default=0, ge=0)
    shares: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    engagement_rate: Optional[float] = None
    raw_payload: Optional[dict] = None


class AnalyticsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    post_id: uuid.UUID
    captured_at: datetime
    impressions: int
    likes: int
    comments_count: int
    shares: int
    clicks: int
    engagement_rate: Optional[float]


class CampaignAnalyticsSummary(BaseModel):
    """Aggregate rollup returned by GET /analytics/campaigns/{id}/summary."""

    campaign_id: uuid.UUID
    total_posts: int
    total_impressions: int
    total_likes: int
    total_comments: int
    total_shares: int
    total_clicks: int
    average_engagement_rate: Optional[float]
