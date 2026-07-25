"""Unit tests for the approval workflow state machine: valid + invalid
transitions, and that decisions correctly advance Post status."""
from __future__ import annotations

import uuid

import pytest

from app.core.exceptions import InvalidTransitionError
from app.models.campaign import Campaign
from app.models.client import Client
from app.models.enums import ApprovalStatus, CampaignStatus, PostStatus
from app.models.organization import Organization
from app.models.post import Post
from app.services.approval_state_machine import ApprovalStateMachine


async def _make_post(db_session) -> tuple[Post, uuid.UUID]:
    org = Organization(name="Acme Agency", slug=f"acme-{uuid.uuid4().hex[:8]}")
    db_session.add(org)
    await db_session.flush()

    client = Client(organization_id=org.id, name="Acme Client")
    db_session.add(client)
    await db_session.flush()

    campaign = Campaign(
        organization_id=org.id, client_id=client.id, name="Launch", status=CampaignStatus.ACTIVE
    )
    db_session.add(campaign)
    await db_session.flush()

    post = Post(organization_id=org.id, campaign_id=campaign.id, platform="linkedin", caption="Hello")
    db_session.add(post)
    await db_session.flush()

    return post, org.id


@pytest.mark.asyncio
async def test_valid_transition_draft_to_internal_review(db_session):
    post, org_id = await _make_post(db_session)
    machine = ApprovalStateMachine(db_session)

    updated = await machine.transition(
        post=post, organization_id=org_id, target_status=PostStatus.INTERNAL_REVIEW, actor_user_id=None
    )
    assert updated.status == PostStatus.INTERNAL_REVIEW


@pytest.mark.asyncio
async def test_invalid_transition_draft_to_published_raises(db_session):
    post, org_id = await _make_post(db_session)
    machine = ApprovalStateMachine(db_session)

    with pytest.raises(InvalidTransitionError):
        await machine.transition(
            post=post, organization_id=org_id, target_status=PostStatus.PUBLISHED, actor_user_id=None
        )


@pytest.mark.asyncio
async def test_invalid_transition_from_terminal_archived_state(db_session):
    post, org_id = await _make_post(db_session)
    machine = ApprovalStateMachine(db_session)
    post = await machine.transition(
        post=post, organization_id=org_id, target_status=PostStatus.ARCHIVED, actor_user_id=None
    )
    with pytest.raises(InvalidTransitionError):
        await machine.transition(
            post=post, organization_id=org_id, target_status=PostStatus.DRAFT, actor_user_id=None
        )


@pytest.mark.asyncio
async def test_record_decision_approved_internal_advances_to_client_review(db_session):
    post, org_id = await _make_post(db_session)
    machine = ApprovalStateMachine(db_session)
    post = await machine.transition(
        post=post, organization_id=org_id, target_status=PostStatus.INTERNAL_REVIEW, actor_user_id=None
    )

    approval = await machine.record_decision(
        post=post,
        organization_id=org_id,
        reviewer_user_id=None,
        stage="internal",
        decision_status=ApprovalStatus.APPROVED,
    )
    assert approval.status == ApprovalStatus.APPROVED
    assert post.status == PostStatus.CLIENT_REVIEW


@pytest.mark.asyncio
async def test_record_decision_rejected_sets_post_rejected(db_session):
    post, org_id = await _make_post(db_session)
    machine = ApprovalStateMachine(db_session)
    post = await machine.transition(
        post=post, organization_id=org_id, target_status=PostStatus.INTERNAL_REVIEW, actor_user_id=None
    )

    await machine.record_decision(
        post=post,
        organization_id=org_id,
        reviewer_user_id=None,
        stage="internal",
        decision_status=ApprovalStatus.REJECTED,
        feedback="Needs more punch.",
    )
    assert post.status == PostStatus.REJECTED


# ---------------------------------------------------------------------------
# Hardening tests (task: approval workflow hardening)
# ---------------------------------------------------------------------------

