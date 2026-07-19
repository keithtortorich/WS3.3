from __future__ import annotations

from app.models.analytics import Analytics
from app.repositories.base import OrgScopedRepository


class AnalyticsRepository(OrgScopedRepository[Analytics]):
    model = Analytics
