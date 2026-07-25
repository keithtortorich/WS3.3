"""Unit tests for the publish pipeline: due-schedule sweep, publish execution,
retry/backoff, idempotence, and tenant isolation.

Everything runs against the SQLite test session with a fake adapter injected —
no Celery broker, no engine of our own, no network.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models.campaign import Campaign
from app.models.client import Client
from app.models.enums import (
    ExecutionNodeRefType,
    PlatformName,
    PostStatus,
    PublishJobStatus,
    WorkflowNodeStatus,
    WorkflowNodeType,
)
from app.models.execution_node import ExecutionNode
from app.models.platform_account import PlatformAccount
from app.models.post import Post
from app.models.publish_job import PublishJob
from app.models.schedule import Schedule
from app.social.schemas import PublishContentResponse
from app.workers.tasks.publish_tasks import (
    PermanentPublishError,
    PublishAttemptFailed,
    _enqueue_due_schedules_async,
    _execute_publish_job_async,
    _retry_publish_job_async,
    compute_backoff_seconds,
)


# ---------------------------------------------------------------------------
# Fakes and fixtures
# ---------------------------------------------------------------------------


class FakeAdapter:
    """Injectable stand-in for a SocialPlatformAdapter. Records calls so tests
    can assert the platform was hit exactly once."""

    def __init__(self, platform: PlatformName, *, fail_times: int = 0, error: Exception | None = None):
        self.platform = platform
        self.calls: list[str] = []
        self._fail_times = fail_times
        self._error = error or RuntimeError("transient upstream error")

    async def publish(self, request):
        self.calls.append(request.text)
        if self._fail_times > 0:
            self._fail_times -= 1
            raise self._error
        return PublishContentResponse(
            external_post_id=f"ext-{len(self.calls)}",
            platform=self.platform.value,
            published_at=datetime.now(timezone.utc),
        )


def factory_for(adapter: FakeAdapter):
    def _factory(platform: PlatformName):
        return adapter

    return _factory


async def _make_post(db_session, org_id: uuid.UUID, status: PostStatus = PostStatus.APPROVED) -> Post:
    """Create a Post row. ``status`` is set at construction time (transient
    object), which the model's direct-write guard permits — this is creation,
    not a transition."""
    client = Client(organization_id=org_id, name="Acme")
    db_session.add(client)
    await db_session.flush()
    campaign = Campaign(organization_id=org_id, client_id=client.id, name="C1")
    db_session.add(campaign)
    await db_session.flush()
    post = Post(
        organization_id=org_id,
        campaign_id=campaign.id,
        platform="linkedin",
        caption="hello world",
        status=status,
    )
    db_session.add(post)
    await db_session.flush()
    return post


async def _make_account(db_session, org_id: uuid.UUID) -> PlatformAccount:
    from app.models.brand import Brand

    client = Client(organization_id=org_id, name="Acme")
    db_session.add(client)
    await db_session.flush()
    brand = Brand(organization_id=org_id, client_id=client.id, name="Brand")
    db_session.add(brand)
    await db_session.flush()
    account = PlatformAccount(
        organization_id=org_id,
        brand_id=brand.id,
        platform=PlatformName.LINKEDIN,
        external_account_id="urn:li:org:1",
    )
    db_session.add(account)
    await db_session.flush()
    return account


async def _make_job(db_session, org_id, post, account, **kwargs) -> PublishJob:
    job = PublishJob(
        organization_id=org_id,
        post_id=post.id,
        platform_account_id=account.id,
        status=kwargs.pop("status", PublishJobStatus.QUEUED),
        **kwargs,
    )
    db_session.add(job)
    await db_session.flush()
    return job


async def _make_schedule(
    db_session,
    scheduled_at: datetime,
    cancelled: bool = False,
    *,
    org_id: uuid.UUID | None = None,
    post: Post | None = None,
    post_status: PostStatus = PostStatus.APPROVED,
) -> Schedule:
    org_id = org_id or uuid.uuid4()
    if post is None:
        post = await _make_post(db_session, org_id, status=post_status)
    account = await _make_account(db_session, org_id)
    schedule = Schedule(
        organization_id=org_id,
        post_id=post.id,
        platform_account_id=account.id,
        scheduled_at=scheduled_at,
        is_cancelled=cancelled,
    )
    db_session.add(schedule)
    await db_session.flush()
    return schedule


# ---------------------------------------------------------------------------
# Due-schedule sweep
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enqueue_no_due_schedules_returns_zero(db_session):
    enqueued = await _enqueue_due_schedules_async(db_session)
    assert enqueued == 0

    jobs = (await db_session.execute(select(PublishJob))).scalars().all()
    assert jobs == []


@pytest.mark.asyncio
async def test_enqueue_single_due_schedule_creates_publish_job_and_consumes_schedule(db_session):
    schedule = await _make_schedule(db_session, scheduled_at=datetime.now(timezone.utc))
    await db_session.commit()

    enqueued = await _enqueue_due_schedules_async(db_session)
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
    # Consumed via enqueued_at. is_cancelled MUST stay False: the calendar
    # filters on it, so marking a published schedule cancelled would erase the
    # post from the customer's calendar. These two flags mean different things.
    assert schedule.enqueued_at is not None
    assert schedule.is_cancelled is False


@pytest.mark.asyncio
async def test_published_schedule_stays_visible_to_the_calendar(db_session):
    """Regression: consuming a schedule must not hide it from the calendar.

    GET /api/v1/calendar filters on ``is_cancelled.is_(False)``. The sweep used
    to set ``is_cancelled = True`` to mean "already handled", which silently
    removed every published post from the calendar view. This asserts against
    the same predicate the calendar router uses.
    """
    schedule = await _make_schedule(db_session, scheduled_at=datetime.now(timezone.utc))
    await db_session.commit()

    assert await _enqueue_due_schedules_async(db_session) == 1

    visible = (
        (
            await db_session.execute(
                select(Schedule).where(
                    Schedule.organization_id == schedule.organization_id,
                    Schedule.is_cancelled.is_(False),
                )
            )
        )
        .scalars()
        .all()
    )
    assert [s.id for s in visible] == [schedule.id]


@pytest.mark.asyncio
async def test_enqueue_does_not_reprocess_an_already_consumed_schedule(db_session):
    """A second beat tick must not create a duplicate job for the same row."""
    await _make_schedule(db_session, scheduled_at=datetime.now(timezone.utc))
    await db_session.commit()

    assert await _enqueue_due_schedules_async(db_session) == 1
    assert await _enqueue_due_schedules_async(db_session) == 0

    jobs = (await db_session.execute(select(PublishJob))).scalars().all()
    assert len(jobs) == 1


@pytest.mark.asyncio
async def test_enqueue_skips_future_schedules(db_session):
    await _make_schedule(db_session, scheduled_at=datetime.now(timezone.utc) + timedelta(minutes=5))
    due = await _make_schedule(db_session, scheduled_at=datetime.now(timezone.utc))
    await db_session.commit()

    enqueued = await _enqueue_due_schedules_async(db_session)
    assert enqueued == 1

    jobs = (await db_session.execute(select(PublishJob))).scalars().all()
    assert len(jobs) == 1
    assert jobs[0].post_id == due.post_id


@pytest.mark.asyncio
async def test_enqueue_skips_already_cancelled_schedules(db_session):
    await _make_schedule(db_session, scheduled_at=datetime.now(timezone.utc), cancelled=True)
    await db_session.commit()

    assert await _enqueue_due_schedules_async(db_session) == 0
    assert (await db_session.execute(select(PublishJob))).scalars().all() == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        PostStatus.DRAFT,
        PostStatus.INTERNAL_REVIEW,
        PostStatus.CLIENT_REVIEW,
        PostStatus.REJECTED,
        PostStatus.PUBLISHED,
        PostStatus.ARCHIVED,
    ],
)
async def test_enqueue_never_enqueues_a_post_that_is_not_publishable(db_session, status):
    """A schedule whose post has not reached APPROVED/SCHEDULED must never
    produce a PublishJob, no matter how overdue it is."""
    await _make_schedule(
        db_session,
        scheduled_at=datetime.now(timezone.utc) - timedelta(hours=2),
        post_status=status,
    )
    await db_session.commit()

    assert await _enqueue_due_schedules_async(db_session) == 0
    assert (await db_session.execute(select(PublishJob))).scalars().all() == []


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [PostStatus.APPROVED, PostStatus.SCHEDULED])
async def test_enqueue_accepts_approved_and_scheduled_posts(db_session, status):
    await _make_schedule(db_session, scheduled_at=datetime.now(timezone.utc), post_status=status)
    await db_session.commit()

    assert await _enqueue_due_schedules_async(db_session) == 1


@pytest.mark.asyncio
async def test_enqueue_multiple_due_schedules_ordered_by_scheduled_at(db_session):
    now = datetime.now(timezone.utc)
    s1 = await _make_schedule(db_session, scheduled_at=now - timedelta(minutes=2))
    s2 = await _make_schedule(db_session, scheduled_at=now - timedelta(minutes=1))
    await db_session.commit()

    assert await _enqueue_due_schedules_async(db_session) == 2

    jobs = (
        await db_session.execute(select(PublishJob).order_by(PublishJob.created_at.asc()))
    ).scalars().all()
    assert {j.post_id for j in jobs} == {s1.post_id, s2.post_id}


@pytest.mark.asyncio
async def test_enqueue_does_not_create_a_second_job_for_an_active_pair(db_session):
    """Uniqueness guard: if a live job already exists for the same
    (post, platform_account), the sweep must not create a duplicate."""
    org_id = uuid.uuid4()
    post = await _make_post(db_session, org_id)
    schedule = await _make_schedule(
        db_session, scheduled_at=datetime.now(timezone.utc), org_id=org_id, post=post
    )
    db_session.add(
        PublishJob(
            organization_id=org_id,
            post_id=post.id,
            platform_account_id=schedule.platform_account_id,
            status=PublishJobStatus.RUNNING,
        )
    )
    await db_session.commit()

    assert await _enqueue_due_schedules_async(db_session) == 0
    jobs = (await db_session.execute(select(PublishJob))).scalars().all()
    assert len(jobs) == 1


@pytest.mark.asyncio
async def test_enqueue_scoped_to_tenant_ignores_other_orgs(db_session):
    """CROSS-TENANT: a sweep for org A must not touch org B's schedules."""
    org_a, org_b = uuid.uuid4(), uuid.uuid4()
    sched_a = await _make_schedule(db_session, scheduled_at=datetime.now(timezone.utc), org_id=org_a)
    sched_b = await _make_schedule(db_session, scheduled_at=datetime.now(timezone.utc), org_id=org_b)
    await db_session.commit()

    assert await _enqueue_due_schedules_async(db_session, tenant_id=org_a) == 1

    jobs = (await db_session.execute(select(PublishJob))).scalars().all()
    assert len(jobs) == 1
    assert jobs[0].organization_id == org_a

    await db_session.refresh(sched_b)
    assert sched_b.enqueued_at is None, "org B's schedule must be untouched"
    assert sched_b.is_cancelled is False
    await db_session.refresh(sched_a)
    assert sched_a.enqueued_at is not None
    assert sched_a.is_cancelled is False


