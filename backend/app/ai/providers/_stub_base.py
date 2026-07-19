"""Shared helper for the typed-stub AI providers.

Each stub provider (OpenAI/Claude/Gemini/Grok/Hermes) fully satisfies the
``AIProvider`` interface so the app can construct and route to it without
import errors, but every method raises ``NotImplementedError`` with a
message telling the developer exactly what to configure and implement.
"""
from __future__ import annotations


def not_implemented(provider_name: str, capability: str, env_key: str) -> NotImplementedError:
    return NotImplementedError(
        f"{provider_name}.{capability}() is not implemented in this scaffold. "
        f"To enable it: set AI_PROVIDER={provider_name.lower()} and {env_key} in your .env, "
        f"then implement {capability}() in app/ai/providers/{provider_name.lower()}.py "
        f"following the pattern established in app/ai/providers/ollama.py."
    )
