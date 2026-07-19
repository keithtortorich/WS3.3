from __future__ import annotations

from app.models.prompt_template import PromptTemplate
from app.repositories.base import OrgScopedRepository


class PromptTemplateRepository(OrgScopedRepository[PromptTemplate]):
    model = PromptTemplate