# ---------------------------------------------------------------------------
# Publish execution — success, idempotence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_publish_success_marks_job_succeeded_and_records_external_id(db_session):
    org_id = uuid.uuid4()
    post = await _make_post(db_session, org_id)
    account = await _make_account(db_session, org_id)
    job = await _make_job(db_session, org_id, post, account)
    await db_session.commit()

    adapter = FakeAdapter(PlatformName.LINKEDIN)
    outcome = await _execute_publish_job_async(
        org_id, job.id, session=db_session, adapter_factory=factory_for(adapter)
    )

    assert outcome == "published"
    await db_session.refresh(job)
    assert job.status == PublishJobStatus.SUCCEEDED
    assert job.external_post_id == "ext-1"
    assert job.last_error is None
    assert job.attempt_count == 1
    assert adapter.calls == ["hello world"]


@pytest.mark.asyncio
async def test_running_the_same_job_twice_publishes_exactly_once(db_session):
    """IDEMPOTENCE: a duplicate delivery must not double-publish."""
    org_id = uuid.uuid4()
    post = await _make_post(db_session, org_id)
    account = await _make_account(db_session, org_id)
    job = await _make_job(db_session, org_id, post, account)
    await db_session.commit()

    adapter = FakeAdapter(PlatformName.LINKEDIN)
    first = await _execute_publish_job_async(
        org_id, job.id, session=db_session, adapter_factory=factory_for(adapter)
    )
    second = await _execute_publish_job_async(
        org_id, job.id, session=db_session, adapter_factory=factory_for(adapter)
    )

    assert first == "published"
    assert second == "already_published"
    assert len(adapter.calls) == 1, "adapter must be called exactly once"

    await db_session.refresh(job)
    assert job.attempt_count == 1


