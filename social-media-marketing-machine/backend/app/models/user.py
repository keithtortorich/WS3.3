"""User + OrganizationMembership (users can belong to multiple orgs)."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID
from app.models.base import Base, TimestampMixin, UUIDPkMixin
from app.models.enums import OrgRole

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.team import TeamMembership


class User(UUIDPkMixin, TimestampMixin, Base):
    """A person. Identity is owned by Clerk; this row mirrors what we need
    locally (denormalized for fast joins) and is keyed by ``clerk_user_id``.

    Users are NOT tenant-scoped directly — a single human can belong to
    multiple organizations (e.g. a freelancer working with two agencies),
    modeled via :class:`OrganizationMembership`.
    """

    __tablename__ = "users"

    clerk_user_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(1024))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    memberships: Mapped[List["OrganizationMembership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email!r}>"


class OrganizationMembership(UUIDPkMixin, TimestampMixin, Base):
    """Join table: which role a User has within an Organization."""

    __tablename__ = "organization_memberships"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_membership_org_user"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[OrgRole] = mapped_column(Enum(OrgRole, name="org_role"), nullable=False, default=OrgRole.MEMBER)

    organization: Mapped["Organization"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="memberships")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<OrganizationMembership org={self.organization_id} user={self.user_id} role={self.role}>"
