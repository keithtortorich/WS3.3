"""YouTube adapter — typed stub. See app/social/platforms/_stub_base.py."""
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


class YouTubeAdapter(SocialPlatformAdapter):
    platform = "youtube"

    async def publish(self, request: PublishContentRequest) -> PublishContentResponse:
        raise not_implemented("YouTube", "publish", "YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET")

    async def schedule(self, request: ScheduleContentRequest) -> ScheduleContentResponse:
        raise not_implemented("YouTube", "schedule", "YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET")

    async def delete(self, request: DeleteContentRequest) -> None:
        raise not_implemented("YouTube", "delete", "YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET")

    async def update(self, request: UpdateContentRequest) -> None:
        raise not_implemented("YouTube", "update", "YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET")

    async def fetch_metrics(self, request: MetricsRequest) -> MetricsResponse:
        raise not_implemented("YouTube", "fetch_metrics", "YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET")

    def validate_media(self, request: MediaValidationRequest) -> MediaValidationResult:
        raise not_implemented("YouTube", "validate_media", "YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET")
