"""Unit tests for WorkflowService execution graph operations."""
from __future__ import annotations

import uuid
from typing import Optional, Sequence

import pytest

from app.models.enums import WorkflowNodeStatus, WorkflowNodeType
from app.models.execution_node import ExecutionNode
from app.services.workflow_service import WorkflowService


class InMemoryNode:
    def __init__(self, node: ExecutionNode):
        for key in (
            "id",
            "organization_id",
            "workflow_instance_id",
            "parent_node_id",
            "node_type",
            "status",
            "display_name",
            "ref_id",
            "ref_type",
            "failure_reason",
            "completed_at",
        ):
            setattr(self, key, getattr(node, key))


class InMemoryExecutionNodeRepository:
    def __init__(self) -> None:
        self.nodes: dict[uuid.UUID, InMemoryNode] = {}
        self.session = self

    async def create(self, obj: ExecutionNode) -> ExecutionNode:
        if obj.id is None:
            obj.id = uuid.uuid4()
        self.nodes[obj.id] = InMemoryNode(obj)
        return obj

    async def get_by_id(self, organization_id: uuid.UUID, obj_id: uuid.UUID) -> Optional[ExecutionNode]:
        node = self.nodes.get(obj_id)
        return ExecutionNode(**node.__dict__) if node else None

    async def get_all_for_org(self, organization_id: uuid.UUID) -> Sequence[ExecutionNode]:
        return [ExecutionNode(**node.__dict__) for node in self.nodes.values()]

    async def get_by_workflow_instance(self, organization_id: uuid.UUID, workflow_instance_id: uuid.UUID) -> Sequence[ExecutionNode]:
        return [
            ExecutionNode(**node.__dict__)
            for node in self.nodes.values()
            if node.workflow_instance_id == workflow_instance_id
        ]

    async def create_root(
        self,
        organization_id: uuid.UUID,
        workflow_instance_id: uuid.UUID,
        display_name: Optional[str] = None,
    ) -> ExecutionNode:
        node = ExecutionNode(
            organization_id=organization_id,
            workflow_instance_id=workflow_instance_id,
            node_type=WorkflowNodeType.CAMPAIGN,
            status=WorkflowNodeStatus.RUNNING,
            display_name=display_name,
        )
        return await self.create(node)

    async def add_child(
        self,
        organization_id: uuid.UUID,
        *,
        root_id: uuid.UUID,
        parent_node_id: uuid.UUID,
        node_type: WorkflowNodeType,
        display_name: Optional[str] = None,
    ) -> ExecutionNode:
        node = ExecutionNode(
            organization_id=organization_id,
            workflow_instance_id=root_id,
            parent_node_id=parent_node_id,
            node_type=node_type,
            display_name=display_name,
        )
        return await self.create(node)

    async def update_status(
        self,
        organization_id: uuid.UUID,
        node_id: uuid.UUID,
        new_status: WorkflowNodeStatus,
    ) -> ExecutionNode:
        node = await self.get_by_id(organization_id=organization_id, obj_id=node_id)
        if node is None:
            raise ValueError("node not found")
        node.status = new_status
        await self.flush()
        return node

    async def flush(self) -> None:
        return None


class FakeWorkflowService(WorkflowService):
    def __init__(self) -> None:
        self.repository = InMemoryExecutionNodeRepository()


@pytest.mark.asyncio
async def test_create_workflow_instance_creates_campaign_root() -> None:
    service = FakeWorkflowService()
    org_id = uuid.uuid4()
    workflow_id = uuid.uuid4()

    root = await service.create_workflow_instance(
        organization_id=org_id,
        workflow_instance_id=workflow_id,
        display_name="test-workflow",
    )

    assert root.organization_id == org_id
    assert root.workflow_instance_id == workflow_id
    assert root.node_type == WorkflowNodeType.CAMPAIGN
    assert root.status == WorkflowNodeStatus.RUNNING
    assert root.display_name == "test-workflow"


@pytest.mark.asyncio
async def test_append_child_node_links_to_parent() -> None:
    service = FakeWorkflowService()
    org_id = uuid.uuid4()
    workflow_id = uuid.uuid4()

    root = await service.create_workflow_instance(
        organization_id=org_id,
        workflow_instance_id=workflow_id,
    )
    child = await service.append_child_node(
        organization_id=org_id,
        workflow_instance_id=workflow_id,
        parent_node_id=root.id,
        node_type=WorkflowNodeType.APPROVAL,
        display_name="approval-1",
    )

    assert child.parent_node_id == root.id
    assert child.workflow_instance_id == workflow_id
    assert child.node_type == WorkflowNodeType.APPROVAL
    assert child.display_name == "approval-1"


@pytest.mark.asyncio
async def test_update_node_status_sets_completed_at_for_terminal_statuses() -> None:
    service = FakeWorkflowService()
    org_id = uuid.uuid4()
    workflow_id = uuid.uuid4()

    root = await service.create_workflow_instance(
        organization_id=org_id,
        workflow_instance_id=workflow_id,
    )
    updated = await service.update_node_status(
        organization_id=org_id,
        node_id=root.id,
        new_status=WorkflowNodeStatus.SUCCEEDED,
        failure_reason=None,
    )

    assert updated.status == WorkflowNodeStatus.SUCCEEDED
    assert updated.completed_at is not None


@pytest.mark.asyncio
async def test_update_node_status_sets_failure_reason() -> None:
    service = FakeWorkflowService()
    org_id = uuid.uuid4()
    workflow_id = uuid.uuid4()

    root = await service.create_workflow_instance(
        organization_id=org_id,
        workflow_instance_id=workflow_id,
    )
    updated = await service.update_node_status(
        organization_id=org_id,
        node_id=root.id,
        new_status=WorkflowNodeStatus.FAILED,
        failure_reason=" publish timeout",
    )

    assert updated.status == WorkflowNodeStatus.FAILED
    assert updated.failure_reason == " publish timeout"


@pytest.mark.asyncio
async def test_get_nodes_returns_nodes_for_workflow_instance() -> None:
    service = FakeWorkflowService()
    org_id = uuid.uuid4()
    workflow_id = uuid.uuid4()

    await service.create_workflow_instance(
        organization_id=org_id,
        workflow_instance_id=workflow_id,
        display_name="root",
    )

    nodes = await service.get_nodes(organization_id=org_id, workflow_instance_id=workflow_id)
    assert len(nodes) == 1


@pytest.mark.asyncio
async def test_create_workflow_instance_generates_display_name_when_none() -> None:
    service = FakeWorkflowService()
    org_id = uuid.uuid4()
    workflow_id = uuid.uuid4()

    root = await service.create_workflow_instance(
        organization_id=org_id,
        workflow_instance_id=workflow_id,
    )
    assert root.display_name is not None
    assert "workflow-" in root.display_name
