"""AgentTemplate: a reusable persona that produces a structured prompt body."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_types import StringArrayCompat
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


class AgentTemplate(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """Versioned, reusable marketing agent prompt template.

    Each row represents an agent persona with its rules, methodology, and
    output contract. The front-end treats it as read-mostly content and
    provides per-run copy support.
    """

    __tablename__ = "agent_templates"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "slug", "version", name="uq_agent_template_org_slug_version"
        ),
    )

    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000))
    template_body: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list | None] = mapped_column(StringArrayCompat)
    category: Mapped[str | None] = mapped_column(String(120), index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AgentTemplate slug={self.slug!r} v={self.version}>"
