"""Unit tests for Celery beat due-schedule polling / enqueue logic."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models.enums import PublishJobStatus
from app.models.publish_job import PublishJob
from app.models.schedule import Schedule
from app.workers.tasks.publish_tasks import _enqueue_due_schedules_async


async def _make_schedule(db_session, scheduled_at: datetime, cancelled: bool = False) -> Schedule:
    schedule = Schedule(
        organization_id=uuid.uuid4(),
        post_id=uuid.uuid4(),
        platform_account_id=uuid.uuid4(),
        scheduled_at=scheduled_at,
        is_cancelled=cancelled,
    )
    db_session.add(schedule)
    await db_session.flush()
    return schedule


@pytest.mark.asyncio
async def test_enqueue_no_due_schedules_returns_zero(db_session):
    enqueued = await _enqueue_due_schedules_async(session=db_session)
    assert enqueued == 0

    jobs = (await db_session.execute(select(PublishJob))).scalars().all()
    assert jobs == []


@pytest.mark.asyncio
async def test_enqueue_single_due_schedule_creates_publish_job_and_cancels_schedule(db_session):
    scheduled_at = datetime.now(timezone.utc)
    schedule = await _make_schedule(db_session, scheduled_at=scheduled_at)
    await db_session.commit()

    enqueued = await _enqueue_due_schedules_async(session=db_session)
    assert enqueued == 1

    job = (
        await db_session.execute(
            select(PublishJob).where(PublishJob.organization_id == schedule.organization_id)
        )
    ).scalar_one_or_none()
    assert job is not None
    assert job.post_id == schedule.post_id
    assert job.platform_account_id == schedule.platform_account_id
    assert job.status == PublishJobStatus.QUEUED
    assert job.attempt_count == 0

    await db_session.refresh(schedule)
    assert schedule.is_cancelled is True


@pytest.mark.asyncio
async def test_enqueue_skips_future_schedules(db_session):
    future = datetime.now(timezone.utc) + timedelta(minutes=5)
    future_schedule = await _make_schedule(db_session, scheduled_at=future)
    due = await _make_schedule(db_session, scheduled_at=datetime.now(timezone.utc))
    await db_session.commit()

    enqueued = await _enqueue_due_schedules_async(session=db_session)
    assert enqueued == 1

    jobs = (await db_session.execute(select(PublishJob))).scalars().all()
    assert len(jobs) == 1
    assert jobs[0].post_id == due.post_id


@pytest.mark.asyncio
async def test_enqueue_skips_already_cancelled_schedules(db_session):
    await _make_schedule(db_session, scheduled_at=datetime.now(timezone.utc), cancelled=True)
    await db_session.commit()

    enqueued = await _enqueue_due_schedules_async(session=db_session)
    assert enqueued == 0


@pytest.mark.asyncio
async def test_enqueue_multiple_due_schedules_ordered_by_scheduled_at(db_session):
    earlier = datetime.now(timezone.utc)
    later = datetime.now(timezone.utc)
    s1 = await _make_schedule(db_session, scheduled_at=earlier)
    s2 = await _make_schedule(db_session, scheduled_at=later)
    await db_session.commit()

    enqueued = await _enqueue_due_schedules_async(session=db_session)
    assert enqueued == 2

    jobs = (
        await db_session.execute(select(PublishJob).order_by(PublishJob.created_at.asc()))
    ).scalars().all()
    assert len(jobs) == 2
    assert jobs[0].post_id == s1.post_id
    assert jobs[1].post_id == s2.post_id
