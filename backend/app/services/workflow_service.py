"""WorkflowService: application coordinate for execution graph operations."""
from __future__ import annotations

import datetime
import uuid
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import WorkflowNodeStatus, WorkflowNodeType
from app.models.execution_node import ExecutionNode
from app.repositories.execution_node_repository import ExecutionNodeRepository


class WorkflowService:
    def __init__(self, db: AsyncSession) -> None:
        self.repository = ExecutionNodeRepository(db)

    async def create_workflow_instance(self, organization_id: uuid.UUID, *, workflow_instance_id: uuid.UUID, display_name: str | None = None) -> ExecutionNode:
        if display_name is None:
            display_name = f"workflow-{workflow_instance_id.hex[:8]}"
        node = ExecutionNode(
            organization_id=organization_id,
            workflow_instance_id=workflow_instance_id,
            node_type=WorkflowNodeType.CAMPAIGN,
            status=WorkflowNodeStatus.RUNNING,
            display_name=display_name,
        )
        await self.repository.create(node)
        return node

    async def append_child_node(self, organization_id: uuid.UUID, *, workflow_instance_id: uuid.UUID, parent_node_id: uuid.UUID, node_type: WorkflowNodeType, display_name: str | None = None) -> ExecutionNode:
        return await self.repository.add_child(
            organization_id=organization_id,
            root_id=workflow_instance_id,
            parent_node_id=parent_node_id,
            node_type=node_type,
            display_name=display_name,
        )

    async def update_node_status(self, organization_id: uuid.UUID, *, node_id: uuid.UUID, new_status: WorkflowNodeStatus, failure_reason: str | None = None) -> ExecutionNode:
        node = await self.repository.update_status(organization_id=organization_id, node_id=node_id, new_status=new_status)
        node.failure_reason = failure_reason
        if new_status in {
            WorkflowNodeStatus.RUNNING,
            WorkflowNodeStatus.SUCCEEDED,
            WorkflowNodeStatus.FAILED,
            WorkflowNodeStatus.CANCELLED,
        }:
            node.completed_at = datetime.datetime.now(datetime.timezone.utc)
        await self.repository.session.flush()
        return node

    async def get_nodes(self, organization_id: uuid.UUID, *, workflow_instance_id: uuid.UUID) -> Sequence[ExecutionNode]:
        return await self.repository.get_by_workflow_instance(
            organization_id=organization_id,
            workflow_instance_id=workflow_instance_id,
        )
