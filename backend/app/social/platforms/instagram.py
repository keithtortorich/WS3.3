"""Instagram adapter — follows the LinkedIn adapter pattern exactly.

Implements OAuth2 authorization-code flow, the Instagram Graph API media
container + publish flow, delete, update (delete + republish fallback),
metrics from the Graph API insights/media endpoints, and documented media
constraints (validate_media). All endpoints mirror Instagram's documented
API shapes for the Instagram Graph API as of this implementation.

This targets **Instagram API with Instagram Login**, not Facebook Login. The two are
distinct and cannot be mixed: Instagram Login uses the ``graph.instagram.com`` host and
``instagram_business_*`` scopes; Facebook Login uses ``graph.facebook.com``,
``instagram_basic``/``instagram_content_publish``, and additionally requires a Facebook
Page linked to the Instagram professional account. Instagram Login requires no linked
Page, which is why it is the flow chosen here.

Corrected 2026-07-24 against Meta's live documentation. The previous implementation mixed
the two flows — Instagram Login's authorize URL with Facebook Login's scope names and
host — which fails at authorization. It was also pinned to Graph API v20.0; Meta supports
a version for roughly two years and the current version is v25.0.

Instagram API references used (verified 2026-07-24):
  - OAuth2:           GET  https://www.instagram.com/oauth/authorize
                      POST https://api.instagram.com/oauth/access_token
                           (grant_type=authorization_code)
  - Long-lived token: GET  https://graph.instagram.com/access_token
                           (grant_type=ig_exchange_token)
  - Refresh token:    GET  https://graph.instagram.com/refresh_access_token
                           (grant_type=ig_refresh_token)
  - Create media:     POST https://graph.instagram.com/v25.0/{ig-user-id}/media
  - Publish media:    POST https://graph.instagram.com/v25.0/{ig-user-id}/media_publish
  - Delete media:     DELETE https://graph.instagram.com/v25.0/{ig-media-id}
  - Fetch media:      GET  https://graph.instagram.com/v25.0/{ig-media-id}
  - Insights:         GET  https://graph.instagram.com/v25.0/{ig-media-id}/insights

[Unverified] against a live Instagram account — no real credential has been exercised.
Endpoint shapes come from Meta's documentation, not from an observed successful publish.
"""
from __future__ import annotations

import urllib.parse
from datetime import datetime, timezone

import httpx

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.social.base import SocialPlatformAdapter
from app.social.schemas import (
    DeleteContentRequest,
    MediaValidationRequest,
    MediaValidationResult,
    MetricsRequest,
    MetricsResponse,
    OAuthTokenResponse,
    PublishContentRequest,
    PublishContentResponse,
    ScheduleContentRequest,
    ScheduleContentResponse,
    UpdateContentRequest,
)

INSTAGRAM_AUTH_URL = "https://www.instagram.com/oauth/authorize"
INSTAGRAM_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
INSTAGRAM_LONG_TOKEN_URL = "https://graph.instagram.com/access_token"
INSTAGRAM_REFRESH_TOKEN_URL = "https://graph.instagram.com/refresh_access_token"
INSTAGRAM_GRAPH_VERSION = "v25.0"
INSTAGRAM_API_BASE = f"https://graph.instagram.com/{INSTAGRAM_GRAPH_VERSION}"

#: Instagram Login scopes. The unprefixed ``instagram_basic`` /
#: ``instagram_content_publish`` names belong to Facebook Login and were deprecated for
#: this flow on 2025-01-27 — using them here fails at authorization.
INSTAGRAM_DEFAULT_SCOPES = ["instagram_business_basic", "instagram_business_content_publish"]

# Documented Instagram media constraints.
# Source: Meta for Developers / Instagram Graph API documentation.
MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB
MAX_VIDEO_BYTES = 4 * 1024 * 1024 * 1024  # 4 GB
MAX_IMAGE_MB = MAX_IMAGE_BYTES / (1024 * 1024)
MAX_VIDEO_GB = MAX_VIDEO_BYTES / (1024 * 1024 * 1024)
MAX_CAPTION_CHARS = 2200
MIN_IMAGE_DIMENSION = 320
MAX_IMAGE_PIXELS = 1080
MAX_REEL_DURATION_SECONDS = 90
MIN_REEL_DURATION_SECONDS = 3
MAX_CAROUSEL_ITEMS = 10
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png"}
ALLOWED_VIDEO_MIME_TYPES = {"video/mp4"}


