"""Organization = the tenant boundary (a marketing agency)."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.user import OrganizationMembership
    from app.models.client import Client
    from app.models.team import Team


class Organization(UUIDPkMixin, TimestampMixin, Base):
    """A tenant (marketing agency). All other tenant-scoped tables hang off
    this via ``organization_id``.

    Note: ``clerk_org_id`` links this row to the corresponding Clerk
    Organization so JWT ``org_id`` claims can be resolved to a local
    Organization without a network round-trip on every request.
    """

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    clerk_org_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    memberships: Mapped[List["OrganizationMembership"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    clients: Mapped[List["Client"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    teams: Mapped[List["Team"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Organization id={self.id} slug={self.slug!r}>"