from sqlalchemy import select  # noqa: E402

from app.core.exceptions import ConflictError, ForbiddenError  # noqa: E402
from app.models.approval import Approval  # noqa: E402
from app.models.audit_log import AuditLog  # noqa: E402
from app.models.enums import AuditAction  # noqa: E402
from app.models.post_version import PostVersion  # noqa: E402
from app.repositories.post_version_repository import PostVersionRepository  # noqa: E402
from app.services.approval_state_machine import (  # noqa: E402
    _ALLOWED_TRANSITIONS,
    TERMINAL_STATUSES,
)


# Shortest legal route from DRAFT to each state, used to park a Post in a
# given status before attempting an illegal jump out of it.
_LEGAL_ROUTE_TO: dict[PostStatus, list[PostStatus]] = {
    PostStatus.DRAFT: [],
    PostStatus.INTERNAL_REVIEW: [PostStatus.INTERNAL_REVIEW],
    PostStatus.CLIENT_REVIEW: [PostStatus.INTERNAL_REVIEW, PostStatus.CLIENT_REVIEW],
    PostStatus.APPROVED: [
        PostStatus.INTERNAL_REVIEW,
        PostStatus.CLIENT_REVIEW,
        PostStatus.APPROVED,
    ],
    PostStatus.REJECTED: [PostStatus.INTERNAL_REVIEW, PostStatus.REJECTED],
    PostStatus.SCHEDULED: [
        PostStatus.INTERNAL_REVIEW,
        PostStatus.CLIENT_REVIEW,
        PostStatus.APPROVED,
        PostStatus.SCHEDULED,
    ],
    PostStatus.PUBLISHED: [
        PostStatus.INTERNAL_REVIEW,
        PostStatus.CLIENT_REVIEW,
        PostStatus.APPROVED,
        PostStatus.SCHEDULED,
        PostStatus.PUBLISHED,
    ],
    PostStatus.ARCHIVED: [PostStatus.ARCHIVED],
}


async def _db_status(db_session, post) -> PostStatus:
    """Read the Post's status straight from the DB, bypassing the identity map."""
    await db_session.flush()
    row = (
        await db_session.execute(select(Post.status).where(Post.id == post.id))
    ).scalar_one()
    # SQLite returns the enum member name label ('DRAFT'); SQLAlchemy's Enum
    # type coerces it back to the member. Compare members, never string labels.
    return row


async def _audit_rows(db_session, post) -> list[AuditLog]:
    result = await db_session.execute(
        select(AuditLog)
        .where(AuditLog.entity_id == post.id, AuditLog.action == AuditAction.STATE_TRANSITION)
        .order_by(AuditLog.created_at)
    )
    return list(result.scalars().all())


def test_transition_table_covers_every_post_status():
    """Every PostStatus member must be an explicit key — an unmapped status
    would silently behave as terminal."""
    assert set(_ALLOWED_TRANSITIONS) == set(PostStatus)
    # And every target is itself a real PostStatus.
    for targets in _ALLOWED_TRANSITIONS.values():
        assert targets <= set(PostStatus)


def test_archived_is_the_only_terminal_state():
    assert TERMINAL_STATUSES == frozenset({PostStatus.ARCHIVED})
    assert _ALLOWED_TRANSITIONS[PostStatus.ARCHIVED] == set()
    # PUBLISHED is intentionally not terminal: it can still be archived.
    assert _ALLOWED_TRANSITIONS[PostStatus.PUBLISHED] == {PostStatus.ARCHIVED}