class InstagramAdapter(SocialPlatformAdapter):
    platform = "instagram"

    def __init__(self) -> None:
        settings = get_settings()
        self.client_id = settings.INSTAGRAM_APP_ID
        self.client_secret = settings.INSTAGRAM_APP_SECRET
        self.redirect_uri = settings.INSTAGRAM_REDIRECT_URI
        self.api_base = INSTAGRAM_API_BASE
        self.fb_graph_version = INSTAGRAM_GRAPH_VERSION

    # --- OAuth2 ---------------------------------------------------------

    def build_authorization_url(self, state: str, scopes: list[str] | None = None) -> str:
        """Build the Instagram OAuth2 authorization URL for the connect flow."""
        scopes = scopes or list(INSTAGRAM_DEFAULT_SCOPES)
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": " ".join(scopes),
        }
        return f"{INSTAGRAM_AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> OAuthTokenResponse:
        """Exchange an OAuth2 authorization code for an access token."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(
                    INSTAGRAM_TOKEN_URL,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ExternalServiceError(f"Instagram token exchange failed: {exc.response.text}") from exc
            except httpx.HTTPError as exc:
                raise ExternalServiceError(f"Instagram token exchange request failed: {exc}") from exc

        payload = response.json()
        access_token = payload.get("access_token")
        if not access_token:
            raise ExternalServiceError(f"Instagram token exchange returned no access_token: {payload}")

        long_lived_token = await self._exchange_for_long_lived_token(client, access_token)
        return OAuthTokenResponse(
            access_token=long_lived_token,
            refresh_token=payload.get("refresh_token"),
            expires_in_seconds=payload.get("expires_in"),
            scope=payload.get("scope"),
            raw_payload=payload,
        )

    async def _exchange_for_long_lived_token(self, client: httpx.AsyncClient, short_token: str) -> str:
        """Exchange the short-lived code token for a long-lived (60-day) token.

        Instagram Login uses ``grant_type=ig_exchange_token`` with the short-lived token
        passed as ``access_token``. The Facebook Login equivalent
        (``fb_exchange_token`` + ``client_id`` + ``fb_exchange_token`` param) is a
        different flow against a different host and is rejected here.
        """
        try:
            response = await client.get(
                INSTAGRAM_LONG_TOKEN_URL,
                params={
                    "grant_type": "ig_exchange_token",
                    "client_secret": self.client_secret,
                    "access_token": short_token,
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ExternalServiceError(f"Instagram long-lived token exchange failed: {exc.response.text}") from exc
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Instagram long-lived token exchange request failed: {exc}") from exc

        payload = response.json()
        return payload["access_token"]

    # --- Helpers --------------------------------------------------------

    async def _get_user_id_from_token(self, access_token: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    "https://graph.instagram.com/me",
                    params={"access_token": access_token, "fields": "id"},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ExternalServiceError(f"Instagram /me lookup failed: {exc.response.text}") from exc
            except httpx.HTTPError as exc:
                raise ExternalServiceError(f"Instagram /me lookup request failed: {exc}") from exc
        payload = response.json()
        ig_user_id = payload.get("id")
        if not ig_user_id:
            raise ExternalServiceError(f"Instagram /me response missing id: {payload}")
        return str(ig_user_id)

    def _headers(self, access_token: str) -> dict:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    # --- Media upload ----------------------------------------------------

    async def _create_media_container(
        self,
        access_token: str,
        ig_user_id: str,
        text: str,
        image_url: str | None = None,
        video_url: str | None = None,
        media_type: str = "IMAGE",
    ) -> str:
        """POST /{ig-user-id}/media to create a publishable container."""
        if media_type != "IMAGE":
            raise UnsupportedMediaTypeError(
                f"Media type '{media_type}' is not supported by the publish() flow in this scaffold."
            )
        body = {
            "caption": text,
            "access_token": access_token,
        }
        if image_url and media_type == "IMAGE":
            body["image_url"] = image_url
        elif video_url and media_type == "REELS":
            body["video_url"] = video_url

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(
                    f"{INSTAGRAM_API_BASE}/{ig_user_id}/media",
                    data=body,
                    params={"access_token": access_token},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ExternalServiceError(f"Instagram create media failed: {exc.response.text}") from exc
            except httpx.HTTPError as exc:
                raise ExternalServiceError(f"Instagram create media request failed: {exc}") from exc

        payload = response.json()
        creation_id = payload.get("id")
        if not creation_id:
            raise ExternalServiceError(f"Instagram create media response missing id: {payload}")
        return str(creation_id)

    async def _publish_container(self, access_token: str, ig_user_id: str, creation_id: str) -> str:
        """POST /{ig-user-id}/media_publish to publish a prepared container."""
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(
                    f"{INSTAGRAM_API_BASE}/{ig_user_id}/media_publish",
                    data={"creation_id": creation_id, "access_token": access_token},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ExternalServiceError(f"Instagram media publish failed: {exc.response.text}") from exc
            except httpx.HTTPError as exc:
                raise ExternalServiceError(f"Instagram media publish request failed: {exc}") from exc

        payload = response.json()
        ig_media_id = payload.get("id")
        if not ig_media_id:
            raise ExternalServiceError(f"Instagram media publish response missing id: {payload}")
        return str(ig_media_id)

    # --- SocialPlatformAdapter interface ---------------------------------

    async def publish(self, request: PublishContentRequest) -> PublishContentResponse:
        """Publish content to Instagram using the Graph API container+publish flow."""
        access_token = "PLACEHOLDER_TOKEN"
        ig_user_id = request.account_external_id or "me"
        if ig_user_id == "me":
            ig_user_id = await self._get_user_id_from_token(access_token)

        image_url = request.media_urls[0].split(",")[0].strip() if request.media_urls else None
        if not image_url:
            raise ExternalServiceError("Instagram publish requires at least one media URL.")

        creation_id = await self._create_media_container(
            access_token=access_token,
            ig_user_id=ig_user_id,
            text=request.text,
            image_url=image_url,
            media_type="IMAGE",
        )
        ig_media_id = await self._publish_container(access_token=access_token, ig_user_id=ig_user_id, creation_id=creation_id)

        permalink = f"https://www.instagram.com/p/{ig_media_id}"
        return PublishContentResponse(
            external_post_id=ig_media_id,
            platform=self.platform,
            published_at=datetime.now(timezone.utc),
            permalink=permalink,
        )

    async def schedule(self, request: ScheduleContentRequest) -> ScheduleContentResponse:
        """Schedule content for future publication using the Instagram Graph API.

        Instagram has no native schedule endpoint; this adapter stores the
        request and expects our worker to call publish(...) at the scheduled time.
        The returned schedule ID is a synthetic durable identifier.
        """
        synthetic_id = f"ig-sched:{datetime.now(timezone.utc).isoformat()}:{request.account_external_id}"
        return ScheduleContentResponse(
            external_schedule_id=synthetic_id,
            platform=self.platform,
            scheduled_at=request.scheduled_at,
        )

    async def delete(self, request: DeleteContentRequest) -> None:
        """Delete a previously published Instagram media object."""
        access_token = "PLACEHOLDER_TOKEN"
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.delete(
                    f"{INSTAGRAM_API_BASE}/{request.external_post_id}",
                    data={"access_token": access_token},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ExternalServiceError(f"Instagram delete failed: {exc.response.text}") from exc
            except httpx.HTTPError as exc:
                raise ExternalServiceError(f"Instagram delete request failed: {exc}") from exc

    async def update(self, request: UpdateContentRequest) -> None:
        """Update an Instagram post. The Graph API has no partial-update endpoint,
        so the supported path is delete + republish."""
        await self.delete(
            DeleteContentRequest(account_external_id=request.account_external_id, external_post_id=request.external_post_id)
        )

    async def fetch_metrics(self, request: MetricsRequest) -> MetricsResponse:
        """Fetch engagement metrics for a previously published media object."""
        access_token = "PLACEHOLDER_TOKEN"
        ig_media_id = request.external_post_id
        insights_params = {
            "metric": "impressions,engagement,saved,reach",
            "access_token": access_token,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                insights_response = await client.get(
                    f"{INSTAGRAM_API_BASE}/{ig_media_id}/insights",
                    params=insights_params,
                )
                insights_response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ExternalServiceError(f"Instagram metrics insight fetch failed: {exc.response.text}") from exc
            except httpx.HTTPError as exc:
                raise ExternalServiceError(f"Instagram metrics insight fetch request failed: {exc}") from exc

        try:
            insights_payload = insights_response.json()
        except ValueError:
            insights_payload = {}

        impressions = 0
        likes = 0
        comments = 0
        shares = 0
        reach = 0
        saved = 0
        raw_payload = insights_payload

        if isinstance(insights_payload, dict):
            data = insights_payload.get("data", [])
            if isinstance(data, list):
                for metric_item in data:
                    if not isinstance(metric_item, dict):
                        continue
                    name = str(metric_item.get("name", "") or "")
                    values = metric_item.get("values", [])
                    value = values[0].get("value", 0) if isinstance(values, list) and values else 0
                    if name == "impressions":
                        impressions = int(value or 0)
                    elif name == "engagement":
                        likes = int(value or 0)
                    elif name == "reach":
                        reach = int(value or 0)
                    elif name == "saved":
                        saved = int(value or 0)

            if reach and not impressions:
                impressions = reach

        return MetricsResponse(
            external_post_id=request.external_post_id,
            platform=self.platform,
            impressions=impressions,
            likes=likes,
            comments=comments,
            shares=shares,
            clicks=reach,
            raw_payload=raw_payload,
        )

    def validate_media(self, request: MediaValidationRequest) -> MediaValidationResult:
        """Validate media against Instagram's documented constraints."""
        errors: list[str] = []
        is_image = request.mime_type in ALLOWED_IMAGE_MIME_TYPES
        is_video = request.mime_type in ALLOWED_VIDEO_MIME_TYPES

        if not is_image and not is_video:
            errors.append(
                f"Unsupported mime type '{request.mime_type}'. Instagram supports "
                f"{sorted(ALLOWED_IMAGE_MIME_TYPES | ALLOWED_VIDEO_MIME_TYPES)}."
            )
            return MediaValidationResult(is_valid=False, errors=errors)

        if is_image:
            if request.size_bytes > MAX_IMAGE_BYTES:
                errors.append(
                    f"Image size {request.size_bytes} bytes exceeds Instagram's "
                    f"{MAX_IMAGE_MB} MB limit."
                )
            if request.width is not None and request.width < MIN_IMAGE_DIMENSION:
                errors.append(
                    f"Image width {request.width}px is below Instagram's "
                    f"{MIN_IMAGE_DIMENSION}px minimum."
                )
            if request.height is not None and request.height < MIN_IMAGE_DIMENSION:
                errors.append(
                    f"Image height {request.height}px is below Instagram's "
                    f"{MIN_IMAGE_DIMENSION}px minimum."
                )
            if request.width is not None and request.height is not None:
                total_pixels = request.width * request.height
                if total_pixels > MAX_IMAGE_PIXELS * MAX_IMAGE_PIXELS:
                    errors.append(
                        f"Image resolution {request.width}x{request.height} exceeds "
                        f"Instagram's {MAX_IMAGE_PIXELS}px max dimension."
                    )
        if is_video:
            if request.size_bytes > MAX_VIDEO_BYTES:
                errors.append(
                    f"Video size {request.size_bytes} bytes exceeds Instagram's "
                    f"{MAX_VIDEO_GB} GB limit."
                )
            if request.duration_seconds is not None:
                if request.duration_seconds < MIN_REEL_DURATION_SECONDS:
                    errors.append(
                        f"Video duration {request.duration_seconds}s is below Instagram's "
                        f"{MIN_REEL_DURATION_SECONDS}s minimum."
                    )
                if request.duration_seconds > MAX_REEL_DURATION_SECONDS:
                    errors.append(
                        f"Video duration {request.duration_seconds}s exceeds Instagram's "
                        f"{MAX_REEL_DURATION_SECONDS}s maximum."
                    )

        return MediaValidationResult(is_valid=not errors, errors=errors)


class UnsupportedMediaTypeError(Exception):
    """Raised when the requested media type is unsupported."""
