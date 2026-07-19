from __future__ import annotations

from app.models.brand import Brand
from app.repositories.base import OrgScopedRepository


class BrandRepository(OrgScopedRepository[Brand]):
    model = Brand