@pytest.mark.asyncio
async def test_full_legal_path_draft_to_published(db_session):
    post, org_id = await _make_post(db_session)
    machine = ApprovalStateMachine(db_session)

    path = [
        PostStatus.INTERNAL_REVIEW,
        PostStatus.CLIENT_REVIEW,
        PostStatus.APPROVED,
        PostStatus.SCHEDULED,
        PostStatus.PUBLISHED,
    ]
    for target in path:
        await machine.transition(
            post=post, organization_id=org_id, target_status=target, actor_user_id=None
        )
        assert await _db_status(db_session, post) == target

    assert len(await _audit_rows(db_session, post)) == len(path)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "current,illegal",
    [
        (PostStatus.DRAFT, PostStatus.PUBLISHED),
        (PostStatus.DRAFT, PostStatus.APPROVED),
        (PostStatus.DRAFT, PostStatus.CLIENT_REVIEW),
        (PostStatus.INTERNAL_REVIEW, PostStatus.PUBLISHED),
        (PostStatus.INTERNAL_REVIEW, PostStatus.APPROVED),
        (PostStatus.CLIENT_REVIEW, PostStatus.SCHEDULED),
        (PostStatus.APPROVED, PostStatus.PUBLISHED),
        (PostStatus.SCHEDULED, PostStatus.APPROVED),
        (PostStatus.PUBLISHED, PostStatus.DRAFT),
        (PostStatus.PUBLISHED, PostStatus.SCHEDULED),
        (PostStatus.REJECTED, PostStatus.INTERNAL_REVIEW),
        (PostStatus.ARCHIVED, PostStatus.DRAFT),
        (PostStatus.ARCHIVED, PostStatus.PUBLISHED),
    ],
)
async def test_illegal_transition_raises_and_leaves_row_unchanged(db_session, current, illegal):
    post, org_id = await _make_post(db_session)
    machine = ApprovalStateMachine(db_session)

    # Walk the legal path to `current` before attempting the illegal jump.
    for step in _LEGAL_ROUTE_TO[current]:
        await machine.transition(
            post=post, organization_id=org_id, target_status=step, actor_user_id=None
        )
    audit_before = len(await _audit_rows(db_session, post))
    assert await _db_status(db_session, post) == current

    with pytest.raises(InvalidTransitionError):
        await machine.transition(
            post=post, organization_id=org_id, target_status=illegal, actor_user_id=None
        )

    assert await _db_status(db_session, post) == current
    assert len(await _audit_rows(db_session, post)) == audit_before


@pytest.mark.asyncio
async def test_every_illegal_pair_in_the_table_raises(db_session):
    """Exhaustive sweep: for every (from, to) pair NOT in the table, the
    machine must refuse. Guards against a permissive edit to _assert_legal."""
    machine = ApprovalStateMachine(db_session)
    post, _ = await _make_post(db_session)
    for current, allowed in _ALLOWED_TRANSITIONS.items():
        for target in set(PostStatus) - allowed:
            with pytest.raises(InvalidTransitionError):
                machine._assert_legal(current, target)


@pytest.mark.asyncio
async def test_direct_status_assignment_is_blocked(db_session):
    """The core invariant: post.status cannot be written outside the machine."""
    post, _ = await _make_post(db_session)
    with pytest.raises(InvalidTransitionError):
        post.status = PostStatus.PUBLISHED
    assert await _db_status(db_session, post) == PostStatus.DRAFT


@pytest.mark.asyncio
async def test_repository_update_cannot_smuggle_a_status_change(db_session):
    from app.repositories.post_repository import PostRepository

    post, org_id = await _make_post(db_session)
    repo = PostRepository(db_session)
    with pytest.raises(InvalidTransitionError):
        await repo.update(post, status=PostStatus.APPROVED)
    assert await _db_status(db_session, post) == PostStatus.DRAFT


