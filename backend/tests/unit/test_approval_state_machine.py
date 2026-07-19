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
