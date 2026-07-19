from __future__ import annotations

from app.models.approval import Approval
from app.repositories.base import OrgScopedRepository


class ApprovalRepository(OrgScopedRepository[Approval]):
    model = Approval