@pytest.mark.asyncio
async def test_transition_writes_audit_row_with_from_to_actor_and_post(db_session):
    post, org_id = await _make_post(db_session)
    machine = ApprovalStateMachine(db_session)
    actor = uuid.uuid4()

    await machine.transition(
        post=post,
        organization_id=org_id,
        target_status=PostStatus.INTERNAL_REVIEW,
        actor_user_id=actor,
        reason="Ready for review.",
    )

    rows = await _audit_rows(db_session, post)
    assert len(rows) == 1
    row = rows[0]
    assert row.action == AuditAction.STATE_TRANSITION
    assert row.entity_type == "Post"
    assert row.entity_id == post.id
    assert row.actor_user_id == actor
    assert row.organization_id == org_id
    assert row.metadata_json["from"] == PostStatus.DRAFT.value
    assert row.metadata_json["to"] == PostStatus.INTERNAL_REVIEW.value


@pytest.mark.asyncio
async def test_cross_org_transition_is_forbidden(db_session):
    post, _ = await _make_post(db_session)
    machine = ApprovalStateMachine(db_session)
    other_org = uuid.uuid4()

    with pytest.raises(ForbiddenError):
        await machine.transition(
            post=post,
            organization_id=other_org,
            target_status=PostStatus.INTERNAL_REVIEW,
            actor_user_id=None,
        )
    assert await _db_status(db_session, post) == PostStatus.DRAFT
    assert await _audit_rows(db_session, post) == []


@pytest.mark.asyncio
async def test_cross_org_decision_is_forbidden_and_writes_no_approval(db_session):
    post, org_id = await _make_post(db_session)
    machine = ApprovalStateMachine(db_session)
    await machine.transition(
        post=post, organization_id=org_id, target_status=PostStatus.INTERNAL_REVIEW, actor_user_id=None
    )

    with pytest.raises(ForbiddenError):
        await machine.record_decision(
            post=post,
            organization_id=uuid.uuid4(),
            reviewer_user_id=None,
            stage="internal",
            decision_status=ApprovalStatus.APPROVED,
        )

    approvals = (
        await db_session.execute(select(Approval).where(Approval.post_id == post.id))
    ).scalars().all()
    assert approvals == []
    assert await _db_status(db_session, post) == PostStatus.INTERNAL_REVIEW


@pytest.mark.asyncio
async def test_illegal_decision_records_no_orphan_approval_row(db_session):
    """A client-stage approval on a DRAFT post implies DRAFT -> APPROVED,
    which is illegal — so neither the Approval row nor the status change
    may survive."""
    post, org_id = await _make_post(db_session)
    machine = ApprovalStateMachine(db_session)

    with pytest.raises(InvalidTransitionError):
        await machine.record_decision(
            post=post,
            organization_id=org_id,
            reviewer_user_id=None,
            stage="client",
            decision_status=ApprovalStatus.APPROVED,
        )

    approvals = (
        await db_session.execute(select(Approval).where(Approval.post_id == post.id))
    ).scalars().all()
    assert approvals == []
    assert await _db_status(db_session, post) == PostStatus.DRAFT


@pytest.mark.asyncio
async def test_changes_requested_returns_post_to_draft(db_session):
    post, org_id = await _make_post(db_session)
    machine = ApprovalStateMachine(db_session)
    await machine.transition(
        post=post, organization_id=org_id, target_status=PostStatus.INTERNAL_REVIEW, actor_user_id=None
    )

    approval = await machine.record_decision(
        post=post,
        organization_id=org_id,
        reviewer_user_id=None,
        stage="internal",
        decision_status=ApprovalStatus.CHANGES_REQUESTED,
        feedback="Tighten the hook.",
    )
    assert approval.status == ApprovalStatus.CHANGES_REQUESTED
    assert await _db_status(db_session, post) == PostStatus.DRAFT


@pytest.mark.asyncio
async def test_pending_decision_records_approval_without_transitioning(db_session):
    post, org_id = await _make_post(db_session)
    machine = ApprovalStateMachine(db_session)
    await machine.transition(
        post=post, organization_id=org_id, target_status=PostStatus.INTERNAL_REVIEW, actor_user_id=None
    )
    audit_before = len(await _audit_rows(db_session, post))

    approval = await machine.record_decision(
        post=post,
        organization_id=org_id,
        reviewer_user_id=None,
        stage="internal",
        decision_status=ApprovalStatus.PENDING,
    )
    assert approval.status == ApprovalStatus.PENDING
    assert await _db_status(db_session, post) == PostStatus.INTERNAL_REVIEW
    assert len(await _audit_rows(db_session, post)) == audit_before


