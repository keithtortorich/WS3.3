"""Team + TeamMembership: sub-groupings of users within an organization."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


class Team(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """A team within an agency (e.g. "Paid Social", "Client Success")."""

    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))

    organization: Mapped["Organization"] = relationship(back_populates="teams")
    memberships: Mapped[List["TeamMembership"]] = relationship(
        back_populates="team", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Team id={self.id} name={self.name!r}>"


class TeamMembership(UUIDPkMixin, TimestampMixin, Base):
    """Join table: which users belong to which team."""

    __tablename__ = "team_memberships"
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_membership_team_user"),
    )

    team_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    team: Mapped["Team"] = relationship(back_populates="memberships")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TeamMembership team={self.team_id} user={self.user_id}>"
