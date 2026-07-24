"""Client: an agency's customer (the entity campaigns are run on behalf of)."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.brand import Brand
    from app.models.campaign import Campaign


class Client(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """A client company that the agency (Organization) manages social media
    for. One Organization has many Clients; one Client has many Brands.
    """

    __tablename__ = "clients"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(255))
    website_url: Mapped[str | None] = mapped_column(String(1024))
    contact_name: Mapped[str | None] = mapped_column(String(255))
    contact_email: Mapped[str | None] = mapped_column(String(320))
    notes: Mapped[str | None] = mapped_column(String(4000))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    #: True when this row was auto-created by an integration because an inbound
    #: campaign had to hang off some Client and none was bound. It is real data
    #: that must not be silently dropped, but it is not a customer anyone
    #: onboarded — the flag exists so operators can list placeholders and merge
    #: them into real Clients instead of discovering them by name convention.
    is_placeholder: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)

    organization: Mapped["Organization"] = relationship(back_populates="clients")
    brands: Mapped[List["Brand"]] = relationship(back_populates="client", cascade="all, delete-orphan")
    campaigns: Mapped[List["Campaign"]] = relationship(back_populates="client", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Client id={self.id} name={self.name!r}>"
