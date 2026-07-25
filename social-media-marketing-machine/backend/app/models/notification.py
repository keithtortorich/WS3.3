"""Notification: an in-app/email notification delivered to a User."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID, JSONBCompat
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import NotificationType

if TYPE_CHECKING:
    from app.models.user import User


class Notification(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """A notification targeted at a specific user within an organization."""

    __tablename__ = "notifications"

    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    link_url: Mapped[str | None] = mapped_column(String(1024))
    metadata_json: Mapped[dict | None] = mapped_column(JSONBCompat)
    is_read: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)

    recipient: Mapped["User"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Notification id={self.id} type={self.notification_type} read={self.is_read}>"