@pytest.mark.asyncio
async def test_decision_transition_also_writes_an_audit_row(db_session):
    post, org_id = await _make_post(db_session)
    machine = ApprovalStateMachine(db_session)
    await machine.transition(
        post=post, organization_id=org_id, target_status=PostStatus.INTERNAL_REVIEW, actor_user_id=None
    )
    await machine.record_decision(
        post=post,
        organization_id=org_id,
        reviewer_user_id=None,
        stage="internal",
        decision_status=ApprovalStatus.APPROVED,
    )
    rows = await _audit_rows(db_session, post)
    assert len(rows) == 2
    assert rows[-1].metadata_json["to"] == PostStatus.CLIENT_REVIEW.value


# --- PostVersion immutability / numbering -----------------------------------


@pytest.mark.asyncio
async def test_snapshot_increments_version_number_and_leaves_priors_untouched(db_session):
    post, _ = await _make_post(db_session)
    repo = PostVersionRepository(db_session)

    v1 = await repo.snapshot_post(post, change_summary="first")
    original_caption = v1.caption
    with allow_content_edit(post, "Rewritten caption"):
        pass
    v2 = await repo.snapshot_post(post, change_summary="second")

    assert (v1.version_number, v2.version_number) == (1, 2)
    versions = await repo.list_for_post(post.id)
    assert [v.version_number for v in versions] == [1, 2]
    assert versions[0].caption == original_caption
    assert versions[1].caption == "Rewritten caption"


@pytest.mark.asyncio
async def test_existing_post_version_cannot_be_mutated(db_session):
    post, _ = await _make_post(db_session)
    repo = PostVersionRepository(db_session)
    v1 = await repo.snapshot_post(post, change_summary="first")
    await db_session.flush()

    v1.caption = "tampered"
    with pytest.raises(ConflictError):
        await db_session.flush()
    db_session.expunge_all()


@pytest.mark.asyncio
async def test_duplicate_version_number_cannot_be_inserted(db_session):
    """The unique constraint is what makes the retry loop in snapshot_post
    safe — assert it actually exists and bites."""
    from sqlalchemy.exc import IntegrityError

    post, _ = await _make_post(db_session)
    repo = PostVersionRepository(db_session)
    await repo.snapshot_post(post)

    dupe = PostVersion(post_id=post.id, version_number=1, caption="clash")
    db_session.add(dupe)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_snapshot_recovers_from_a_version_number_collision(db_session):
    """Simulate the concurrent-edit race: the max() read is stale, so the
    first INSERT collides. snapshot_post must retry, not corrupt history."""
    post, _ = await _make_post(db_session)
    repo = PostVersionRepository(db_session)
    await repo.snapshot_post(post)  # v1

    real_max = repo.get_latest_version_number
    calls = {"n": 0}

    async def stale_then_fresh(post_id):
        calls["n"] += 1
        if calls["n"] == 1:
            return 0  # stale read -> tries to insert v1 again
        return await real_max(post_id)

    repo.get_latest_version_number = stale_then_fresh
    v = await repo.snapshot_post(post, change_summary="racing edit")
    assert v.version_number == 2
    assert calls["n"] == 2
    versions = await repo.list_for_post(post.id)
    assert [x.version_number for x in versions] == [1, 2]


from contextlib import contextmanager  # noqa: E402


@contextmanager
def allow_content_edit(post, new_caption):
    """Content (not status) edits need no guard — this just makes the test
    read as an explicit edit step."""
    post.caption = new_caption
    yield
