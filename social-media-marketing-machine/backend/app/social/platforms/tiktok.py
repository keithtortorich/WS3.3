"""TikTok adapter — typed stub. See app/social/platforms/_stub_base.py."""
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


class TikTokAdapter(SocialPlatformAdapter):
    platform = "tiktok"

    async def publish(self, request: PublishContentRequest) -> PublishContentResponse:
        raise not_implemented("TikTok", "publish", "TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET")

    async def schedule(self, request: ScheduleContentRequest) -> ScheduleContentResponse:
        raise not_implemented("TikTok", "schedule", "TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET")

    async def delete(self, request: DeleteContentRequest) -> None:
        raise not_implemented("TikTok", "delete", "TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET")

    async def update(self, request: UpdateContentRequest) -> None:
        raise not_implemented("TikTok", "update", "TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET")

    async def fetch_metrics(self, request: MetricsRequest) -> MetricsResponse:
        raise not_implemented("TikTok", "fetch_metrics", "TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET")

    def validate_media(self, request: MediaValidationRequest) -> MediaValidationResult:
        raise not_implemented("TikTok", "validate_media", "TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET")
