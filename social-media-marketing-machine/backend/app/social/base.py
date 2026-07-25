"""Abstract base for pluggable social platform adapters.

Mirrors the AI provider abstraction pattern (``app/ai/base.py``): every
platform-specific quirk (auth flow, API shapes, media constraints) is
hidden behind this interface so the rest of the app (publish workers,
routers) only ever talks to :class:`SocialPlatformAdapter`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.social.schemas import (
    DeleteContentRequest,
    MediaValidationRequest,
    MediaValidationResult,
    MetricsRequest,
    MetricsResponse,
    PublishContentRequest,
    PublishContentResponse,
    ScheduleContentRequest,
    ScheduleContentResponse,
    UpdateContentRequest,
)


class SocialPlatformAdapter(ABC):
    """Abstract interface every social platform adapter must implement."""

    platform: str

    @abstractmethod
    async def publish(self, request: PublishContentRequest) -> PublishContentResponse:
        """Publish content immediately to the platform."""

    @abstractmethod
    async def schedule(self, request: ScheduleContentRequest) -> ScheduleContentResponse:
        """Schedule content for future publication via the platform's own
        native scheduling API (if supported) rather than our own worker."""

    @abstractmethod
    async def delete(self, request: DeleteContentRequest) -> None:
        """Delete previously published content."""

    @abstractmethod
    async def update(self, request: UpdateContentRequest) -> None:
        """Update previously published content, if the platform allows edits."""

    @abstractmethod
    async def fetch_metrics(self, request: MetricsRequest) -> MetricsResponse:
        """Fetch engagement metrics for a previously published post."""

    @abstractmethod
    def validate_media(self, request: MediaValidationRequest) -> MediaValidationResult:
        """Validate a media asset against the platform's documented
        constraints (file size, format, dimensions) BEFORE attempting
        upload — this is synchronous/local validation, no network call."""
