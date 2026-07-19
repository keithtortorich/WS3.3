"""PublishJob: a concrete attempt (or series of retry attempts) to publish a
Post to a platform. Consumed by the Celery publish worker (task #9)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import PublishJobStatus

if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.platform_account import PlatformAccount


class PublishJob(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """Tracks one publish attempt lifecycle, including retry bookkeeping
    (``attempt_count`` / ``max_attempts`` used by the exponential-backoff
    retry task in ``app.workers.tasks.publish_tasks``).
    """

    __tablename__ = "publish_jobs"

    post_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform_account_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("platform_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[PublishJobStatus] = mapped_column(
        Enum(PublishJobStatus, name="publish_job_status"),
        nullable=False,
        default=PublishJobStatus.QUEUED,
        index=True,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    last_error: Mapped[str | None] = mapped_column(Text)
    external_post_id: Mapped[str | None] = mapped_column(String(255))
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    post: Mapped["Post"] = relationship(back_populates="publish_jobs")
    platform_account: Mapped["PlatformAccount"] = relationship(back_populates="publish_jobs")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PublishJob id={self.id} status={self.status} attempt={self.attempt_count}>"
