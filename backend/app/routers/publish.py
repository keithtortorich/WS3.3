"""Publish router: schedule/enqueue publish jobs.

Real publishing execution happens asynchronously in the Celery worker
(``app/workers/tasks/publish_tasks.py`` — task #9). This router's job is to
create the ``Schedule``/``PublishJob`` rows and (for immediate publish)
enqueue the Celery task; it does not call the social platform API inline
(that would block the request on a third-party HTTP round trip).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_org
from app.core.db import get_db
from app.models.enums import PublishJobStatus
from app.models.publish_job import PublishJob
from app.models.schedule import Schedule
from app.repositories.publish_job_repository import PublishJobRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.schemas.publish import PublishJobRead, PublishRequest, ScheduleRequest

router = APIRouter(prefix="/api/v1/publish", tags=["publish"])


@router.post("/now", response_model=PublishJobRead, status_code=status.HTTP_201_CREATED)
async def publish_now(
    payload: PublishRequest,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> PublishJob:
    """Create a PublishJob and enqueue immediate publication via Celery."""
    repo = PublishJobRepository(db)
    job = PublishJob(
        organization_id=uuid.UUID(org_id),
        post_id=payload.post_id,
        platform_account_id=payload.platform_account_id,
        status=PublishJobStatus.QUEUED,
    )
    job = await repo.create(job)
    await db.commit()
    await db.refresh(job)

    # Local import avoids a hard dependency on a running Celery broker at
    # module import time (useful for tests that never touch this branch).
    from app.workers.tasks.publish_tasks import execute_publish_job

    execute_publish_job.delay(str(job.id))
    return job


@router.post("/schedule", status_code=status.HTTP_201_CREATED)
async def schedule_publish(
    payload: ScheduleRequest,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a future Schedule row. A periodic Celery beat task (out of
    scaffold scope beyond this scheduling primitive) would poll due
    schedules and enqueue PublishJobs at the right time."""
    repo = ScheduleRepository(db)
    schedule = Schedule(
        organization_id=uuid.UUID(org_id),
        post_id=payload.post_id,
        platform_account_id=payload.platform_account_id,
        scheduled_at=payload.scheduled_at,
    )
    schedule = await repo.create(schedule)
    await db.commit()
    await db.refresh(schedule)
    return {"schedule_id": str(schedule.id), "scheduled_at": schedule.scheduled_at.isoformat()}


@router.get("/jobs/{job_id}", response_model=PublishJobRead)
async def get_publish_job(
    job_id: uuid.UUID,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> PublishJob:
    """Fetch a PublishJob's current status (useful for polling from the UI)."""
    repo = PublishJobRepository(db)
    job = await repo.get_by_id(uuid.UUID(org_id), job_id)
    if job is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError(f"PublishJob {job_id} not found.")
    return job
