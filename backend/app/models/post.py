"""Post: a single piece of social content moving through the approval
state machine (task #8) toward publication."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID, StringArrayCompat
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import PostStatus

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.user import User
    from app.models.post_version import PostVersion
    from app.models.media import Media
    from app.models.approval import Approval
    from app.models.comment import Comment
    from app.models.schedule import Schedule
    from app.models.publish_job import PublishJob


class Post(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """A social media post. ``platform`` denotes the target platform;
    ``status`` mirrors :class:`app.models.enums.PostStatus` and is
    transitioned exclusively via ``app.services.approval_state_machine``.
    """

    __tablename__ = "posts"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    post_type: Mapped[str] = mapped_column(String(50), nullable=False, default="standard")
    caption: Mapped[str] = mapped_column(Text, nullable=False, default="")
    hashtags: Mapped[list | None] = mapped_column(StringArrayCompat)
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus, name="post_status"), nullable=False, default=PostStatus.DRAFT, index=True
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="posts")
    created_by: Mapped["User | None"] = relationship()
    versions: Mapped[List["PostVersion"]] = relationship(
        back_populates="post", cascade="all, delete-orphan", order_by="PostVersion.version_number"
    )
    media_items: Mapped[List["Media"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    approvals: Mapped[List["Approval"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    comments: Mapped[List["Comment"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    publish_jobs: Mapped[List["PublishJob"]] = relationship(back_populates="post", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Post id={self.id} platform={self.platform} status={self.status}>"
