"""Google Business Profile adapter — typed stub. See app/social/platforms/_stub_base.py."""
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


class GoogleBusinessAdapter(SocialPlatformAdapter):
    platform = "google_business"

    async def publish(self, request: PublishContentRequest) -> PublishContentResponse:
        raise not_implemented("GoogleBusiness", "publish", "GOOGLE_BUSINESS_CLIENT_ID / GOOGLE_BUSINESS_CLIENT_SECRET")

    async def schedule(self, request: ScheduleContentRequest) -> ScheduleContentResponse:
        raise not_implemented("GoogleBusiness", "schedule", "GOOGLE_BUSINESS_CLIENT_ID / GOOGLE_BUSINESS_CLIENT_SECRET")

    async def delete(self, request: DeleteContentRequest) -> None:
        raise not_implemented("GoogleBusiness", "delete", "GOOGLE_BUSINESS_CLIENT_ID / GOOGLE_BUSINESS_CLIENT_SECRET")

    async def update(self, request: UpdateContentRequest) -> None:
        raise not_implemented("GoogleBusiness", "update", "GOOGLE_BUSINESS_CLIENT_ID / GOOGLE_BUSINESS_CLIENT_SECRET")

    async def fetch_metrics(self, request: MetricsRequest) -> MetricsResponse:
        raise not_implemented("GoogleBusiness", "fetch_metrics", "GOOGLE_BUSINESS_CLIENT_ID / GOOGLE_BUSINESS_CLIENT_SECRET")

    def validate_media(self, request: MediaValidationRequest) -> MediaValidationResult:
        raise not_implemented("GoogleBusiness", "validate_media", "GOOGLE_BUSINESS_CLIENT_ID / GOOGLE_BUSINESS_CLIENT_SECRET")
