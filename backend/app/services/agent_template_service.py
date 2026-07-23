"""AgentTemplate prompt renderer.

This is intentionally separated from PromptTemplateService because agent
prompts are broader marketing work personas, not content/campaign templates
with a shared std vocab. Sharing the same container would conflate two
different prompt domains and discard the richer attributes agents need.
"""
from __future__ import annotations

from typing import Any

import jinja2

from app.ai.base import AIProvider
from app.ai.schemas import TextGenerationRequest, TextGenerationResponse
from app.core.exceptions import ValidationAppError
from app.models.agent_template import AgentTemplate

_agent_jinja_env = jinja2.Environment(
    undefined=jinja2.Undefined,
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
)


class AgentRunParams:
    """Typed container for the agent prompt variable vocabulary."""

    def __init__(
        self,
        *,
        task_context: str = "",
        client_name: str = "",
        industry: str = "",
        location: str = "",
        website_url: str = "",
        brand_voice: str = "",
        audience: str = "",
        campaign: str = "",
        goal: str = "",
        notes: str = "",
    ) -> None:
        self.task_context = task_context
        self.client_name = client_name
        self.industry = industry
        self.location = location
        self.website_url = website_url
        self.brand_voice = brand_voice
        self.audience = audience
        self.campaign = campaign
        self.goal = goal
        self.notes = notes

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_context": self.task_context,
            "client_name": self.client_name,
            "industry": self.industry,
            "location": self.location,
            "website_url": self.website_url,
            "brand_voice": self.brand_voice,
            "audience": self.audience,
            "campaign": self.campaign,
            "goal": self.goal,
            "notes": self.notes,
        }


class AgentTemplateService:
    """Renders an agent template and optionally sends the rendered prompt to
    the configured AI provider."""

    def __init__(self, ai_provider: AIProvider) -> None:
        self.ai_provider = ai_provider

    def render(self, template: AgentTemplate, variables: AgentRunParams) -> str:
        try:
            jinja_template = _agent_jinja_env.from_string(template.template_body)
            return jinja_template.render(**variables.as_dict())
        except jinja2.TemplateSyntaxError as exc:
            raise ValidationAppError(
                f"AgentTemplate '{template.slug}' has invalid syntax: {exc}"
            ) from exc

    async def render_and_generate(
        self,
        template: AgentTemplate,
        variables: AgentRunParams,
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> TextGenerationResponse:
        prompt = self.render(template, variables)
        request = TextGenerationRequest(prompt=prompt, max_tokens=max_tokens, temperature=temperature)
        return await self.ai_provider.generate_text(request)
