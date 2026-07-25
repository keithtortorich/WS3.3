"""X (Twitter) adapter — typed stub. See app/social/platforms/_stub_base.py."""
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


class XAdapter(SocialPlatformAdapter):
    platform = "x"

    async def publish(self, request: PublishContentRequest) -> PublishContentResponse:
        raise not_implemented("X", "publish", "X_API_KEY / X_API_SECRET")

    async def schedule(self, request: ScheduleContentRequest) -> ScheduleContentResponse:
        raise not_implemented("X", "schedule", "X_API_KEY / X_API_SECRET")

    async def delete(self, request: DeleteContentRequest) -> None:
        raise not_implemented("X", "delete", "X_API_KEY / X_API_SECRET")

    async def update(self, request: UpdateContentRequest) -> None:
        raise not_implemented("X", "update", "X_API_KEY / X_API_SECRET")

    async def fetch_metrics(self, request: MetricsRequest) -> MetricsResponse:
        raise not_implemented("X", "fetch_metrics", "X_API_KEY / X_API_SECRET")

    def validate_media(self, request: MediaValidationRequest) -> MediaValidationResult:
        raise not_implemented("X", "validate_media", "X_API_KEY / X_API_SECRET")
