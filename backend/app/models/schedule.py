"""Schedule: when a Post is planned to publish to a specific PlatformAccount."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.platform_account import PlatformAccount


class Schedule(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """A planned publish time for a Post on a given PlatformAccount. The
    Celery beat/worker layer (task #9) polls due schedules and creates
    PublishJob rows.
    """

    __tablename__ = "schedules"

    post_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform_account_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("platform_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    is_cancelled: Mapped[bool] = mapped_column(default=False, nullable=False)

    post: Mapped["Post"] = relationship(back_populates="schedules")
    platform_account: Mapped["PlatformAccount"] = relationship(back_populates="schedules")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Schedule post={self.post_id} at={self.scheduled_at}>"
