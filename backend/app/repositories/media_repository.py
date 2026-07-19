from __future__ import annotations

from app.models.media import Media
from app.repositories.base import OrgScopedRepository


class MediaRepository(OrgScopedRepository[Media]):
    model = Media
