from __future__ import annotations

from app.models.agent_template import AgentTemplate
from app.repositories.base import OrgScopedRepository


class AgentTemplateRepository(OrgScopedRepository[AgentTemplate]):
    model = AgentTemplate
