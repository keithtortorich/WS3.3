"""Analytics: time-series performance metrics pulled from platform APIs."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID, JSONBCompat
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.post import Post


class Analytics(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """A single metrics snapshot for a Post, captured at ``captured_at``.
    Storing snapshots (rather than mutating one row) lets us chart trends
    over time.
    """

    __tablename__ = "analytics"

    post_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shares: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    engagement_rate: Mapped[float | None] = mapped_column(Numeric(6, 4))
    raw_payload: Mapped[dict | None] = mapped_column(JSONBCompat)

    post: Mapped["Post"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Analytics post={self.post_id} at={self.captured_at}>"
