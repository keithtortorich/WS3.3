"""Pydantic schemas for the Analytics resource."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional

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


class WeeklyKPIBucket(BaseModel):
    """One week's aggregated KPIs for a campaign.

    ``week_start`` is the Monday of the ISO week the snapshots fall in
    (``docs/sql/smm_gtm_bridge.sql`` 4b uses ``date_trunc('week', ...)``,
    which is Monday-based).
    """

    week_start: date
    post_count: int
    impressions: int
    likes: int
    comments: int
    shares: int
    clicks: int
    engagement_rate: Optional[float] = Field(
        default=None,
        description=(
            "(likes + comments + shares) / impressions for the bucket; "
            "null when the bucket recorded no impressions."
        ),
    )


class CampaignWeeklyRollup(BaseModel):
    """Response envelope for GET /analytics/campaigns/{id}/weekly."""

    campaign_id: uuid.UUID
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    weeks: List[WeeklyKPIBucket]
