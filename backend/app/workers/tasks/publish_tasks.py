"""Celery tasks for executing and retrying publish jobs.

``execute_publish_job`` is the REAL worker task referenced in task #9: it
subscribes (conceptually — via direct call after a PublishFailed event) to
publish failures and retries with exponential backoff, honoring
``PUBLISH_RETRY_MAX_ATTEMPTS`` / ``PUBLISH_RETRY_BACKOFF_BASE_SECONDS``
from Settings (mirroring .env.example).

Design note: this task creates its OWN short-lived async DB session/engine
rather than reusing the FastAPI request-scoped session, because Celery
workers are separate OS processes with their own event loop lifecycle —
sharing an AsyncSession across process boundaries is not possible.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from celery.utils.log import get_task_logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.events.bus import event_bus
from app.events.domain_events import Published, PublishFailed
from app.models.enums import PlatformName, PublishJobStatus
from app.models.publish_job import PublishJob
from app.models.schedule import Schedule
from app.social.factory import get_social_adapter
from app.social.schemas import PublishContentRequest
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)
settings = get_settings()


def _make_session_factory() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def _execute_publish_job_async(job_id: str) -> None:
    session_factory = _make_session_factory()
    async with session_factory() as session:
        job = (
            await session.execute(select(PublishJob).where(PublishJob.id == uuid.UUID(job_id)))
        ).scalar_one_or_none()
        if job is None:
            logger.warning("PublishJob %s not found; nothing to do.", job_id)
            return

        job.status = PublishJobStatus.RUNNING
        job.attempt_count += 1
        await session.commit()

        try:
            # Load the Post to get platform + caption, and PlatformAccount for
            # the external account id. Kept minimal (no full repository use)
            # since this runs outside the FastAPI request/DI lifecycle.
            from app.models.platform_account import PlatformAccount
            from app.models.post import Post

            post = (await session.execute(select(Post).where(Post.id == job.post_id))).scalar_one()
            account = (
                await session.execute(
                    select(PlatformAccount).where(PlatformAccount.id == job.platform_account_id)
                )
            ).scalar_one()

            adapter = get_social_adapter(PlatformName(account.platform.value if hasattr(account.platform, "value") else account.platform))
            result = await adapter.publish(
                PublishContentRequest(
                    account_external_id=account.external_account_id,
                    text=post.caption,
                )
            )

            job.status = PublishJobStatus.SUCCEEDED
            job.external_post_id = result.external_post_id
            job.last_error = None
            await session.commit()

            await event_bus.publish(
                Published(
                    organization_id=job.organization_id,
                    publish_job_id=job.id,
                    post_id=job.post_id,
                    platform=account.platform.value if hasattr(account.platform, "value") else str(account.platform),
                    external_post_id=result.external_post_id,
                )
            )
        except Exception as exc:  # noqa: BLE001 - publish failures must not crash the worker
            job.status = PublishJobStatus.FAILED
            job.last_error = str(exc)
            await session.commit()

            await event_bus.publish(
                PublishFailed(
                    organization_id=job.organization_id,
                    publish_job_id=job.id,
                    post_id=job.post_id,
                    platform=str(job.platform_account_id),
                    error_message=str(exc),
                    attempt_count=job.attempt_count,
                )
            )
            # Re-raise so Celery's own retry bookkeeping (if configured) and
            # the caller task below can decide whether to schedule a retry.
            raise


@celery_app.task(name="publish.execute_publish_job", bind=True, max_retries=None)
def execute_publish_job(self, job_id: str) -> None:
    """Entry point: execute a single publish attempt for a PublishJob.

    On failure, schedules a retry via ``retry_publish_job_with_backoff``
    (not Celery's built-in ``self.retry`` decorator) so the backoff
    schedule/attempt cap is computed uniformly from Settings and is
    unit-testable independent of a running Celery worker.
    """
    try:
        asyncio.run(_execute_publish_job_async(job_id))
    except Exception:  # noqa: BLE001
        retry_publish_job_with_backoff.delay(job_id)


def compute_backoff_seconds(attempt_count: int, base_seconds: int) -> int:
    """Exponential backoff: base * 2^(attempt-1), e.g. base=30 -> 30, 60, 120, 240...

    Pure function (no Celery/DB dependency) so it's directly unit-testable.
    """
    return base_seconds * (2 ** max(attempt_count - 1, 0))


@celery_app.task(name="publish.retry_publish_job_with_backoff")
def retry_publish_job_with_backoff(job_id: str) -> None:
    """Look up the job's current attempt_count, and either re-enqueue
    ``execute_publish_job`` after an exponential-backoff delay, or give up
    and leave the job in FAILED state once ``PUBLISH_RETRY_MAX_ATTEMPTS``
    is exceeded.
    """

    async def _check_and_retry() -> None:
        session_factory = _make_session_factory()
        async with session_factory() as session:
            job = (
                await session.execute(select(PublishJob).where(PublishJob.id == uuid.UUID(job_id)))
            ).scalar_one_or_none()
            if job is None:
                return

            if job.attempt_count >= settings.PUBLISH_RETRY_MAX_ATTEMPTS:
                logger.warning(
                    "PublishJob %s exceeded max attempts (%d); giving up.",
                    job_id,
                    settings.PUBLISH_RETRY_MAX_ATTEMPTS,
                )
                job.status = PublishJobStatus.FAILED
                await session.commit()
                return

            delay_seconds = compute_backoff_seconds(
                job.attempt_count, settings.PUBLISH_RETRY_BACKOFF_BASE_SECONDS
            )
            job.status = PublishJobStatus.RETRYING
            job.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
            await session.commit()

            execute_publish_job.apply_async(args=[job_id], countdown=delay_seconds)

    asyncio.run(_check_and_retry())


async def _enqueue_due_schedules_async() -> int:
    session_factory = _make_session_factory()
    async with session_factory() as session:
        stmt = (
            select(Schedule)
            .where(Schedule.scheduled_at <= datetime.now(timezone.utc))
            .where(Schedule.is_cancelled == False)  # noqa: E712
            .order_by(Schedule.scheduled_at.asc())
            .limit(500)
        )
        due = (await session.execute(stmt)).scalars().all()
        if not due:
            return 0

        from app.models.platform_account import PlatformAccount

        enqueued = 0
        for schedule in due:
            job = PublishJob(
                organization_id=schedule.organization_id,
                post_id=schedule.post_id,
                platform_account_id=schedule.platform_account_id,
                status=PublishJobStatus.QUEUED,
            )
            session.add(job)
            schedule.is_cancelled = True
            enqueued += 1

        await session.commit()
        return enqueued


@celery_app.task(name="publish.enqueue_due_schedules")
def enqueue_due_schedules() -> int:
    """Celery beat-polled task: enqueue PublishJobs for due Schedule rows.

    Returns the number of schedules converted into publish jobs in this run.
    """
    return asyncio.run(_enqueue_due_schedules_async())
