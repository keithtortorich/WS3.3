"""Factory that instantiates the configured AIProvider.

Picks a concrete provider based on ``Settings.AI_PROVIDER`` (mirrors the
``AI_PROVIDER`` variable in .env.example). Only ``ollama`` is fully
implemented in this scaffold; every other value returns a typed stub that
raises ``NotImplementedError`` the moment a capability method is actually
called (not at construction time), so the app can still boot and route
requests to it — it just fails loudly and clearly when used.
"""
from __future__ import annotations

from functools import lru_cache

from app.ai.base import AIProvider
from app.ai.providers.claude import ClaudeProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.grok import GrokProvider
from app.ai.providers.hermes import HermesProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openai import OpenAIProvider
from app.core.config import get_settings

_PROVIDER_REGISTRY = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
    "gemini": GeminiProvider,
    "grok": GrokProvider,
    "hermes": HermesProvider,
}


def get_ai_provider(provider_name: str | None = None) -> AIProvider:
    """Instantiate the AI provider named by ``provider_name`` (defaults to
    ``Settings.AI_PROVIDER``). Raises ``ValueError`` for an unknown name —
    this is distinct from ``NotImplementedError``, which stub providers
    raise per-method once you actually try to use them.
    """
    settings = get_settings()
    name = (provider_name or settings.AI_PROVIDER).lower()
    provider_cls = _PROVIDER_REGISTRY.get(name)
    if provider_cls is None:
        raise ValueError(
            f"Unknown AI_PROVIDER '{name}'. Valid options: {sorted(_PROVIDER_REGISTRY)}"
        )
    return provider_cls()


@lru_cache
def get_default_ai_provider() -> AIProvider:
    """Cached singleton for the default (env-configured) provider — use
    this in FastAPI dependencies to avoid re-instantiating an HTTP client
    per request."""
    return get_ai_provider()
