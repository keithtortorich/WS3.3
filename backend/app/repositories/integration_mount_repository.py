"""IntegrationMount repository.

Org-scoped like every other tenant repository: ``get_by_id`` (inherited)
already folds ``organization_id`` into the WHERE clause, so a mount id
belonging to another organization resolves to ``None`` rather than leaking.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select

from app.models.integration_mount import IntegrationMount
from app.repositories.base import OrgScopedRepository


class IntegrationMountRepository(OrgScopedRepository[IntegrationMount]):
    model = IntegrationMount

    async def get_by_external_tenant(
        self,
        organization_id: uuid.UUID,
        *,
        external_system: str,
        external_tenant_id: str,
    ) -> Optional[IntegrationMount]:
        """Look up the mount for an external tenant within one organization."""
        stmt = select(self.model).where(
            self.model.organization_id == organization_id,
            self.model.external_system == external_system,
            self.model.external_tenant_id == external_tenant_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
