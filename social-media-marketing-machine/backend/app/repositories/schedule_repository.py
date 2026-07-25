from __future__ import annotations

from app.models.schedule import Schedule
from app.repositories.base import OrgScopedRepository


class ScheduleRepository(OrgScopedRepository[Schedule]):
    model = Schedule
