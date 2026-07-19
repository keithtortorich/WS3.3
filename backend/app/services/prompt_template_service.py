"""Prompt template engine: fills a Jinja2 PromptTemplate with campaign/brand
variables and dispatches the rendered prompt through the configured AI
provider (via ``app.ai.factory``).

The variable set below (brand, voice, audience, platform, goal, offer, cta,
keywords, campaign, post_type) is the shared vocabulary every starter
template in ``app/templates/*.jinja2`` is written against — passing extra
keys is harmless (Jinja2 ignores unused context), and missing keys render
as empty strings via ``undefined=jinja2.Undefined`` (chosen deliberately so
a template with an optional variable, e.g. ``offer``, doesn't hard-fail).
"""
from __future__ import annotations

from typing import Any, Optional

import jinja2

from app.ai.base import AIProvider
from app.ai.schemas import TextGenerationRequest, TextGenerationResponse
from app.core.exceptions import ValidationAppError
from app.models.prompt_template import PromptTemplate

_jinja_env = jinja2.Environment(
    undefined=jinja2.Undefined,  # missing variables render as empty string, not an error
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,  # prompts are plain text, not HTML
)


class PromptVariables:
    """Typed container for the standard prompt variable vocabulary.

    Using a dedicated class (rather than a bare dict) means a typo in a
    variable name is caught by the constructor's keyword arguments rather
    than silently producing an empty substitution at render time.
    """

    def __init__(
        self,
        *,
        brand: str,
        voice: str = "",
        audience: str = "",
        platform: str = "",
        goal: str = "",
        offer: Optional[str] = None,
        cta: str = "",
        keywords: Optional[list[str]] = None,
        campaign: str = "",
        post_type: str = "standard",
    ) -> None:
        self.brand = brand
        self.voice = voice
        self.audience = audience
        self.platform = platform
        self.goal = goal
        self.offer = offer
        self.cta = cta
        self.keywords = keywords or []
        self.campaign = campaign
        self.post_type = post_type

    def as_dict(self) -> dict[str, Any]:
        return {
            "brand": self.brand,
            "voice": self.voice,
            "audience": self.audience,
            "platform": self.platform,
            "goal": self.goal,
            "offer": self.offer,
            "cta": self.cta,
            "keywords": self.keywords,
            "campaign": self.campaign,
            "post_type": self.post_type,
        }


class PromptTemplateService:
    """Renders a :class:`PromptTemplate` and (optionally) sends it to an AI
    provider to produce generated content."""

    def __init__(self, ai_provider: AIProvider) -> None:
        self.ai_provider = ai_provider

    def render(self, template: PromptTemplate, variables: PromptVariables) -> str:
        """Render the template body with the given variables. Raises
        :class:`ValidationAppError` on a Jinja2 syntax error in the stored
        template (should only happen if a template was hand-edited badly)."""
        try:
            jinja_template = _jinja_env.from_string(template.template_body)
            return jinja_template.render(**variables.as_dict())
        except jinja2.TemplateSyntaxError as exc:
            raise ValidationAppError(f"Prompt template '{template.slug}' has invalid syntax: {exc}") from exc

    async def render_and_generate(
        self,
        template: PromptTemplate,
        variables: PromptVariables,
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> TextGenerationResponse:
        """Render the template and immediately generate text via the
        configured AI provider — the common end-to-end path used by
        "Generate caption" / "Generate hooks" / "Generate hashtags" UI actions."""
        prompt = self.render(template, variables)
        request = TextGenerationRequest(prompt=prompt, max_tokens=max_tokens, temperature=temperature)
        return await self.ai_provider.generate_text(request)
