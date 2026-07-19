"""Threads adapter — typed stub. See app/social/platforms/_stub_base.py."""
from __future__ import annotations

from app.social.base import SocialPlatformAdapter
from app.social.platforms._stub_base import not_implemented
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


class ThreadsAdapter(SocialPlatformAdapter):
    platform = "threads"

    async def publish(self, request: PublishContentRequest) -> PublishContentResponse:
        raise not_implemented("Threads", "publish", "THREADS_APP_ID / THREADS_APP_SECRET")

    async def schedule(self, request: ScheduleContentRequest) -> ScheduleContentResponse:
        raise not_implemented("Threads", "schedule", "THREADS_APP_ID / THREADS_APP_SECRET")

    async def delete(self, request: DeleteContentRequest) -> None:
        raise not_implemented("Threads", "delete", "THREADS_APP_ID / THREADS_APP_SECRET")

    async def update(self, request: UpdateContentRequest) -> None:
        raise not_implemented("Threads", "update", "THREADS_APP_ID / THREADS_APP_SECRET")

    async def fetch_metrics(self, request: MetricsRequest) -> MetricsResponse:
        raise not_implemented("Threads", "fetch_metrics", "THREADS_APP_ID / THREADS_APP_SECRET")

    def validate_media(self, request: MediaValidationRequest) -> MediaValidationResult:
        raise not_implemented("Threads", "validate_media", "THREADS_APP_ID / THREADS_APP_SECRET")
