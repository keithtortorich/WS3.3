"""Analytics router: record + query performance metrics."""
from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_org
from app.core.db import get_db
from app.core.exceptions import NotFoundError
from app.models.analytics import Analytics
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.campaign_repository import CampaignRepository
from app.schemas.analytics import (
    AnalyticsRead,
    AnalyticsSnapshotCreate,
    CampaignAnalyticsSummary,
    CampaignWeeklyRollup,
    WeeklyKPIBucket,
)
from app.schemas.common import Page


def _start_of_day(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.post("", response_model=AnalyticsRead, status_code=status.HTTP_201_CREATED)
async def record_analytics_snapshot(
    payload: AnalyticsSnapshotCreate,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Analytics:
    """Record a point-in-time metrics snapshot for a Post (typically called
    by the analytics-sync worker after polling a platform's stats API).

    Snapshots are immutable: re-posting the same
    ``(post_id, captured_at)`` returns 409 instead of duplicating or
    overwriting the existing observation.
    """
    repo = AnalyticsRepository(db)
    snapshot = Analytics(organization_id=uuid.UUID(org_id), **payload.model_dump())
    snapshot = await repo.create_snapshot(snapshot)
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
    organization_id = uuid.UUID(org_id)
    summary = await AnalyticsRepository(db).campaign_summary(organization_id, campaign_id)
    return CampaignAnalyticsSummary(campaign_id=campaign_id, **summary._asdict())


@router.get("/campaigns/{campaign_id}/weekly", response_model=CampaignWeeklyRollup)
async def campaign_weekly_rollup(
    campaign_id: uuid.UUID,
    start_date: date | None = Query(
        default=None, description="Inclusive first day of the range (UTC)."
    ),
    end_date: date | None = Query(
        default=None, description="Inclusive last day of the range (UTC)."
    ),
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> CampaignWeeklyRollup:
    """Weekly KPI rollup for a campaign (``smm_gtm_bridge.sql`` section 4b).

    Buckets are ISO weeks (Monday start). Weeks with no snapshots are
    absent from the response rather than zero-filled; a range containing no
    snapshots returns an empty ``weeks`` list, not an error.
    """
    organization_id = uuid.UUID(org_id)
    campaign = await CampaignRepository(db).get_by_id(organization_id, campaign_id)
    if campaign is None:
        raise NotFoundError(f"Campaign {campaign_id} not found.")

    start = _start_of_day(start_date) if start_date else None
    # end_date is inclusive for the caller; the query bound is half-open.
    end = _start_of_day(end_date + timedelta(days=1)) if end_date else None

    rows = await AnalyticsRepository(db).weekly_rollup(
        organization_id, campaign_id, start=start, end=end
    )
    return CampaignWeeklyRollup(
        campaign_id=campaign_id,
        start=start,
        end=end,
        weeks=[WeeklyKPIBucket(**row._asdict()) for row in rows],
    )
