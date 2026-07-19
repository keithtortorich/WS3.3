from __future__ import annotations

from app.models.publish_job import PublishJob
from app.repositories.base import OrgScopedRepository


class PublishJobRepository(OrgScopedRepository[PublishJob]):
    model = PublishJob
