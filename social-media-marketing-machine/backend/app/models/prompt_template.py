"""PromptTemplate: a versioned, reusable Jinja2 prompt used by the prompt
template engine (task #7)."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import StringArrayCompat
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin


class PromptTemplate(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """A named, versioned Jinja2 template body plus the list of variable
    names it expects (for validation/introspection by the UI).
    """

    __tablename__ = "prompt_templates"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", "version", name="uq_prompt_template_org_slug_version"),
    )

    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000))
    template_body: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list | None] = mapped_column(StringArrayCompat)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PromptTemplate slug={self.slug!r} v={self.version}>"
