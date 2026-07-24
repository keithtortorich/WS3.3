import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ExecutionNodeRefType, WorkflowNodeStatus, WorkflowNodeType
from app.models.execution_node import ExecutionNode
from app.repositories.base import OrgScopedRepository


class ExecutionNodeRepository(OrgScopedRepository[ExecutionNode]):
    model = ExecutionNode

    async def get(self, organization_id: Optional[str] = None, **kwargs) -> Optional[ExecutionNode]:
        return await self.get_by_id(organization_id=organization_id, obj_id=kwargs["id"])

    async def get_all_for_org(self, organization_id: uuid.UUID) -> Sequence[ExecutionNode]:
        stmt = select(self.model).where(self.model.organization_id == organization_id)
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def get_by_workflow_instance(self, organization_id: uuid.UUID, workflow_instance_id: uuid.UUID) -> Sequence[ExecutionNode]:
        stmt = select(self.model).where(
            self.model.organization_id == organization_id,
            self.model.workflow_instance_id == workflow_instance_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def get_by_ref(
        self,
        organization_id: uuid.UUID,
        *,
        ref_type: ExecutionNodeRefType,
        ref_id: uuid.UUID,
    ) -> Optional[ExecutionNode]:
        """Find the node that references a domain row (e.g. a PublishJob).

        Org-scoped like every other read here. Returns the most recently
        created match if several nodes reference the same row, so callers
        update the live one rather than a stale historical node.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.organization_id == organization_id,
                self.model.ref_type == ref_type,
                self.model.ref_id == ref_id,
            )
            .order_by(self.model.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

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
        await self.session.flush()
        return node
