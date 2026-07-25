"""Integration test: POST /api/v1/campaigns then GET it back, against the
real FastAPI app wired to an in-memory SQLite DB (get_db overridden)."""
from __future__ import annotations

import uuid

import pytest

from app.models.client import Client
from app.models.organization import Organization


async def _seed_client(db_session, org_id: uuid.UUID) -> uuid.UUID:
    org = Organization(id=org_id, name="Test Org", slug=f"test-org-{org_id.hex[:8]}")
    db_session.add(org)
    await db_session.flush()

    client_row = Client(organization_id=org_id, name="Test Client")
    db_session.add(client_row)
    await db_session.commit()
    return client_row.id


@pytest.mark.asyncio
async def test_create_and_get_campaign(client, db_session):
    from tests.conftest import TEST_ORG_ID

    client_id = await _seed_client(db_session, TEST_ORG_ID)

    create_payload = {
        "name": "Q3 Product Launch",
        "goal": "Drive awareness for the new product line",
        "client_id": str(client_id),
        "status": "draft",
    }
    create_response = await client.post("/api/v1/campaigns", json=create_payload)
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["name"] == "Q3 Product Launch"
    assert created["status"] == "draft"
    campaign_id = created["id"]

    get_response = await client.get(f"/api/v1/campaigns/{campaign_id}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["id"] == campaign_id
    assert fetched["name"] == "Q3 Product Launch"
    assert fetched["client_id"] == str(client_id)


@pytest.mark.asyncio
async def test_list_campaigns_pagination_envelope(client, db_session):
    from tests.conftest import TEST_ORG_ID

    client_id = await _seed_client(db_session, TEST_ORG_ID)

    for i in range(3):
        resp = await client.post(
            "/api/v1/campaigns",
            json={"name": f"Campaign {i}", "client_id": str(client_id)},
        )
        assert resp.status_code == 201

    list_response = await client.get("/api/v1/campaigns?page=1&page_size=2")
    assert list_response.status_code == 200
    page = list_response.json()
    assert page["total"] == 3
    assert page["page"] == 1
    assert page["page_size"] == 2
    assert len(page["items"]) == 2
    assert page["total_pages"] == 2


@pytest.mark.asyncio
async def test_get_nonexistent_campaign_returns_404(client):
    response = await client.get(f"/api/v1/campaigns/{uuid.uuid4()}")
    assert response.status_code == 404
    body = response.json()
    assert body["error"] == "NotFoundError"
