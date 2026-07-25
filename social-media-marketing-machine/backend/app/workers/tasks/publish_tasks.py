"""Celery tasks for enqueueing, executing and retrying publish jobs.

Reliability contract implemented here
-------------------------------------
1. **Tenant scoping.** Every task takes ``tenant_id`` explicitly and every
   query filters on ``organization_id``. A task dispatched for org A can
   never read or mutate org B's schedules, posts, accounts or jobs — even
   if it is handed org B's job id.

2. **Idempotence at the data layer.** A publish attempt begins with an
   atomic conditional UPDATE ("the claim"):

       UPDATE publish_jobs
          SET status = 'RUNNING', attempt_count = attempt_count + 1
        WHERE id = :id AND organization_id = :org
          AND status IN ('QUEUED', 'RETRYING')

   Exactly one worker can win that statement; every other concurrent or
   duplicate delivery sees ``rowcount == 0`` and returns without calling
   the platform adapter. This has to be in the database because Celery
   workers are separate OS processes — a module-level "already running"
   set would be per-process and therefore useless.

3. **Bounded retry that actually settles.** A transient failure moves the
   job to ``RETRYING`` with ``last_error`` and ``next_attempt_at`` recorded
   and schedules the next attempt with exponential backoff. Once
   ``attempt_count`` reaches the job's ``max_attempts`` the job settles on
   ``FAILED`` with the error recorded. A :class:`PermanentPublishError`
   (bad post status, missing row, unsupported platform) skips retries and
   goes straight to ``FAILED``.

4. **No swallowed exceptions.** Failures are logged with context and
   re-raised so Celery records the task as failed and monitoring sees it.
   The only deliberately-tolerated errors are execution-graph updates,
   which degrade to a warning rather than losing a real publish.

Design note: these tasks create their OWN short-lived async engine/session
rather than reusing the FastAPI request-scoped session, because Celery
workers are separate OS processes with their own event loop lifecycle.
Every ``_*_async`` helper also accepts an injected ``session`` (and an
injected ``adapter_factory``) so the logic is unit-testable against the
SQLite test session with no broker, no engine and no network.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from celery.utils.log import get_task_logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.events.bus import event_bus
from app.events.domain_events import Published, PublishFailed
from app.models.enums import (
    ExecutionNodeRefType,
    PlatformName,
    PostStatus,
    PublishJobStatus,
    WorkflowNodeStatus,
)
from app.models.platform_account import PlatformAccount
from app.models.post import Post
from app.models.publish_job import PublishJob
from app.models.schedule import Schedule
from app.repositories.execution_node_repository import ExecutionNodeRepository
from app.services.workflow_service import WorkflowService
from app.social.base import SocialPlatformAdapter
from app.social.factory import get_social_adapter
from app.social.schemas import PublishContentRequest
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)
settings = get_settings()

AdapterFactory = Callable[[PlatformName], SocialPlatformAdapter]

#: Statuses a worker is allowed to claim. Anything else (RUNNING, SUCCEEDED,
#: FAILED, CANCELLED) means another worker holds the job or it has settled.
CLAIMABLE_STATUSES = (PublishJobStatus.QUEUED, PublishJobStatus.RETRYING)

#: Post statuses from which publishing is legal. Anything earlier in the
#: approval flow must never reach a platform.
PUBLISHABLE_POST_STATUSES = (PostStatus.APPROVED, PostStatus.SCHEDULED)

#: PublishJob statuses that mean "this post/account pair is already spoken
#: for" — used by the enqueue sweep as a uniqueness guard.
ACTIVE_JOB_STATUSES = (
    PublishJobStatus.QUEUED,
    PublishJobStatus.RUNNING,
    PublishJobStatus.RETRYING,
    PublishJobStatus.SUCCEEDED,
)


class PermanentPublishError(Exception):
    """A failure that retrying cannot fix (missing row, illegal post status,
    unimplemented platform adapter). Settles the job on FAILED immediately."""


class PublishAttemptFailed(Exception):
    """A transient failure with retry budget left. Carries the computed
    backoff so the Celery entry point can schedule the next attempt without
    a second database round trip."""

    def __init__(self, message: str, *, retry_in_seconds: int, attempt_count: int) -> None:
        super().__init__(message)
        self.retry_in_seconds = retry_in_seconds
        self.attempt_count = attempt_count


def _make_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def _as_uuid(value: uuid.UUID | str) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def compute_backoff_seconds(attempt_count: int, base_seconds: int) -> int:
    """Exponential backoff: base * 2^(attempt-1), e.g. base=30 -> 30, 60, 120, 240...

    Pure function (no Celery/DB dependency) so it's directly unit-testable.
    """
    return base_seconds * (2 ** max(attempt_count - 1, 0))


# ---------------------------------------------------------------------------
# Execution graph (execution_nodes) wiring
# ---------------------------------------------------------------------------


async def _sync_execution_node(
    session: AsyncSession,
    *,
    organization_id: uuid.UUID,
    job_id: uuid.UUID,
    new_status: WorkflowNodeStatus,
    failure_reason: Optional[str] = None,
) -> None:
    """Move the execution_nodes row referencing this publish job.

    Goes through the existing :class:`WorkflowService` — no raw SQL and no
    reimplementation of graph semantics. If no node references this job
    (the common case today, since nothing creates PUBLISH_JOB nodes yet)
    this is a no-op. Any failure in the graph layer is logged and swallowed
    on purpose: losing a bookkeeping row must never abort or fail a publish
    that has already been handed to a platform.
    """
    try:
        repo = ExecutionNodeRepository(session)
        node = await repo.get_by_ref(
            organization_id=organization_id,
            ref_type=ExecutionNodeRefType.PUBLISH_JOB,
            ref_id=job_id,
        )
        if node is None:
            logger.debug(
                "No execution node references PublishJob %s (org %s); skipping graph update.",
                job_id,
                organization_id,
            )
            return
        await WorkflowService(session).update_node_status(
            organization_id,
            node_id=node.id,
            new_status=new_status,
            failure_reason=failure_reason,
        )
    except Exception:  # noqa: BLE001 - graph bookkeeping must degrade, not crash publishing
        logger.warning(
            "Failed to update execution node for PublishJob %s (org %s) to %s.",
            job_id,
            organization_id,
            new_status,
            exc_info=True,
        )


# ---------------------------------------------------------------------------
# Publish execution
# ---------------------------------------------------------------------------


async def _load_job(
    session: AsyncSession, organization_id: uuid.UUID, job_id: uuid.UUID
) -> Optional[PublishJob]:
    stmt = select(PublishJob).where(
        PublishJob.id == job_id,
        PublishJob.organization_id == organization_id,
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def _claim_job(
    session: AsyncSession, organization_id: uuid.UUID, job_id: uuid.UUID
) -> bool:
    """Atomically take ownership of a job. Returns True iff this caller won.

    The uniqueness guard lives in the WHERE clause, not in process memory,
    so it holds across Celery worker processes and duplicate deliveries.
    """
    stmt = (
        update(PublishJob)
        .where(
            PublishJob.id == job_id,
            PublishJob.organization_id == organization_id,
            PublishJob.status.in_(CLAIMABLE_STATUSES),
        )
        .values(
            status=PublishJobStatus.RUNNING,
            attempt_count=PublishJob.attempt_count + 1,
            updated_at=datetime.now(timezone.utc),
        )
        .execution_options(synchronize_session=False)
    )
    result = await session.execute(stmt)
    claimed = bool(result.rowcount)
    if claimed:
        await session.commit()
    return claimed


async def _mark_post_published(
    session: AsyncSession, *, post: Post, organization_id: uuid.UUID
) -> None:
    """Advance the Post to PUBLISHED via the approval state machine.

    Never assigns ``post.status`` directly — SCHEDULED -> PUBLISHED is the
    only legal edge, so a post published from APPROVED (immediate publish)
    is left alone rather than forced. Failures here are logged, not raised:
    the content is already live on the platform and the job row is the
    authoritative record of that.
    """
    if post.status != PostStatus.SCHEDULED:
        return
    try:
        from app.services.approval_state_machine import ApprovalStateMachine

        await ApprovalStateMachine(session).transition(
            post=post,
            organization_id=organization_id,
            target_status=PostStatus.PUBLISHED,
            actor_user_id=None,
            reason="Published by publish worker.",
        )
    except Exception:  # noqa: BLE001 - see docstring
        logger.warning(
            "Could not transition Post %s to PUBLISHED after a successful publish.",
            post.id,
            exc_info=True,
        )


async def _settle_failure(
    session: AsyncSession,
    *,
    job: PublishJob,
    organization_id: uuid.UUID,
    error: Exception,
    permanent: bool,
    platform: str = "",
) -> None:
    """Record a failed attempt, choosing RETRYING vs FAILED by the bound."""
    message = f"{type(error).__name__}: {error}"
    max_attempts = job.max_attempts or settings.PUBLISH_RETRY_MAX_ATTEMPTS
    exhausted = permanent or job.attempt_count >= max_attempts

    job.last_error = message
    if exhausted:
        job.status = PublishJobStatus.FAILED
        job.next_attempt_at = None
    else:
        delay = compute_backoff_seconds(
            job.attempt_count, settings.PUBLISH_RETRY_BACKOFF_BASE_SECONDS
        )
        job.status = PublishJobStatus.RETRYING
        job.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=delay)

    if exhausted:
        await _sync_execution_node(
            session,
            organization_id=organization_id,
            job_id=job.id,
            new_status=WorkflowNodeStatus.FAILED,
            failure_reason=message[:1000],
        )
    await session.commit()

    logger.error(
        "PublishJob %s (org %s) attempt %d/%d failed: %s",
        job.id,
        organization_id,
        job.attempt_count,
        max_attempts,
        message,
        exc_info=error,
    )

    await event_bus.publish(
        PublishFailed(
            organization_id=organization_id,
            publish_job_id=job.id,
            post_id=job.post_id,
            platform=platform,
            error_message=message,
            attempt_count=job.attempt_count,
        )
    )

    if exhausted:
        raise error
    raise PublishAttemptFailed(
        message,
        retry_in_seconds=compute_backoff_seconds(
            job.attempt_count, settings.PUBLISH_RETRY_BACKOFF_BASE_SECONDS
        ),
        attempt_count=job.attempt_count,
    ) from error


async def _execute_publish_job_async(
    tenant_id: uuid.UUID | str,
    job_id: uuid.UUID | str,
    *,
    session: Optional[AsyncSession] = None,
    adapter_factory: Optional[AdapterFactory] = None,
) -> str:
    """Run one publish attempt. Returns a short outcome string.

    Outcomes: ``"published"``, ``"not_found"``, ``"already_published"``,
    ``"not_claimed"``. Raises on failure (never swallows).
    """
    if session is None:
        engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
        try:
            async with _make_session_factory(engine)() as owned_session:
                return await _execute_publish_job_async(
                    tenant_id,
                    job_id,
                    session=owned_session,
                    adapter_factory=adapter_factory,
                )
        finally:
            await engine.dispose()

    organization_id = _as_uuid(tenant_id)
    job_uuid = _as_uuid(job_id)
    make_adapter = adapter_factory or get_social_adapter

    job = await _load_job(session, organization_id, job_uuid)
    if job is None:
        # Also covers the cross-tenant case: a job id belonging to another
        # org is indistinguishable from a nonexistent one, by design.
        logger.warning(
            "PublishJob %s not found for org %s; nothing to do.", job_uuid, organization_id
        )
        return "not_found"

    if job.status == PublishJobStatus.SUCCEEDED or job.external_post_id:
        logger.info(
            "PublishJob %s (org %s) already published as %s; skipping duplicate delivery.",
            job_uuid,
            organization_id,
            job.external_post_id,
        )
        return "already_published"

    if not await _claim_job(session, organization_id, job_uuid):
        logger.info(
            "PublishJob %s (org %s) could not be claimed (status=%s); another worker owns it.",
            job_uuid,
            organization_id,
            job.status,
        )
        return "not_claimed"

    await session.refresh(job)

    await _sync_execution_node(
        session,
        organization_id=organization_id,
        job_id=job.id,
        new_status=WorkflowNodeStatus.RUNNING,
    )

    # Resolved inside the try below; kept out here so the failure handlers can
    # report the real platform instead of a placeholder.
    platform: Optional[PlatformName] = None

    try:
        post = (
            await session.execute(
                select(Post).where(
                    Post.id == job.post_id,
                    Post.organization_id == organization_id,
                )
            )
        ).scalar_one_or_none()
        if post is None:
            raise PermanentPublishError(
                f"Post {job.post_id} not found for org {organization_id}."
            )

        if post.status not in PUBLISHABLE_POST_STATUSES:
            raise PermanentPublishError(
                f"Post {post.id} is in status '{post.status.value}'; refusing to publish. "
                f"Publishable statuses: "
                f"{sorted(s.value for s in PUBLISHABLE_POST_STATUSES)}."
            )

        account = (
            await session.execute(
                select(PlatformAccount).where(
                    PlatformAccount.id == job.platform_account_id,
                    PlatformAccount.organization_id == organization_id,
                )
            )
        ).scalar_one_or_none()
        if account is None:
            raise PermanentPublishError(
                f"PlatformAccount {job.platform_account_id} not found for org {organization_id}."
            )

        platform = (
            account.platform
            if isinstance(account.platform, PlatformName)
            else PlatformName(str(account.platform))
        )

        try:
            adapter = make_adapter(platform)
        except ValueError as exc:
            raise PermanentPublishError(str(exc)) from exc

        result = await adapter.publish(
            PublishContentRequest(
                account_external_id=account.external_account_id,
                text=post.caption,
            )
        )
    except (NotImplementedError, PermanentPublishError) as exc:
        # Stub adapter / illegal post status / missing row — retrying will
        # never help, so settle straight on FAILED.
        await _settle_failure(
            session,
            job=job,
            organization_id=organization_id,
            error=exc,
            permanent=True,
            platform=platform.value if platform else "",
        )
        raise  # unreachable; _settle_failure always raises
    except Exception as exc:  # noqa: BLE001 - classified as transient, re-raised below
        await _settle_failure(
            session,
            job=job,
            organization_id=organization_id,
            error=exc,
            permanent=False,
            platform=platform.value if platform else "",
        )
        raise

    job.status = PublishJobStatus.SUCCEEDED
    job.external_post_id = result.external_post_id
    job.last_error = None
    job.next_attempt_at = None

    await _mark_post_published(session, post=post, organization_id=organization_id)
    await _sync_execution_node(
        session,
        organization_id=organization_id,
        job_id=job.id,
        new_status=WorkflowNodeStatus.SUCCEEDED,
    )
    await session.commit()

    await event_bus.publish(
        Published(
            organization_id=organization_id,
            publish_job_id=job.id,
            post_id=job.post_id,
            platform=platform.value,
            external_post_id=result.external_post_id,
        )
    )
    logger.info(
        "PublishJob %s (org %s) published to %s as %s.",
        job.id,
        organization_id,
        platform.value,
        result.external_post_id,
    )
    return "published"


@celery_app.task(name="publish.execute_publish_job", bind=True, max_retries=None)
def execute_publish_job(self, tenant_id: str, job_id: str) -> str:
    """Execute a single publish attempt for a PublishJob owned by ``tenant_id``.

    Retries are scheduled explicitly (not via Celery's ``self.retry``) so the
    backoff schedule and attempt cap are computed uniformly from the job row
    plus Settings, and are unit-testable without a running worker. The
    exception is always re-raised so a failure surfaces in Celery's result
    backend and in monitoring instead of disappearing.
    """
    try:
        return asyncio.run(_execute_publish_job_async(tenant_id, job_id))
    except PublishAttemptFailed as exc:
        logger.warning(
            "Scheduling retry for PublishJob %s (org %s) in %ds after attempt %d.",
            job_id,
            tenant_id,
            exc.retry_in_seconds,
            exc.attempt_count,
        )
        execute_publish_job.apply_async(
            args=[str(tenant_id), str(job_id)], countdown=exc.retry_in_seconds
        )
        raise
    except Exception:
        logger.exception(
            "PublishJob %s (org %s) failed permanently.", job_id, tenant_id
        )
        raise


@celery_app.task(name="publish.retry_publish_job_with_backoff")
def retry_publish_job_with_backoff(tenant_id: str, job_id: str) -> None:
    """Re-drive a job that is sitting in RETRYING, or settle it on FAILED.

    Kept as a separate entry point so an operator (or a PublishFailed
    subscriber) can ask for a retry without re-running the attempt inline.
    It re-checks the bound itself, so calling it on an exhausted job settles
    the job rather than looping forever.
    """

    async def _check_and_retry() -> None:
        engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
        try:
            async with _make_session_factory(engine)() as session:
                await _retry_publish_job_async(tenant_id, job_id, session=session)
        finally:
            await engine.dispose()

    asyncio.run(_check_and_retry())


async def _retry_publish_job_async(
    tenant_id: uuid.UUID | str,
    job_id: uuid.UUID | str,
    *,
    session: AsyncSession,
) -> Optional[int]:
    """Returns the scheduled delay in seconds, or None if nothing was scheduled."""
    organization_id = _as_uuid(tenant_id)
    job_uuid = _as_uuid(job_id)

    job = await _load_job(session, organization_id, job_uuid)
    if job is None:
        logger.warning(
            "PublishJob %s not found for org %s; not retrying.", job_uuid, organization_id
        )
        return None

    if job.status in (PublishJobStatus.SUCCEEDED, PublishJobStatus.CANCELLED):
        return None

    max_attempts = job.max_attempts or settings.PUBLISH_RETRY_MAX_ATTEMPTS
    if job.attempt_count >= max_attempts:
        logger.warning(
            "PublishJob %s (org %s) exceeded max attempts (%d); giving up.",
            job_uuid,
            organization_id,
            max_attempts,
        )
        job.status = PublishJobStatus.FAILED
        job.next_attempt_at = None
        await _sync_execution_node(
            session,
            organization_id=organization_id,
            job_id=job.id,
            new_status=WorkflowNodeStatus.FAILED,
            failure_reason=(job.last_error or "Exceeded max publish attempts.")[:1000],
        )
        await session.commit()
        return None

    delay_seconds = compute_backoff_seconds(
        job.attempt_count, settings.PUBLISH_RETRY_BACKOFF_BASE_SECONDS
    )
    job.status = PublishJobStatus.RETRYING
    job.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
    await session.commit()

    execute_publish_job.apply_async(
        args=[str(organization_id), str(job_uuid)], countdown=delay_seconds
    )
    return delay_seconds


# ---------------------------------------------------------------------------
# Due-schedule sweep
# ---------------------------------------------------------------------------


async def _enqueue_due_schedules_async(
    session: Optional[AsyncSession] = None,
    *,
    tenant_id: uuid.UUID | str | None = None,
    now: Optional[datetime] = None,
    limit: int = 500,
) -> int:
    """Convert due Schedule rows into QUEUED PublishJob rows.

    A schedule is enqueued only when ALL of the following hold:
      * ``scheduled_at`` has passed,
      * the schedule is not cancelled,
      * its Post belongs to the same organization as the schedule, and
      * that Post is in APPROVED or SCHEDULED status.

    Nothing earlier in the approval flow (DRAFT, INTERNAL_REVIEW,
    CLIENT_REVIEW, REJECTED) can reach a platform, and neither can an
    already-PUBLISHED or ARCHIVED post.

    When ``tenant_id`` is given the sweep is restricted to that organization;
    the beat-driven call intentionally sweeps every org, but each created job
    inherits its schedule's ``organization_id``, never a caller-supplied one.
    """
    if session is None:
        engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
        try:
            async with _make_session_factory(engine)() as owned_session:
                return await _enqueue_due_schedules_async(
                    owned_session, tenant_id=tenant_id, now=now, limit=limit
                )
        finally:
            await engine.dispose()

    cutoff = now or datetime.now(timezone.utc)

    stmt = (
        select(Schedule, Post)
        .join(
            Post,
            (Post.id == Schedule.post_id)
            # Tenant integrity on the join itself: a schedule can never pick
            # up another org's post even if post_id somehow collided.
            & (Post.organization_id == Schedule.organization_id),
        )
        .where(Schedule.scheduled_at <= cutoff)
        .where(Schedule.is_cancelled.is_(False))
        # "Not yet consumed by a previous sweep." Distinct from is_cancelled so
        # a published schedule stays visible on the calendar.
        .where(Schedule.enqueued_at.is_(None))
        .where(Post.status.in_(PUBLISHABLE_POST_STATUSES))
        .order_by(Schedule.scheduled_at.asc())
        .limit(limit)
    )
    if tenant_id is not None:
        stmt = stmt.where(Schedule.organization_id == _as_uuid(tenant_id))

    rows = (await session.execute(stmt)).all()
    if not rows:
        return 0

    enqueued = 0
    for schedule, _post in rows:
        # Uniqueness guard: never create a second live job for a
        # (post, account) pair the system is already working on or has
        # already published. Belt-and-braces with the claim in
        # ``_claim_job`` — this one stops the duplicate ever existing.
        existing = (
            await session.execute(
                select(PublishJob.id)
                .where(
                    PublishJob.organization_id == schedule.organization_id,
                    PublishJob.post_id == schedule.post_id,
                    PublishJob.platform_account_id == schedule.platform_account_id,
                    PublishJob.status.in_(ACTIVE_JOB_STATUSES),
                )
                .limit(1)
            )
        ).first()
        if existing is not None:
            logger.info(
                "Schedule %s (org %s) already has an active publish job; skipping.",
                schedule.id,
                schedule.organization_id,
            )
            # Still consume the schedule so the sweep doesn't re-examine it
            # on every beat tick.
            schedule.enqueued_at = cutoff
            continue

        job = PublishJob(
            organization_id=schedule.organization_id,
            post_id=schedule.post_id,
            platform_account_id=schedule.platform_account_id,
            status=PublishJobStatus.QUEUED,
        )
        session.add(job)
        # Mark the schedule consumed so the sweep does not re-enqueue it on the
        # next beat tick. This is ``enqueued_at``, NOT ``is_cancelled``: the two
        # mean different things, and conflating them hid published posts from
        # GET /api/v1/calendar, which filters on is_cancelled. See migration
        # e00c25c0041f.
        schedule.enqueued_at = cutoff
        enqueued += 1

    await session.commit()
    return enqueued


@celery_app.task(name="publish.enqueue_due_schedules")
def enqueue_due_schedules(tenant_id: str | None = None) -> int:
    """Celery beat-polled task: enqueue PublishJobs for due Schedule rows.

    Returns the number of schedules converted into publish jobs in this run.
    """
    return asyncio.run(_enqueue_due_schedules_async(tenant_id=tenant_id))
