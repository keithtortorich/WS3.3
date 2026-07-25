"""Integration tests for execution_nodes model + repository layer."""
from __future__ import annotations

import uuid

import pytest

from app.models.enums import WorkflowNodeStatus, WorkflowNodeType
from app.models.execution_node import ExecutionNode
from app.repositories.execution_node_repository import ExecutionNodeRepository


@pytest.mark.asyncio
async def test_create_and_get_execution_node(db_session):
    from tests.conftest import TEST_ORG_ID

    repo = ExecutionNodeRepository(db_session)
    workflow_id = uuid.uuid4()

    root = await repo.create_root(
        organization_id=TEST_ORG_ID,
        workflow_instance_id=workflow_id,
        display_name="campaign-root",
    )
    await db_session.commit()

    fetched = await repo.get(organization_id=str(TEST_ORG_ID), id=root.id)
    assert fetched is not None
    assert fetched.workflow_instance_id == workflow_id
    assert fetched.node_type == WorkflowNodeType.CAMPAIGN
    assert fetched.status == WorkflowNodeStatus.RUNNING
    assert fetched.display_name == "campaign-root"


@pytest.mark.asyncio
async def test_add_child_links_parent_and_workflow_instance(db_session):
    from tests.conftest import TEST_ORG_ID

    repo = ExecutionNodeRepository(db_session)
    workflow_id = uuid.uuid4()

    root = await repo.create_root(
        organization_id=TEST_ORG_ID,
        workflow_instance_id=workflow_id,
    )
    await db_session.commit()

    child = await repo.add_child(
        organization_id=TEST_ORG_ID,
        root_id=workflow_id,
        parent_node_id=root.id,
        node_type=WorkflowNodeType.APPROVAL,
        display_name="internal-review",
    )
    await db_session.commit()

    assert child.parent_node_id == root.id
    assert child.workflow_instance_id == workflow_id
    assert child.node_type == WorkflowNodeType.APPROVAL


@pytest.mark.asyncio
async def test_update_status_changes_status(db_session):
    from tests.conftest import TEST_ORG_ID

    repo = ExecutionNodeRepository(db_session)
    workflow_id = uuid.uuid4()

    root = await repo.create_root(
        organization_id=TEST_ORG_ID,
        workflow_instance_id=workflow_id,
    )
    await db_session.commit()

    updated = await repo.update_status(
        organization_id=TEST_ORG_ID,
        node_id=root.id,
        new_status=WorkflowNodeStatus.SUCCEEDED,
    )
    await db_session.commit()

    assert updated.status == WorkflowNodeStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_get_all_for_org_scoped(db_session):
    from tests.conftest import TEST_ORG_ID

    repo = ExecutionNodeRepository(db_session)
    other_org_id = uuid.uuid4()

    await repo.create_root(organization_id=TEST_ORG_ID, workflow_instance_id=uuid.uuid4())
    await repo.create_root(organization_id=other_org_id, workflow_instance_id=uuid.uuid4())
    await db_session.commit()

    nodes = await repo.get_all_for_org(TEST_ORG_ID)
    assert len(nodes) == 1
    assert nodes[0].organization_id == TEST_ORG_ID


@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_missing_node(db_session):
    from tests.conftest import TEST_ORG_ID

    repo = ExecutionNodeRepository(db_session)
    missing_id = uuid.uuid4()
    node = await repo.get(organization_id=str(TEST_ORG_ID), id=missing_id)
    assert node is None


@pytest.mark.asyncio
async def test_model_has_expected_tablename():
    assert ExecutionNode.__tablename__ == "execution_nodes"
