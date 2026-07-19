"""Brand: a distinct brand identity under a Client (a client may run several)."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID, JSONBCompat, StringArrayCompat
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.client import Client
    from app.models.campaign import Campaign
    from app.models.platform_account import PlatformAccount


class Brand(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """A brand voice/identity belonging to a Client. Drives AI prompt
    variables (voice, audience, keywords) used by the prompt template
    engine (task #7).
    """

    __tablename__ = "brands"

    client_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    voice: Mapped[str | None] = mapped_column(String(2000))
    audience: Mapped[str | None] = mapped_column(String(2000))
    keywords: Mapped[list | None] = mapped_column(StringArrayCompat)
    logo_url: Mapped[str | None] = mapped_column(String(1024))
    brand_colors: Mapped[dict | None] = mapped_column(JSONBCompat)
    guidelines: Mapped[str | None] = mapped_column(String(8000))

    client: Mapped["Client"] = relationship(back_populates="brands")
    campaigns: Mapped[List["Campaign"]] = relationship(back_populates="brand", cascade="all, delete-orphan")
    platform_accounts: Mapped[List["PlatformAccount"]] = relationship(
        back_populates="brand", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Brand id={self.id} name={self.name!r}>"
