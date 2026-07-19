from __future__ import annotations

from app.models.notification import Notification
from app.repositories.base import OrgScopedRepository


class NotificationRepository(OrgScopedRepository[Notification]):
    model = Notification
