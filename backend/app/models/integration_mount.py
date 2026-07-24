"""IntegrationMount: the binding between an external system's tenant and an
SMM organization.

WHY THIS EXISTS
WS3.3 (WebStaffr) identifies tenants with bare public slugs generated from a
business name (``acme-hvac``). SMM identifies tenants with Clerk organization
ids (``org_ABC``) resolved from a verified JWT. Those two identity models are
deliberately NOT merged — see INTEGRATION_PLAN.md ("Do not paper over it with
shared-secret hacks"). This table is the explicit mapping between them: one
row per (organization, external system, external tenant), created once via
``POST /integrations/social-media-marketing/mount`` and thereafter used to
resolve inbound campaign intents to the correct SMM org.

The row is org-scoped like every other tenant table, so a mount created by
one organization is invisible to another even if its ``mount_id`` leaks.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID, StringArrayCompat
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.organization import Organization

#: Mount modes. ``agent_managed`` lets the SMM agent act unattended;
#: ``approval_required`` forces every generated post through review.
#: Kept as plain strings (not a DB Enum) because the vocabulary is owned by
#: the integration contract in INTEGRATION_PLAN.md, not by SMM's own domain
#: model — adding a mode should not require a schema migration.
MOUNT_MODE_AGENT_MANAGED = "agent_managed"
MOUNT_MODE_APPROVAL_REQUIRED = "approval_required"
MOUNT_MODES = (MOUNT_MODE_AGENT_MANAGED, MOUNT_MODE_APPROVAL_REQUIRED)

#: Default/only external system wired today.
EXTERNAL_SYSTEM_WEBSTAFFR = "webstaffr3.3"


class IntegrationMount(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """Maps ``(external_system, external_tenant_id)`` to this SMM organization."""

    __tablename__ = "integration_mounts"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "external_system",
            "external_tenant_id",
            name="uq_integration_mount_org_system_tenant",
        ),
    )

    external_system: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, default=EXTERNAL_SYSTEM_WEBSTAFFR
    )
    external_tenant_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    platforms: Mapped[list | None] = mapped_column(StringArrayCompat)
    default_brand_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("brands.id", ondelete="SET NULL"), index=True
    )
    #: The real Client that campaigns from this external tenant belong to.
    #: Binding the customer once, at mount time, is what keeps the intent path
    #: from having to guess per request — mounting is an operator action by
    #: someone who knows which customer this is. When set, it takes precedence
    #: over every other resolution step and no placeholder is ever created.
    default_client_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("clients.id", ondelete="SET NULL"), index=True
    )
    mode: Mapped[str] = mapped_column(
        String(50), nullable=False, default=MOUNT_MODE_APPROVAL_REQUIRED
    )

    organization: Mapped["Organization"] = relationship()
    default_brand: Mapped["Brand | None"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<IntegrationMount id={self.id} system={self.external_system!r}"
            f" tenant={self.external_tenant_id!r} mode={self.mode!r}>"
        )
