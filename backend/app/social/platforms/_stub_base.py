"""Shared helper for the typed-stub social platform adapters."""
from __future__ import annotations


def not_implemented(platform_name: str, capability: str, env_hint: str) -> NotImplementedError:
    return NotImplementedError(
        f"{platform_name}Adapter.{capability}() is not implemented in this scaffold. "
        f"To enable it: configure {env_hint} in your .env, then implement {capability}() "
        f"in app/social/platforms/{platform_name.lower()}.py following the pattern "
        f"established in app/social/platforms/linkedin.py."
    )
