from __future__ import annotations

from app.models.platform_account import PlatformAccount
from app.repositories.base import OrgScopedRepository


class PlatformAccountRepository(OrgScopedRepository[PlatformAccount]):
    model = PlatformAccount
