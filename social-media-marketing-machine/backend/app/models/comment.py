"""Comment: threaded discussion attached to a Post (used in review workflow)."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.user import User


class Comment(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """A comment on a Post. ``parent_comment_id`` allows a single level (or
    more, if the client chooses to nest) of threaded replies.
    """

    __tablename__ = "comments"

    post_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    parent_comment_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("comments.id", ondelete="CASCADE"), index=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    resolved: Mapped[bool] = mapped_column(default=False, nullable=False)

    post: Mapped["Post"] = relationship(back_populates="comments")
    author: Mapped["User | None"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Comment id={self.id} post={self.post_id}>"
