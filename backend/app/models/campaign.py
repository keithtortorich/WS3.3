"""Campaign: a time-boxed marketing effort containing many Posts."""
from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING, List

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import CampaignStatus

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.client import Client
    from app.models.brand import Brand
    from app.models.post import Post


class Campaign(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """A marketing campaign: groups Posts under a shared goal/date range."""

    __tablename__ = "campaigns"

    client_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("brands.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    goal: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, name="campaign_status"), nullable=False, default=CampaignStatus.DRAFT, index=True
    )
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    budget_cents: Mapped[int | None] = mapped_column()

    client: Mapped["Client"] = relationship(back_populates="campaigns")
    brand: Mapped["Brand | None"] = relationship(back_populates="campaigns")
    posts: Mapped[List["Post"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Campaign id={self.id} name={self.name!r} status={self.status}>"
