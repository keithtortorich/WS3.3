"""Facebook adapter — typed stub. See app/social/platforms/_stub_base.py."""
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


class FacebookAdapter(SocialPlatformAdapter):
    platform = "facebook"

    async def publish(self, request: PublishContentRequest) -> PublishContentResponse:
        raise not_implemented("Facebook", "publish", "FACEBOOK_APP_ID / FACEBOOK_APP_SECRET")

    async def schedule(self, request: ScheduleContentRequest) -> ScheduleContentResponse:
        raise not_implemented("Facebook", "schedule", "FACEBOOK_APP_ID / FACEBOOK_APP_SECRET")

    async def delete(self, request: DeleteContentRequest) -> None:
        raise not_implemented("Facebook", "delete", "FACEBOOK_APP_ID / FACEBOOK_APP_SECRET")

    async def update(self, request: UpdateContentRequest) -> None:
        raise not_implemented("Facebook", "update", "FACEBOOK_APP_ID / FACEBOOK_APP_SECRET")

    async def fetch_metrics(self, request: MetricsRequest) -> MetricsResponse:
        raise not_implemented("Facebook", "fetch_metrics", "FACEBOOK_APP_ID / FACEBOOK_APP_SECRET")

    def validate_media(self, request: MediaValidationRequest) -> MediaValidationResult:
        raise not_implemented("Facebook", "validate_media", "FACEBOOK_APP_ID / FACEBOOK_APP_SECRET")
