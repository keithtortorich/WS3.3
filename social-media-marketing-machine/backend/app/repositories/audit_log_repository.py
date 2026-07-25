from __future__ import annotations

from app.models.audit_log import AuditLog
from app.repositories.base import OrgScopedRepository


class AuditLogRepository(OrgScopedRepository[AuditLog]):
    model = AuditLog
