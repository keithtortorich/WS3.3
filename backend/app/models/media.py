"""Media: an image/video/gif/document asset attached to a Post."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import MediaType

if TYPE_CHECKING:
    from app.models.post import Post


class Media(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """A media asset stored in S3-compatible object storage. ``storage_key``
    is the bucket-relative key; ``url`` is the publicly resolvable URL
    (built from ``S3_PUBLIC_URL_BASE``).
    """

    __tablename__ = "media"

    post_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("posts.id", ondelete="CASCADE"), index=True
    )
    media_type: Mapped[MediaType] = mapped_column(Enum(MediaType, name="media_type"), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(255))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    alt_text: Mapped[str | None] = mapped_column(String(1000))
    ai_generated: Mapped[bool] = mapped_column(default=False, nullable=False)

    post: Mapped["Post | None"] = relationship(back_populates="media_items")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Media id={self.id} type={self.media_type}>"
