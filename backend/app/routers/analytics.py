"""Analytics router: record + query performance metrics."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_org
from app.core.db import get_db
from app.models.analytics import Analytics
from app.models.post import Post
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import AnalyticsRead, AnalyticsSnapshotCreate, CampaignAnalyticsSummary
from app.schemas.common import Page

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.post("", response_model=AnalyticsRead, status_code=status.HTTP_201_CREATED)
async def record_analytics_snapshot(
    payload: AnalyticsSnapshotCreate,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Analytics:
    """Record a point-in-time metrics snapshot for a Post (typically called
    by the analytics-sync worker after polling a platform's stats API)."""
    repo = AnalyticsRepository(db)
    snapshot = Analytics(organization_id=uuid.UUID(org_id), **payload.model_dump())
    snapshot = await repo.create(snapshot)
    await db.commit()
    await db.refresh(snapshot)
    return snapshot


@router.get("", response_model=Page[AnalyticsRead])
async def list_analytics(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    post_id: uuid.UUID | None = Query(default=None),
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Page[AnalyticsRead]:
    """List analytics snapshots, optionally filtered by post."""
    repo = AnalyticsRepository(db)
    extra_filters = [Analytics.post_id == post_id] if post_id else None
    result = await repo.list_paginated(
        uuid.UUID(org_id), page=page, page_size=page_size, extra_filters=extra_filters
    )
    return Page[AnalyticsRead](
        items=[AnalyticsRead.model_validate(a) for a in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.get("/campaigns/{campaign_id}/summary", response_model=CampaignAnalyticsSummary)
async def campaign_analytics_summary(
    campaign_id: uuid.UUID,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> CampaignAnalyticsSummary:
    """Aggregate rollup of all analytics snapshots for a campaign's posts."""
    stmt = (
        select(
            func.count(func.distinct(Post.id)),
            func.coalesce(func.sum(Analytics.impressions), 0),
            func.coalesce(func.sum(Analytics.likes), 0),
            func.coalesce(func.sum(Analytics.comments_count), 0),
            func.coalesce(func.sum(Analytics.shares), 0),
            func.coalesce(func.sum(Analytics.clicks), 0),
            func.avg(Analytics.engagement_rate),
        )
        .select_from(Post)
        .outerjoin(Analytics, Analytics.post_id == Post.id)
        .where(Post.campaign_id == campaign_id, Post.organization_id == uuid.UUID(org_id))
    )
    row = (await db.execute(stmt)).one()
    total_posts, impressions, likes, comments_count, shares, clicks, avg_engagement = row
    return CampaignAnalyticsSummary(
        campaign_id=campaign_id,
        total_posts=total_posts or 0,
        total_impressions=impressions or 0,
        total_likes=likes or 0,
        total_comments=comments_count or 0,
        total_shares=shares or 0,
        total_clicks=clicks or 0,
        average_engagement_rate=float(avg_engagement) if avg_engagement is not None else None,
    )