@pytest.mark.asyncio
async def test_a_job_already_claimed_by_another_worker_is_not_published(db_session):
    """A job sitting in RUNNING (claimed elsewhere) must not be re-claimed."""
    org_id = uuid.uuid4()
    post = await _make_post(db_session, org_id)
    account = await _make_account(db_session, org_id)
    job = await _make_job(db_session, org_id, post, account, status=PublishJobStatus.RUNNING)
    await db_session.commit()

    adapter = FakeAdapter(PlatformName.LINKEDIN)
    outcome = await _execute_publish_job_async(
        org_id, job.id, session=db_session, adapter_factory=factory_for(adapter)
    )

    assert outcome == "not_claimed"
    assert adapter.calls == []


# ---------------------------------------------------------------------------
# Publish execution — retry and permanent failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transient_failure_sets_retrying_then_eventually_succeeds(db_session):
    org_id = uuid.uuid4()
    post = await _make_post(db_session, org_id)
    account = await _make_account(db_session, org_id)
    job = await _make_job(db_session, org_id, post, account, max_attempts=3)
    await db_session.commit()

    adapter = FakeAdapter(PlatformName.LINKEDIN, fail_times=1)
    factory = factory_for(adapter)

    with pytest.raises(PublishAttemptFailed) as excinfo:
        await _execute_publish_job_async(
            org_id, job.id, session=db_session, adapter_factory=factory
        )
    assert excinfo.value.retry_in_seconds > 0

    await db_session.refresh(job)
    assert job.status == PublishJobStatus.RETRYING
    assert job.attempt_count == 1
    assert "transient upstream error" in job.last_error
    assert job.next_attempt_at is not None

    # Second delivery (what the scheduled retry would do) succeeds.
    outcome = await _execute_publish_job_async(
        org_id, job.id, session=db_session, adapter_factory=factory
    )
    assert outcome == "published"

    await db_session.refresh(job)
    assert job.status == PublishJobStatus.SUCCEEDED
    assert job.attempt_count == 2
    assert job.last_error is None
    assert job.next_attempt_at is None
    assert len(adapter.calls) == 2


