"""Calendar router: aggregated view of Schedules joined with Post/Platform
info, driving the frontend's content calendar page."""
from __future__ import annotations

import uuid
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_org
from app.core.db import get_db
from app.models.post import Post
from app.models.schedule import Schedule

router = APIRouter(prefix="/api/v1/calendar", tags=["calendar"])


@router.get("", response_model=list[dict])
async def get_calendar(
    start_date: date = Query(...),
    end_date: date = Query(...),
    campaign_id: uuid.UUID | None = Query(default=None),
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Return all scheduled posts between start_date and end_date (inclusive)."""
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)

    stmt = (
        select(Schedule, Post)
        .join(Post, Post.id == Schedule.post_id)
        .where(
            Schedule.organization_id == uuid.UUID(org_id),
            Schedule.scheduled_at >= start_dt,
            Schedule.scheduled_at <= end_dt,
            Schedule.is_cancelled.is_(False),
        )
        .order_by(Schedule.scheduled_at)
    )
    if campaign_id:
        stmt = stmt.where(Post.campaign_id == campaign_id)

    rows = (await db.execute(stmt)).all()
    return [
        {
            "schedule_id": str(schedule.id),
            "post_id": str(post.id),
            "platform_account_id": str(schedule.platform_account_id),
            "scheduled_at": schedule.scheduled_at.isoformat(),
            "platform": post.platform,
            "post_status": post.status.value,
            "caption_preview": (post.caption or "")[:120],
        }
        for schedule, post in rows
    ]
