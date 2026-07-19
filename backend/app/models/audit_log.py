"""AuditLog: immutable record of significant actions, including approval
state machine transitions (task #8)."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import GUID, JSONBCompat
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import AuditAction

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """Append-only audit trail. ``entity_type``/``entity_id`` identify the
    affected row generically so a single table can audit the whole schema.
    """

    __tablename__ = "audit_logs"

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction, name="audit_action"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(GUID, index=True)
    description: Mapped[str | None] = mapped_column(String(2000))
    metadata_json: Mapped[dict | None] = mapped_column(JSONBCompat)

    actor: Mapped["User | None"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuditLog id={self.id} action={self.action} entity={self.entity_type}:{self.entity_id}>"
