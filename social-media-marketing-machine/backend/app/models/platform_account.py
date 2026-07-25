"""PlatformAccount: a connected social platform account (OAuth tokens) for a Brand."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import PlatformName

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.schedule import Schedule
    from app.models.publish_job import PublishJob


class PlatformAccount(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """OAuth connection between a Brand and a social platform account.

    Tokens are stored encrypted at rest in production (encryption handled
    at the service layer / a KMS-backed column-level encryption solution —
    out of scope for this scaffold; see docs/TROUBLESHOOTING.md). Here they
    are plain strings for scaffold simplicity.
    """

    __tablename__ = "platform_accounts"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[PlatformName] = mapped_column(
        Enum(PlatformName, name="platform_name"), nullable=False, index=True
    )
    external_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    access_token: Mapped[str | None] = mapped_column(String(4000))
    refresh_token: Mapped[str | None] = mapped_column(String(4000))
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    brand: Mapped["Brand"] = relationship(back_populates="platform_accounts")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="platform_account")
    publish_jobs: Mapped[List["PublishJob"]] = relationship(back_populates="platform_account")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PlatformAccount id={self.id} platform={self.platform}>"
