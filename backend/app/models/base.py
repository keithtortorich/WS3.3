"""Declarative base + shared mixins for all ORM models.

Design notes:
- We use SQLAlchemy 2.0's ``DeclarativeBase`` (not the legacy
  ``declarative_base()`` factory) for full typing support with
  ``Mapped[...]`` / ``mapped_column``.
- Primary keys are UUIDs generated application-side via ``uuid.uuid4`` so
  that IDs are available before an INSERT round-trip (useful for building
  related objects in a single unit of work) and so the same code path works
  identically against PostgreSQL and SQLite in tests. PostgreSQL's
  ``gen_random_uuid()`` server-side default is intentionally NOT used, to
  keep dialect portability — see docs/TROUBLESHOOTING.md.
- ``TimestampMixin`` gives every table consistent ``created_at`` /
  ``updated_at`` columns.
- ``OrgScopedMixin`` gives every tenant-scoped table an indexed
  ``organization_id`` FK. This is the *data model* half of multi-tenancy;
  the *enforcement* half lives in ``app/repositories/base.py`` (see its
  docstring for why filtering happens at the repository layer).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import CHAR, TypeDecorator

from app.core.db_types import GUID


def utcnow() -> datetime:
    """Return a timezone-aware UTC now() for default timestamp values."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Shared declarative base for the entire ORM model graph."""

    type_annotation_map = {
        uuid.UUID: GUID,
    }


class UUIDPkMixin:
    """Application-generated UUID primary key.

    Generating the UUID in Python (rather than relying on a Postgres
    server_default) keeps model behavior identical across PostgreSQL and
    SQLite, which is required for the SQLite-backed test suite (task #12).
    """

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    """created_at / updated_at columns, maintained in Python for portability."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


class OrgScopedMixin:
    """Adds an indexed ``organization_id`` FK to every tenant-scoped table.

    EVERY table that stores tenant data must use this mixin. It is the
    schema-level half of defense-in-depth multi-tenancy: even if a
    repository or router forgot to filter by org, the FK/index still make
    the column trivially available for filtering and prevent orphaned
    cross-tenant references at the database level.
    """

    @property
    def _org_fk_target(self) -> str:  # pragma: no cover - documentation only
        return "organizations.id"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
