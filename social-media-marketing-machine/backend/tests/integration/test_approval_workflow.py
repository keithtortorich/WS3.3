"""Integration tests for the approval workflow, driven through the real
FastAPI app (SQLite-backed, get_db/auth overridden).

These assert on DATABASE ROWS, not just HTTP status codes: an endpoint that
returns 200 while failing to write an AuditLog row, or that leaves a Post's
status changed after refusing a transition, is exactly the class of bug this
suite exists to catch.

Enum note: SQLAlchemy persists the enum MEMBER NAME, so DB labels are
UPPERCASE ('PENDING'). Assertions here compare enum members (or the JSON
`.value` the API actually serializes), never a raw lowercase DB literal —
that would silently match nothing.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.approval import Approval
from app.models.audit_log import AuditLog
from app.models.campaign import Campaign
from app.models.client import Client
from app.models.enums import ApprovalStatus, AuditAction, CampaignStatus, PostStatus
from app.models.organization import Organization
from app.models.post import Post
from app.models.post_version import PostVersion


async def _seed_campaign(db_session, org_id: uuid.UUID) -> uuid.UUID:
    org = (
        await db_session.execute(select(Organization).where(Organization.id == org_id))
    ).scalar_one_or_none()
    if org is None:
        org = Organization(id=org_id, name=f"Org {org_id.hex[:6]}", slug=f"org-{org_id.hex[:8]}")
        db_session.add(org)
        await db_session.flush()

    client_row = Client(organization_id=org_id, name="Test Client")
    db_session.add(client_row)
    await db_session.flush()

    campaign = Campaign(
        organization_id=org_id,
        client_id=client_row.id,
        name="Launch",
        status=CampaignStatus.ACTIVE,
    )
    db_session.add(campaign)
    await db_session.commit()
    return campaign.id


async def _create_post(client, campaign_id: uuid.UUID) -> str:
    resp = await client.post(
        "/api/v1/posts",
        json={
            "campaign_id": str(campaign_id),
            "platform": "linkedin",
            "caption": "Original caption",
            "hashtags": ["launch"],
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _transition(client, post_id: str, target: PostStatus, reason: str | None = None):
    return await client.post(
        f"/api/v1/approvals/posts/{post_id}/transition",
        json={"target_status": target.value, "reason": reason},
    )


async def _db_post(db_session, post_id: str) -> Post:
    db_session.expire_all()
    return (
        await db_session.execute(select(Post).where(Post.id == uuid.UUID(post_id)))
    ).scalar_one()


async def _transition_audit_rows(db_session, post_id: str) -> list[AuditLog]:
    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.entity_id == uuid.UUID(post_id),
            AuditLog.action == AuditAction.STATE_TRANSITION,
        )
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_legal_path_draft_to_published_over_http(client, db_session):
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_campaign(db_session, TEST_ORG_ID)
    post_id = await _create_post(client, campaign_id)

    assert (await _db_post(db_session, post_id)).status == PostStatus.DRAFT

    path = [
        PostStatus.INTERNAL_REVIEW,
        PostStatus.CLIENT_REVIEW,
        PostStatus.APPROVED,
        PostStatus.SCHEDULED,
        PostStatus.PUBLISHED,
    ]
    for index, target in enumerate(path, start=1):
        resp = await _transition(client, post_id, target)
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == target.value

        # Assert the row, not the response code.
        assert (await _db_post(db_session, post_id)).status == target
        rows = await _transition_audit_rows(db_session, post_id)
        assert len(rows) == index
        assert rows[-1].metadata_json["to"] == target.value


# ---------------------------------------------------------------------------
# Illegal transitions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "illegal",
    [
        PostStatus.PUBLISHED,
        PostStatus.APPROVED,
        PostStatus.CLIENT_REVIEW,
        PostStatus.SCHEDULED,
        PostStatus.REJECTED,
    ],
)
async def test_illegal_transition_from_draft_409s_and_row_is_unchanged(
    client, db_session, illegal
):
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_campaign(db_session, TEST_ORG_ID)
    post_id = await _create_post(client, campaign_id)

    resp = await _transition(client, post_id, illegal)
    assert resp.status_code == 409, resp.text
    assert resp.json()["error"] == "InvalidTransitionError"

    assert (await _db_post(db_session, post_id)).status == PostStatus.DRAFT
    assert await _transition_audit_rows(db_session, post_id) == []


@pytest.mark.asyncio
async def test_archived_is_terminal_over_http(client, db_session):
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_campaign(db_session, TEST_ORG_ID)
    post_id = await _create_post(client, campaign_id)

    assert (await _transition(client, post_id, PostStatus.ARCHIVED)).status_code == 200
    assert (await _db_post(db_session, post_id)).status == PostStatus.ARCHIVED

    for escape in PostStatus:
        resp = await _transition(client, post_id, escape)
        assert resp.status_code == 409, f"{escape} escaped ARCHIVED"
        assert (await _db_post(db_session, post_id)).status == PostStatus.ARCHIVED


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------


async def _decide(client, post_id: str, stage: str, status: ApprovalStatus, feedback=None):
    return await client.post(
        f"/api/v1/approvals/posts/{post_id}/decisions",
        json={"stage": stage, "status": status.value, "feedback": feedback},
    )


@pytest.mark.asyncio
async def test_approve_internal_then_client_lands_approved_with_approval_rows(client, db_session):
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_campaign(db_session, TEST_ORG_ID)
    post_id = await _create_post(client, campaign_id)
    assert (await _transition(client, post_id, PostStatus.INTERNAL_REVIEW)).status_code == 200

    resp = await _decide(client, post_id, "internal", ApprovalStatus.APPROVED)
    assert resp.status_code == 201, resp.text
    assert (await _db_post(db_session, post_id)).status == PostStatus.CLIENT_REVIEW

    resp = await _decide(client, post_id, "client", ApprovalStatus.APPROVED)
    assert resp.status_code == 201, resp.text
    assert (await _db_post(db_session, post_id)).status == PostStatus.APPROVED

    approvals = (
        await db_session.execute(
            select(Approval).where(Approval.post_id == uuid.UUID(post_id))
        )
    ).scalars().all()
    assert len(approvals) == 2
    assert {a.stage for a in approvals} == {"internal", "client"}
    assert all(a.status == ApprovalStatus.APPROVED for a in approvals)
    assert all(a.organization_id == TEST_ORG_ID for a in approvals)

    # One audit row per transition: submit + 2 decision-driven advances.
    assert len(await _transition_audit_rows(db_session, post_id)) == 3


@pytest.mark.asyncio
async def test_reject_lands_rejected_with_feedback_recorded(client, db_session):
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_campaign(db_session, TEST_ORG_ID)
    post_id = await _create_post(client, campaign_id)
    await _transition(client, post_id, PostStatus.INTERNAL_REVIEW)

    resp = await _decide(
        client, post_id, "internal", ApprovalStatus.REJECTED, feedback="Off-brand."
    )
    assert resp.status_code == 201, resp.text
    assert (await _db_post(db_session, post_id)).status == PostStatus.REJECTED

    approval = (
        await db_session.execute(
            select(Approval).where(Approval.post_id == uuid.UUID(post_id))
        )
    ).scalar_one()
    assert approval.status == ApprovalStatus.REJECTED
    assert approval.feedback == "Off-brand."


@pytest.mark.asyncio
async def test_request_changes_returns_post_to_draft(client, db_session):
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_campaign(db_session, TEST_ORG_ID)
    post_id = await _create_post(client, campaign_id)
    await _transition(client, post_id, PostStatus.INTERNAL_REVIEW)
    await _transition(client, post_id, PostStatus.CLIENT_REVIEW)

    resp = await _decide(
        client, post_id, "client", ApprovalStatus.CHANGES_REQUESTED, feedback="Shorter."
    )
    assert resp.status_code == 201, resp.text
    assert (await _db_post(db_session, post_id)).status == PostStatus.DRAFT

    approval = (
        await db_session.execute(
            select(Approval).where(Approval.post_id == uuid.UUID(post_id))
        )
    ).scalar_one()
    assert approval.status == ApprovalStatus.CHANGES_REQUESTED


@pytest.mark.asyncio
async def test_decision_implying_an_illegal_transition_writes_no_approval(client, db_session):
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_campaign(db_session, TEST_ORG_ID)
    post_id = await _create_post(client, campaign_id)  # still DRAFT

    # 'client' stage approval implies DRAFT -> APPROVED, which is illegal.
    resp = await _decide(client, post_id, "client", ApprovalStatus.APPROVED)
    assert resp.status_code == 409, resp.text

    approvals = (
        await db_session.execute(
            select(Approval).where(Approval.post_id == uuid.UUID(post_id))
        )
    ).scalars().all()
    assert approvals == []
    assert (await _db_post(db_session, post_id)).status == PostStatus.DRAFT


# ---------------------------------------------------------------------------
# Version snapshots
# ---------------------------------------------------------------------------


async def _versions(db_session, post_id: str) -> list[PostVersion]:
    db_session.expire_all()
    result = await db_session.execute(
        select(PostVersion)
        .where(PostVersion.post_id == uuid.UUID(post_id))
        .order_by(PostVersion.version_number)
    )
    return list(result.scalars().all())


@pytest.mark.asyncio
async def test_edit_creates_a_new_version_and_leaves_prior_versions_untouched(client, db_session):
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_campaign(db_session, TEST_ORG_ID)
    post_id = await _create_post(client, campaign_id)

    versions = await _versions(db_session, post_id)
    assert [v.version_number for v in versions] == [1]
    assert versions[0].caption == "Original caption"
    v1_id = versions[0].id

    resp = await client.patch(
        f"/api/v1/posts/{post_id}",
        json={"caption": "Second caption", "change_summary": "Punchier hook"},
    )
    assert resp.status_code == 200, resp.text

    resp = await client.patch(f"/api/v1/posts/{post_id}", json={"caption": "Third caption"})
    assert resp.status_code == 200, resp.text

    versions = await _versions(db_session, post_id)
    assert [v.version_number for v in versions] == [1, 2, 3]
    assert [v.caption for v in versions] == [
        "Original caption",
        "Second caption",
        "Third caption",
    ]
    # v1 is the same immutable row, not a rewritten one.
    assert versions[0].id == v1_id
    assert versions[1].change_summary == "Punchier hook"


@pytest.mark.asyncio
async def test_editing_content_does_not_change_status(client, db_session):
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_campaign(db_session, TEST_ORG_ID)
    post_id = await _create_post(client, campaign_id)
    await _transition(client, post_id, PostStatus.INTERNAL_REVIEW)

    resp = await client.patch(f"/api/v1/posts/{post_id}", json={"caption": "Edited in review"})
    assert resp.status_code == 200, resp.text
    assert (await _db_post(db_session, post_id)).status == PostStatus.INTERNAL_REVIEW
    # PostUpdate has no `status` field, so a smuggled one is simply ignored.
    resp = await client.patch(
        f"/api/v1/posts/{post_id}", json={"caption": "x", "status": "published"}
    )
    assert resp.status_code == 200, resp.text
    assert (await _db_post(db_session, post_id)).status == PostStatus.INTERNAL_REVIEW


# ---------------------------------------------------------------------------
# Cross-tenant
# ---------------------------------------------------------------------------


async def _seed_foreign_post(db_session) -> str:
    other_org_id = uuid.uuid4()
    campaign_id = await _seed_campaign(db_session, other_org_id)
    post = Post(
        organization_id=other_org_id,
        campaign_id=campaign_id,
        platform="linkedin",
        caption="Another agency's post",
    )
    db_session.add(post)
    await db_session.commit()
    return str(post.id)


@pytest.mark.asyncio
async def test_cross_tenant_transition_is_refused(client, db_session):
    foreign_post_id = await _seed_foreign_post(db_session)

    resp = await _transition(client, foreign_post_id, PostStatus.INTERNAL_REVIEW)
    assert resp.status_code == 404, resp.text

    assert (await _db_post(db_session, foreign_post_id)).status == PostStatus.DRAFT
    assert await _transition_audit_rows(db_session, foreign_post_id) == []


@pytest.mark.asyncio
async def test_cross_tenant_approval_decision_is_refused(client, db_session):
    foreign_post_id = await _seed_foreign_post(db_session)

    resp = await _decide(client, foreign_post_id, "internal", ApprovalStatus.APPROVED)
    assert resp.status_code == 404, resp.text

    approvals = (
        await db_session.execute(
            select(Approval).where(Approval.post_id == uuid.UUID(foreign_post_id))
        )
    ).scalars().all()
    assert approvals == []
    assert (await _db_post(db_session, foreign_post_id)).status == PostStatus.DRAFT


@pytest.mark.asyncio
async def test_cross_tenant_post_edit_is_refused_and_writes_no_version(client, db_session):
    foreign_post_id = await _seed_foreign_post(db_session)

    resp = await client.patch(
        f"/api/v1/posts/{foreign_post_id}", json={"caption": "hijacked"}
    )
    assert resp.status_code == 404, resp.text
    assert await _versions(db_session, foreign_post_id) == []
    assert (await _db_post(db_session, foreign_post_id)).caption == "Another agency's post"


@pytest.mark.asyncio
async def test_cross_tenant_approval_listing_is_empty(client, db_session):
    foreign_post_id = await _seed_foreign_post(db_session)

    resp = await client.get(f"/api/v1/approvals/posts/{foreign_post_id}")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
