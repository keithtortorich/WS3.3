"""Execution node row in the workflow execution graph."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import ExecutionNodeRefType, WorkflowNodeStatus, WorkflowNodeType

if TYPE_CHECKING:
    from app.models.organization import Organization


class ExecutionNode(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """A step/event tracked inside an execution graph."""

    __tablename__ = "execution_nodes"

    workflow_instance_id: Mapped[uuid.UUID] = mapped_column(
        GUID, nullable=False, index=True
    )
    parent_node_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("execution_nodes.id", ondelete="SET NULL"),
        index=True,
    )
    node_type: Mapped[WorkflowNodeType] = mapped_column(
        Enum(WorkflowNodeType, name="workflow_node_type"),
        nullable=False,
        index=True,
    )
    status: Mapped[WorkflowNodeStatus] = mapped_column(
        Enum(WorkflowNodeStatus, name="workflow_node_status"),
        nullable=False,
        default=WorkflowNodeStatus.PENDING,
        index=True,
    )
    display_name: Mapped[str | None] = mapped_column(String(255))
    ref_id: Mapped[uuid.UUID | None] = mapped_column(GUID, index=True)
    ref_type: Mapped[ExecutionNodeRefType | None] = mapped_column(
        Enum(ExecutionNodeRefType, name="execution_node_ref_type"),
        index=True,
    )
    failure_reason: Mapped[str | None] = mapped_column(String(1000))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    organization: Mapped["Organization"] = relationship()
    parent: Mapped["ExecutionNode | None"] = relationship(
        remote_side="ExecutionNode.id",
        back_populates="children",
    )
    children: Mapped[list["ExecutionNode"]] = relationship(back_populates="parent")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ExecutionNode id={self.id} workflow={self.workflow_instance_id}"
            f" type={self.node_type.value} status={self.status.value}>"
        )
