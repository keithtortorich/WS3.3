"""Task: a work item (not to be confused with a Celery task) — e.g. "record
video for campaign X" — assignable to a user."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import TaskStatus

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.campaign import Campaign


class Task(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """A generic work item, optionally linked to a Campaign, assignable to
    a User, with a due date and status.
    """

    __tablename__ = "tasks"

    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    assignee_user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"), nullable=False, default=TaskStatus.TODO, index=True
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    assignee: Mapped["User | None"] = relationship()
    campaign: Mapped["Campaign | None"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Task id={self.id} title={self.title!r} status={self.status}>"