@pytest.mark.asyncio
async def test_failure_settles_on_failed_once_max_attempts_reached(db_session):
    org_id = uuid.uuid4()
    post = await _make_post(db_session, org_id)
    account = await _make_account(db_session, org_id)
    job = await _make_job(db_session, org_id, post, account, max_attempts=2)
    await db_session.commit()

    adapter = FakeAdapter(PlatformName.LINKEDIN, fail_times=99)
    factory = factory_for(adapter)

    with pytest.raises(PublishAttemptFailed):
        await _execute_publish_job_async(org_id, job.id, session=db_session, adapter_factory=factory)
    await db_session.refresh(job)
    assert job.status == PublishJobStatus.RETRYING

    # Second (final) attempt: the bound is reached, so it settles on FAILED
    # and the original exception propagates rather than being swallowed.
    with pytest.raises(RuntimeError, match="transient upstream error"):
        await _execute_publish_job_async(org_id, job.id, session=db_session, adapter_factory=factory)

    await db_session.refresh(job)
    assert job.status == PublishJobStatus.FAILED
    assert job.attempt_count == 2
    assert "transient upstream error" in job.last_error
    assert job.next_attempt_at is None


@pytest.mark.asyncio
async def test_publish_refuses_a_post_that_is_not_approved(db_session):
    """Defense in depth: even if a job exists (e.g. via /publish/now), a
    DRAFT post must never reach the adapter, and must fail permanently."""
    org_id = uuid.uuid4()
    post = await _make_post(db_session, org_id, status=PostStatus.DRAFT)
    account = await _make_account(db_session, org_id)
    job = await _make_job(db_session, org_id, post, account, max_attempts=5)
    await db_session.commit()

    adapter = FakeAdapter(PlatformName.LINKEDIN)
    with pytest.raises(PermanentPublishError, match="refusing to publish"):
        await _execute_publish_job_async(
            org_id, job.id, session=db_session, adapter_factory=factory_for(adapter)
        )

    assert adapter.calls == []
    await db_session.refresh(job)
    # FAILED immediately despite 4 attempts of budget remaining.
    assert job.status == PublishJobStatus.FAILED
    assert job.attempt_count == 1
    assert "draft" in job.last_error


