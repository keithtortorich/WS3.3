"""PostVersion: immutable snapshot of a Post's content at a point in time.

Written by the approval state machine (task #8) on every content change so
reviewers can diff revisions and so a rejected/edited post can be audited.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID, StringArrayCompat
from app.models.base import Base, TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.user import User


class PostVersion(UUIDPkMixin, TimestampMixin, Base):
    """A single historical revision of a Post's editable content."""

    __tablename__ = "post_versions"
    __table_args__ = (
        UniqueConstraint("post_id", "version_number", name="uq_post_version_number"),
    )

    post_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    caption: Mapped[str] = mapped_column(Text, nullable=False, default="")
    hashtags: Mapped[list | None] = mapped_column(StringArrayCompat)
    edited_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL")
    )
    change_summary: Mapped[str | None] = mapped_column(String(1000))

    post: Mapped["Post"] = relationship(back_populates="versions")
    edited_by: Mapped["User | None"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PostVersion post={self.post_id} v={self.version_number}>"
