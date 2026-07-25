"""Integration test: AgentTemplate endpoints."""

from __future__ import annotations

import uuid

import pytest

from app.models.agent_template import AgentTemplate
from app.schemas.agent_template import AgentTemplateCreate


async def _seed_agent(db_session, org_id: uuid.UUID) -> uuid.UUID:
    agent = AgentTemplate(
        organization_id=org_id,
        slug="test-agent",
        name="Test Agent",
        description="A test agent.",
        template_body="You are a test agent for {{client_name}} in {{industry}}.",
        variables=["client_name", "industry"],
        category="strategy",
        version=1,
        is_active=True,
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent.id


@pytest.mark.asyncio
async def test_create_agent_template(client, db_session):
    from tests.conftest import TEST_ORG_ID

    payload = {
        "slug": "competitive-intelligence-agent",
        "name": "Competitive Intelligence Agent",
        "description": "Research competitors.",
        "template_body": "You are Competitive Intelligence Agent...",
        "variables": ["company"],
        "category": "strategy",
        "version": 1,
    }
    response = await client.post("/api/v1/agents", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["slug"] == payload["slug"]
    assert data["category"] == "strategy"


@pytest.mark.asyncio
async def test_list_and_get_agent_template(client, db_session):
    from tests.conftest import TEST_ORG_ID

    agent_id = await _seed_agent(db_session, TEST_ORG_ID)

    list_response = await client.get("/api/v1/agents")
    assert list_response.status_code == 200
    items = list_response.json()
    assert any(item["id"] == str(agent_id) for item in items)

    get_response = await client.get(f"/api/v1/agents/{agent_id}")
    assert get_response.status_code == 200
    assert get_response.json()["slug"] == "test-agent"


@pytest.mark.asyncio
async def test_update_agent_template(client, db_session):
    from tests.conftest import TEST_ORG_ID

    agent_id = await _seed_agent(db_session, TEST_ORG_ID)
    patch_response = await client.patch(
        f"/api/v1/agents/{agent_id}", json={"is_active": False}
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_agent_template(client, db_session):
    from tests.conftest import TEST_ORG_ID

    agent_id = await _seed_agent(db_session, TEST_ORG_ID)
    delete_response = await client.delete(f"/api/v1/agents/{agent_id}")
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/agents/{agent_id}")
    assert get_response.status_code == 404