@pytest.mark.asyncio
async def test_missing_platform_account_fails_permanently(db_session):
    org_id = uuid.uuid4()
    post = await _make_post(db_session, org_id)
    account = await _make_account(db_session, org_id)
    job = await _make_job(db_session, org_id, post, account)
    job.platform_account_id = uuid.uuid4()  # dangling reference
    await db_session.commit()

    with pytest.raises(PermanentPublishError, match="PlatformAccount"):
        await _execute_publish_job_async(
            org_id,
            job.id,
            session=db_session,
            adapter_factory=factory_for(FakeAdapter(PlatformName.LINKEDIN)),
        )

    await db_session.refresh(job)
    assert job.status == PublishJobStatus.FAILED


# ---------------------------------------------------------------------------
# Cross-tenant isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_task_for_org_a_cannot_touch_org_b_job(db_session):
    """CROSS-TENANT: executing org B's job id under org A's tenant_id must be
    a no-op — no adapter call, no status change on B's row."""
    org_a, org_b = uuid.uuid4(), uuid.uuid4()
    post_b = await _make_post(db_session, org_b)
    account_b = await _make_account(db_session, org_b)
    job_b = await _make_job(db_session, org_b, post_b, account_b)
    await db_session.commit()

    adapter = FakeAdapter(PlatformName.LINKEDIN)
    outcome = await _execute_publish_job_async(
        org_a, job_b.id, session=db_session, adapter_factory=factory_for(adapter)
    )

    assert outcome == "not_found"
    assert adapter.calls == []
    await db_session.refresh(job_b)
    assert job_b.status == PublishJobStatus.QUEUED
    assert job_b.attempt_count == 0


@pytest.mark.asyncio
async def test_retry_task_for_org_a_cannot_touch_org_b_job(db_session):
    org_a, org_b = uuid.uuid4(), uuid.uuid4()
    post_b = await _make_post(db_session, org_b)
    account_b = await _make_account(db_session, org_b)
    job_b = await _make_job(
        db_session, org_b, post_b, account_b, status=PublishJobStatus.RETRYING, attempt_count=9
    )
    await db_session.commit()

    assert await _retry_publish_job_async(org_a, job_b.id, session=db_session) is None

    await db_session.refresh(job_b)
    assert job_b.status == PublishJobStatus.RETRYING, "org B's job must be untouched"


@pytest.mark.asyncio
async def test_retry_task_settles_exhausted_job_on_failed(db_session):
    org_id = uuid.uuid4()
    post = await _make_post(db_session, org_id)
    account = await _make_account(db_session, org_id)
    job = await _make_job(
        db_session,
        org_id,
        post,
        account,
        status=PublishJobStatus.RETRYING,
        attempt_count=5,
        max_attempts=5,
        last_error="boom",
    )
    await db_session.commit()

    assert await _retry_publish_job_async(org_id, job.id, session=db_session) is None

    await db_session.refresh(job)
    assert job.status == PublishJobStatus.FAILED
    assert job.next_attempt_at is None


# ---------------------------------------------------------------------------
# Execution graph wiring
# ---------------------------------------------------------------------------


