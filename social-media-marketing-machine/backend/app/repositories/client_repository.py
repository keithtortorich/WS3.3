from __future__ import annotations

from app.models.client import Client
from app.repositories.base import OrgScopedRepository


class ClientRepository(OrgScopedRepository[Client]):
    model = Client
