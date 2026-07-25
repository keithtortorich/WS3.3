"""Approval: a review decision recorded against a Post."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import ApprovalStatus

if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.user import User


class Approval(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """One approval "checkpoint" instance for a Post (internal or client
    review). Multiple Approval rows accumulate across a Post's lifecycle.
    """

    __tablename__ = "approvals"

    post_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    stage: Mapped[str] = mapped_column(String(50), nullable=False, default="internal")
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approval_status"), nullable=False, default=ApprovalStatus.PENDING, index=True
    )
    feedback: Mapped[str | None] = mapped_column(String(4000))

    post: Mapped["Post"] = relationship(back_populates="approvals")
    reviewer: Mapped["User | None"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Approval post={self.post_id} stage={self.stage} status={self.status}>"