async def _make_node(db_session, org_id: uuid.UUID, job: PublishJob) -> ExecutionNode:
    node = ExecutionNode(
        organization_id=org_id,
        workflow_instance_id=uuid.uuid4(),
        node_type=WorkflowNodeType.PUBLISH_JOB,
        status=WorkflowNodeStatus.PENDING,
        ref_type=ExecutionNodeRefType.PUBLISH_JOB,
        ref_id=job.id,
    )
    db_session.add(node)
    await db_session.flush()
    return node


@pytest.mark.asyncio
async def test_successful_publish_moves_execution_node_to_succeeded(db_session):
    org_id = uuid.uuid4()
    post = await _make_post(db_session, org_id)
    account = await _make_account(db_session, org_id)
    job = await _make_job(db_session, org_id, post, account)
    node = await _make_node(db_session, org_id, job)
    await db_session.commit()

    await _execute_publish_job_async(
        org_id,
        job.id,
        session=db_session,
        adapter_factory=factory_for(FakeAdapter(PlatformName.LINKEDIN)),
    )

    await db_session.refresh(node)
    assert node.status == WorkflowNodeStatus.SUCCEEDED
    assert node.completed_at is not None


@pytest.mark.asyncio
async def test_permanent_failure_moves_execution_node_to_failed(db_session):
    org_id = uuid.uuid4()
    post = await _make_post(db_session, org_id, status=PostStatus.DRAFT)
    account = await _make_account(db_session, org_id)
    job = await _make_job(db_session, org_id, post, account)
    node = await _make_node(db_session, org_id, job)
    await db_session.commit()

    with pytest.raises(PermanentPublishError):
        await _execute_publish_job_async(
            org_id,
            job.id,
            session=db_session,
            adapter_factory=factory_for(FakeAdapter(PlatformName.LINKEDIN)),
        )

    await db_session.refresh(node)
    assert node.status == WorkflowNodeStatus.FAILED
    assert node.failure_reason is not None


@pytest.mark.asyncio
async def test_publish_succeeds_when_no_execution_node_exists(db_session):
    """Graph updates degrade gracefully — a missing node must not break the
    publish (nothing creates PUBLISH_JOB nodes today)."""
    org_id = uuid.uuid4()
    post = await _make_post(db_session, org_id)
    account = await _make_account(db_session, org_id)
    job = await _make_job(db_session, org_id, post, account)
    await db_session.commit()

    outcome = await _execute_publish_job_async(
        org_id,
        job.id,
        session=db_session,
        adapter_factory=factory_for(FakeAdapter(PlatformName.LINKEDIN)),
    )
    assert outcome == "published"


@pytest.mark.asyncio
async def test_execution_node_lookup_is_org_scoped(db_session):
    """CROSS-TENANT: org A's publish must not move org B's node, even if the
    node references the same job id."""
    org_a, org_b = uuid.uuid4(), uuid.uuid4()
    post = await _make_post(db_session, org_a)
    account = await _make_account(db_session, org_a)
    job = await _make_job(db_session, org_a, post, account)

    foreign_node = ExecutionNode(
        organization_id=org_b,
        workflow_instance_id=uuid.uuid4(),
        node_type=WorkflowNodeType.PUBLISH_JOB,
        status=WorkflowNodeStatus.PENDING,
        ref_type=ExecutionNodeRefType.PUBLISH_JOB,
        ref_id=job.id,
    )
    db_session.add(foreign_node)
    await db_session.commit()

    await _execute_publish_job_async(
        org_a,
        job.id,
        session=db_session,
        adapter_factory=factory_for(FakeAdapter(PlatformName.LINKEDIN)),
    )

    await db_session.refresh(foreign_node)
    assert foreign_node.status == WorkflowNodeStatus.PENDING


# ---------------------------------------------------------------------------
# Backoff
# ---------------------------------------------------------------------------


def test_compute_backoff_is_exponential():
    assert compute_backoff_seconds(1, 30) == 30
    assert compute_backoff_seconds(2, 30) == 60
    assert compute_backoff_seconds(3, 30) == 120
    assert compute_backoff_seconds(0, 30) == 30
