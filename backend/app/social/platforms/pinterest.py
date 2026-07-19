"""Pinterest adapter — typed stub. See app/social/platforms/_stub_base.py."""
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


class PinterestAdapter(SocialPlatformAdapter):
    platform = "pinterest"

    async def publish(self, request: PublishContentRequest) -> PublishContentResponse:
        raise not_implemented("Pinterest", "publish", "PINTEREST_APP_ID / PINTEREST_APP_SECRET")

    async def schedule(self, request: ScheduleContentRequest) -> ScheduleContentResponse:
        raise not_implemented("Pinterest", "schedule", "PINTEREST_APP_ID / PINTEREST_APP_SECRET")

    async def delete(self, request: DeleteContentRequest) -> None:
        raise not_implemented("Pinterest", "delete", "PINTEREST_APP_ID / PINTEREST_APP_SECRET")

    async def update(self, request: UpdateContentRequest) -> None:
        raise not_implemented("Pinterest", "update", "PINTEREST_APP_ID / PINTEREST_APP_SECRET")

    async def fetch_metrics(self, request: MetricsRequest) -> MetricsResponse:
        raise not_implemented("Pinterest", "fetch_metrics", "PINTEREST_APP_ID / PINTEREST_APP_SECRET")

    def validate_media(self, request: MediaValidationRequest) -> MediaValidationResult:
        raise not_implemented("Pinterest", "validate_media", "PINTEREST_APP_ID / PINTEREST_APP_SECRET")
