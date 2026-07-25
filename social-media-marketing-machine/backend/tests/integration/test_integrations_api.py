"""Integration tests for the WS3.3 -> SMM bridge.

``app/routers/integrations.py`` is deliberately NOT wired into
``app/main.py`` here — that file is owned by the dispatcher. These tests
mount the router onto the shared ``app`` fixture instead, which exercises
the real router, real service, real repositories and a real SQLite schema
built from ``Base.metadata``.

Assertions go to actual DB rows, not just status codes: an ingest that
returns 200 while writing nothing is exactly the failure mode worth
catching.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.approval import Approval
from app.models.brand import Brand
from app.models.campaign import Campaign
from app.models.client import Client
from app.models.enums import (
    ApprovalStatus,
    AuditAction,
    ExecutionNodeRefType,
    PostStatus,
    WorkflowNodeType,
)
from app.models.execution_node import ExecutionNode
from app.models.integration_mount import IntegrationMount
from app.models.organization import Organization
from app.models.post import Post
from app.models.post_version import PostVersion
from app.models.audit_log import AuditLog
from app.routers import integrations
from tests.conftest import TEST_ORG_ID

MOUNT_URL = "/integrations/social-media-marketing/mount"
OTHER_ORG_ID = uuid.uuid4()


@pytest_asyncio.fixture
async def integrations_client(app, async_engine):
    """The shared test app with the integrations router mounted."""
    app.include_router(integrations.router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _session_factory(async_engine):
    return async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)


async def _seed(db_session, *, org_id: uuid.UUID = TEST_ORG_ID) -> tuple[uuid.UUID, uuid.UUID]:
    """Create an Organization + Client + Brand. Returns (client_id, brand_id)."""
    org = Organization(id=org_id, name=f"Org {org_id.hex[:6]}", slug=f"org-{org_id.hex[:8]}")
    db_session.add(org)
    await db_session.flush()

    client_row = Client(organization_id=org_id, name="Acme HVAC")
    db_session.add(client_row)
    await db_session.flush()

    brand = Brand(organization_id=org_id, client_id=client_row.id, name="Acme Primary")
    db_session.add(brand)
    await db_session.commit()
    return client_row.id, brand.id


def _mount_payload(brand_id: uuid.UUID | None = None, tenant_id: str = "acme-hvac") -> dict:
    payload = {
        "tenant_id": tenant_id,
        "social_tenant_id": str(TEST_ORG_ID),
        "platforms": ["meta"],
        "mode": "agent_managed",
    }
    if brand_id is not None:
        payload["default_brand_id"] = str(brand_id)
    return payload


def _intent_payload(brand_id: uuid.UUID | None = None, platforms: list[str] | None = None) -> dict:
    return {
        "campaign_intent": {
            "objective": "bookings",
            "budget_cents": 50000,
            "platforms": platforms if platforms is not None else ["meta"],
            "start": "2026-08-01",
            "end": "2026-08-31",
            **({"brand_id": str(brand_id)} if brand_id else {}),
        },
        "post_draft": {
            "headline": "Phoenix HVAC checkup special",
            "body": "Book a 21-point inspection before August.",
            "media_refs": [],
        },
    }


async def _create_mount(integrations_client, brand_id, tenant_id: str = "acme-hvac") -> uuid.UUID:
    response = await integrations_client.post(MOUNT_URL, json=_mount_payload(brand_id, tenant_id))
    assert response.status_code == 204, response.text
    location = response.headers["Location"]
    return uuid.UUID(location.rsplit("/", 1)[-1])


# ----------------------------------------------------------------------
# mount
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mount_happy_path_returns_204_with_location(
    integrations_client, db_session, async_engine
):
    _, brand_id = await _seed(db_session)

    response = await integrations_client.post(MOUNT_URL, json=_mount_payload(brand_id))

    assert response.status_code == 204, response.text
    assert response.content == b""
    location = response.headers.get("Location")
    assert location is not None
    assert location.startswith(f"{MOUNT_URL}/")
    mount_id = uuid.UUID(location.rsplit("/", 1)[-1])

    async with _session_factory(async_engine)() as session:
        mount = await session.get(IntegrationMount, mount_id)
        assert mount is not None
        assert mount.organization_id == TEST_ORG_ID
        assert mount.external_system == "webstaffr3.3"
        assert mount.external_tenant_id == "acme-hvac"
        assert mount.platforms == ["meta"]
        assert mount.default_brand_id == brand_id
        assert mount.mode == "agent_managed"


@pytest.mark.asyncio
async def test_duplicate_mount_returns_409(integrations_client, db_session, async_engine):
    _, brand_id = await _seed(db_session)

    first = await integrations_client.post(MOUNT_URL, json=_mount_payload(brand_id))
    assert first.status_code == 204

    second = await integrations_client.post(MOUNT_URL, json=_mount_payload(brand_id))
    assert second.status_code == 409, second.text
    assert second.json()["error"] == "ConflictError"

    async with _session_factory(async_engine)() as session:
        total = await session.scalar(select(func.count()).select_from(IntegrationMount))
        assert total == 1


@pytest.mark.asyncio
async def test_mount_rejects_unknown_mode(integrations_client, db_session):
    await _seed(db_session)

    payload = _mount_payload()
    payload["mode"] = "yolo"
    response = await integrations_client.post(MOUNT_URL, json=payload)

    assert response.status_code == 422, response.text
    assert response.json()["error"] == "ValidationAppError"


@pytest.mark.asyncio
async def test_mount_rejects_foreign_social_tenant_id(integrations_client, db_session):
    await _seed(db_session)

    payload = _mount_payload()
    payload["social_tenant_id"] = str(OTHER_ORG_ID)
    response = await integrations_client.post(MOUNT_URL, json=payload)

    assert response.status_code == 403, response.text


# ----------------------------------------------------------------------
# intent
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_intent_happy_path_creates_full_graph(
    integrations_client, db_session, async_engine
):
    client_id, brand_id = await _seed(db_session)
    mount_id = await _create_mount(integrations_client, brand_id)

    response = await integrations_client.post(
        f"{MOUNT_URL}/{mount_id}/intent", json=_intent_payload(brand_id)
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "pending_review"
    workflow_instance_id = uuid.UUID(body["workflow_instance_id"])
    assert body["approval_url"] == f"/approvals/{workflow_instance_id}"

    async with _session_factory(async_engine)() as session:
        # --- campaign ---
        campaign = await session.get(Campaign, uuid.UUID(body["campaign_id"]))
        assert campaign is not None
        assert campaign.organization_id == TEST_ORG_ID
        assert campaign.client_id == client_id
        assert campaign.brand_id == brand_id
        assert campaign.goal == "bookings"
        assert campaign.budget_cents == 50000
        assert campaign.start_date.isoformat() == "2026-08-01"
        assert campaign.end_date.isoformat() == "2026-08-31"

        # --- post ---
        posts = (
            await session.execute(select(Post).where(Post.campaign_id == campaign.id))
        ).scalars().all()
        assert len(posts) == 1
        post = posts[0]
        assert post.platform == "meta"
        assert post.organization_id == TEST_ORG_ID
        # moved off DRAFT via the approval state machine, never assigned directly
        assert post.status == PostStatus.INTERNAL_REVIEW
        assert "Phoenix HVAC checkup special" in post.caption

        # --- initial version ---
        versions = (
            await session.execute(select(PostVersion).where(PostVersion.post_id == post.id))
        ).scalars().all()
        assert len(versions) == 1
        assert versions[0].version_number == 1
        assert versions[0].caption == post.caption

        # --- bootstrap approval ---
        approvals = (
            await session.execute(select(Approval).where(Approval.post_id == post.id))
        ).scalars().all()
        assert len(approvals) == 1
        assert approvals[0].status == ApprovalStatus.PENDING
        assert approvals[0].stage == "internal"
        assert approvals[0].organization_id == TEST_ORG_ID

        # --- execution graph ---
        nodes = (
            await session.execute(
                select(ExecutionNode).where(
                    ExecutionNode.workflow_instance_id == workflow_instance_id
                )
            )
        ).scalars().all()
        by_type = {}
        for node in nodes:
            by_type.setdefault(node.node_type, []).append(node)
        assert set(by_type) == {
            WorkflowNodeType.CAMPAIGN,
            WorkflowNodeType.INTEGRATION_EVENT,
            WorkflowNodeType.POST,
            WorkflowNodeType.APPROVAL,
        }
        root = by_type[WorkflowNodeType.CAMPAIGN][0]
        assert root.parent_node_id is None
        assert root.ref_id == campaign.id
        assert root.ref_type == ExecutionNodeRefType.CAMPAIGN

        post_node = by_type[WorkflowNodeType.POST][0]
        assert post_node.parent_node_id == root.id
        assert post_node.ref_id == post.id
        assert post_node.ref_type == ExecutionNodeRefType.POST

        approval_node = by_type[WorkflowNodeType.APPROVAL][0]
        assert approval_node.parent_node_id == post_node.id
        assert approval_node.ref_id == approvals[0].id

        assert all(n.organization_id == TEST_ORG_ID for n in nodes)

        # --- audit ---
        audits = (
            await session.execute(
                select(AuditLog).where(AuditLog.entity_type == "IntegrationIntent")
            )
        ).scalars().all()
        assert len(audits) == 1
        assert audits[0].action == AuditAction.CREATE
        assert audits[0].organization_id == TEST_ORG_ID
        assert audits[0].metadata_json["mount_id"] == str(mount_id)
        assert audits[0].metadata_json["workflow_instance_id"] == str(workflow_instance_id)


@pytest.mark.asyncio
async def test_intent_creates_one_post_per_platform(
    integrations_client, db_session, async_engine
):
    _, brand_id = await _seed(db_session)
    mount_id = await _create_mount(integrations_client, brand_id)

    response = await integrations_client.post(
        f"{MOUNT_URL}/{mount_id}/intent",
        json=_intent_payload(brand_id, platforms=["meta", "linkedin", "meta"]),
    )
    assert response.status_code == 200, response.text
    assert len(response.json()["post_ids"]) == 2  # duplicate platform deduplicated

    async with _session_factory(async_engine)() as session:
        posts = (await session.execute(select(Post))).scalars().all()
        assert sorted(p.platform for p in posts) == ["linkedin", "meta"]
        approvals = (await session.execute(select(Approval))).scalars().all()
        assert len(approvals) == 2


@pytest.mark.asyncio
async def test_intent_unknown_mount_returns_404(integrations_client, db_session):
    await _seed(db_session)

    response = await integrations_client.post(
        f"{MOUNT_URL}/{uuid.uuid4()}/intent", json=_intent_payload()
    )

    assert response.status_code == 404, response.text
    assert response.json()["error"] == "NotFoundError"


@pytest.mark.asyncio
async def test_intent_cannot_resolve_another_orgs_mount(
    integrations_client, db_session, async_engine
):
    """CROSS-TENANT ISOLATION: a mount owned by another organization must be
    indistinguishable from a nonexistent one."""
    await _seed(db_session)
    other_org = Organization(
        id=OTHER_ORG_ID, name="Other Org", slug=f"other-{OTHER_ORG_ID.hex[:8]}"
    )
    db_session.add(other_org)
    await db_session.flush()
    foreign_mount = IntegrationMount(
        organization_id=OTHER_ORG_ID,
        external_system="webstaffr3.3",
        external_tenant_id="rival-hvac",
        platforms=["meta"],
        mode="agent_managed",
    )
    db_session.add(foreign_mount)
    await db_session.commit()
    foreign_mount_id = foreign_mount.id

    # The authenticated caller is TEST_ORG_ID (conftest override).
    response = await integrations_client.post(
        f"{MOUNT_URL}/{foreign_mount_id}/intent", json=_intent_payload()
    )

    assert response.status_code == 404, response.text
    assert response.json()["error"] == "NotFoundError"

    async with _session_factory(async_engine)() as session:
        # Nothing was created against either organization.
        assert await session.scalar(select(func.count()).select_from(Campaign)) == 0
        assert await session.scalar(select(func.count()).select_from(Post)) == 0
        # The foreign mount is untouched.
        still_there = await session.get(IntegrationMount, foreign_mount_id)
        assert still_there is not None
        assert still_there.organization_id == OTHER_ORG_ID


@pytest.mark.asyncio
async def test_intent_with_unknown_brand_returns_404(
    integrations_client, db_session, async_engine
):
    _, brand_id = await _seed(db_session)
    mount_id = await _create_mount(integrations_client, brand_id)

    response = await integrations_client.post(
        f"{MOUNT_URL}/{mount_id}/intent", json=_intent_payload(uuid.uuid4())
    )

    assert response.status_code == 404, response.text

    async with _session_factory(async_engine)() as session:
        assert await session.scalar(select(func.count()).select_from(Campaign)) == 0


@pytest.mark.asyncio
async def test_partial_ingest_rolls_back_completely(
    integrations_client, db_session, async_engine, monkeypatch
):
    """A mid-ingest failure must leave zero rows — no orphaned Campaign,
    Post, PostVersion, execution node or audit row."""
    _, brand_id = await _seed(db_session)
    mount_id = await _create_mount(integrations_client, brand_id)

    from app.services.integration_service import IntegrationService

    async def _boom(self, organization_id, post):
        raise RuntimeError("simulated failure after campaign + post were written")

    monkeypatch.setattr(IntegrationService, "_bootstrap_approval", _boom)

    with pytest.raises(RuntimeError):
        await integrations_client.post(
            f"{MOUNT_URL}/{mount_id}/intent", json=_intent_payload(brand_id)
        )

    async with _session_factory(async_engine)() as session:
        assert await session.scalar(select(func.count()).select_from(Campaign)) == 0
        assert await session.scalar(select(func.count()).select_from(Post)) == 0
        assert await session.scalar(select(func.count()).select_from(PostVersion)) == 0
        assert await session.scalar(select(func.count()).select_from(Approval)) == 0
        assert await session.scalar(select(func.count()).select_from(ExecutionNode)) == 0
        intent_audits = await session.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.entity_type == "IntegrationIntent")
        )
        assert intent_audits == 0
        # The mount itself was committed by an earlier request and survives.
        assert await session.scalar(select(func.count()).select_from(IntegrationMount)) == 1
