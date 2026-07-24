"""Workflow graph models and client surface.

This is a thin seam, not a full graph engine. Persistence stays in
`sync.py` and `repository.py`; this module only defines the public
dataclasses and a thin client wrapper so callers can swap in an
HTTP-backed client later without changing router/handler code.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ExecutionNode:
    node_id: str
    tenant_id: str
    workflow_instance_id: str
    type: str
    status: str
    payload_ref: Optional[str]
    parent_node_id: Optional[str]
    created_at: str
    completed_at: Optional[str]
    failure_reason: Optional[str]


VALID_NODE_TYPES = frozenset(
    {"intake", "campaign", "post", "publish_job", "approval", "integration_event"}
)
VALID_STATUSES = frozenset(
    {"pending", "active", "awaiting_approval", "completed", "failed", "canceled"}
)


class WorkflowGraphError(RuntimeError):
    """Raised when workflow graph integration config or calls fail."""


class WorkflowGraphClient:
    """Thin wrapper around WorkflowGraphRepository so routers can swap
    this for an HTTP-backed client later without changing handler code.
    """

    def __init__(self, conn: Any) -> None:
        self._conn = conn

    def create_node(
        self,
        *,
        tenant_id: str,
        workflow_instance_id: str,
        node_id: str,
        type: str,
        status: str,
        payload_ref: Optional[str] = None,
        parent_node_id: Optional[str] = None,
    ) -> ExecutionNode:
        from .sync import create_node
        return create_node(
            self._conn,
            tenant_id=tenant_id,
            workflow_instance_id=workflow_instance_id,
            node_id=node_id,
            type=type,
            status=status,
            payload_ref=payload_ref,
            parent_node_id=parent_node_id,
        )

    def get_node(
        self,
        *,
        tenant_id: str,
        workflow_instance_id: str,
        node_id: str,
    ) -> Optional[ExecutionNode]:
        from .sync import get_node
        return get_node(
            self._conn,
            tenant_id=tenant_id,
            workflow_instance_id=workflow_instance_id,
            node_id=node_id,
        )

    def list_nodes(
        self,
        *,
        tenant_id: str,
        workflow_instance_id: str,
    ) -> list[ExecutionNode]:
        from .sync import list_nodes
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
        completed_at: Optional[str] = None,
        failure_reason: Optional[str] = None,
    ) -> Optional[ExecutionNode]:
        from .sync import update_node_status
        return update_node_status(
            self._conn,
            tenant_id=tenant_id,
            workflow_instance_id=workflow_instance_id,
            node_id=node_id,
            status=status,
            completed_at=completed_at,
            failure_reason=failure_reason,
        )
