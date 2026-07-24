"""Workflow graph persistence layer.

Tenant-scoped first: every query filters by tenant_id. Follows the same
raw-SQL shape as WorkflowRepository/ExecutionRepository, but bounded to
the execution-trace model from RETAINED_GRAPH_MODEL.md.
"""
from __future__ import annotations

from typing import Any, Optional

from .client import ExecutionNode
from .sync import (
    create_node,
    get_node,
    list_nodes,
    update_node_status,
)


class WorkflowGraphRepository:
    """Persists and loads workflow graph execution nodes.

    This is a thin seam. The actual SQL stays in `sync.py` so the client
    and router can call bounded helpers directly without depending on a
    class instance.
    """

    def __init__(self, conn: Any) -> None:
        self._conn = conn

    def add_node(self, node: ExecutionNode) -> ExecutionNode:
        return create_node(
            self._conn,
            tenant_id=node.tenant_id,
            workflow_instance_id=node.workflow_instance_id,
            node_id=node.node_id,
            type=node.type,
            status=node.status,
            payload_ref=node.payload_ref,
            parent_node_id=node.parent_node_id,
        )

    def get_node(
        self,
        tenant_id: str,
        workflow_instance_id: str,
        node_id: str,
    ) -> Optional[ExecutionNode]:
        return get_node(
            self._conn,
            tenant_id=tenant_id,
            workflow_instance_id=workflow_instance_id,
            node_id=node_id,
        )

    def list_nodes(
        self,
        tenant_id: str,
        workflow_instance_id: str,
    ) -> list[ExecutionNode]:
        return list_nodes(
            self._conn,
            tenant_id=tenant_id,
            workflow_instance_id=workflow_instance_id,
        )

    def update_node_status(
        self,
        *,
        tenant_id: str,
        workflow_instance_id: str,
        node_id: str,
        status: str,
        completed_at: str | None = None,
        failure_reason: str | None = None,
    ) -> ExecutionNode | None:
        return update_node_status(
            self._conn,
            tenant_id=tenant_id,
            workflow_instance_id=workflow_instance_id,
            node_id=node_id,
            status=status,
            completed_at=completed_at,
            failure_reason=failure_reason,
        )
