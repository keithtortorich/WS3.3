"""Unit tests for the Instagram social platform adapter, mirroring test_linkedin_adapter."""
from __future__ import annotations

import httpx
import pytest

from app.social.platforms.instagram import (
    INSTAGRAM_GRAPH_VERSION,
    INSTAGRAM_LONG_TOKEN_URL,
    INSTAGRAM_REFRESH_TOKEN_URL,
    InstagramAdapter,
    MAX_IMAGE_BYTES,
    MAX_VIDEO_BYTES,
)
from app.social.schemas import (
    DeleteContentRequest,
    MediaValidationRequest,
    MetricsRequest,
    OAuthTokenResponse,
    PublishContentRequest,
    ScheduleContentRequest,
    UpdateContentRequest,
)


def test_build_authorization_url_contains_required_params():
    adapter = InstagramAdapter()
    url = adapter.build_authorization_url(state="abc123")
    assert "response_type=code" in url
    assert "state=abc123" in url
    assert "client_id=" in url
    assert url.startswith("https://www.instagram.com/oauth/authorize")


def test_validate_media_accepts_valid_jpeg():
    adapter = InstagramAdapter()
    result = adapter.validate_media(
        MediaValidationRequest(mime_type="image/jpeg", size_bytes=1_000_000)
    )
    assert result.is_valid is True
    assert result.errors == []


def test_validate_media_accepts_valid_video():
    adapter = InstagramAdapter()
    result = adapter.validate_media(
        MediaValidationRequest(mime_type="video/mp4", size_bytes=1_000_000_000)
    )
    assert result.is_valid is True
    assert result.errors == []


def test_validate_media_rejects_oversized_image():
    adapter = InstagramAdapter()
    result = adapter.validate_media(
        MediaValidationRequest(mime_type="image/png", size_bytes=MAX_IMAGE_BYTES + 1)
    )
    assert result.is_valid is False
    assert "exceeds Instagram's" in result.errors[0]


def test_validate_media_rejects_oversized_video():
    adapter = InstagramAdapter()
    result = adapter.validate_media(
        MediaValidationRequest(mime_type="video/mp4", size_bytes=MAX_VIDEO_BYTES + 1)
    )
    assert result.is_valid is False
    assert "exceeds Instagram's" in result.errors[0]


def test_validate_media_rejects_unsupported_mime_type():
    adapter = InstagramAdapter()
    result = adapter.validate_media(
        MediaValidationRequest(mime_type="image/bmp", size_bytes=1000)
    )
    assert result.is_valid is False
    assert "Unsupported mime type" in result.errors[0]


def test_validate_media_rejects_too_small_image_dimensions():
    adapter = InstagramAdapter()
    result = adapter.validate_media(
        MediaValidationRequest(
            mime_type="image/jpeg",
            size_bytes=100_000,
            width=100,
            height=100,
        )
    )
    assert result.is_valid is False
    assert any("width" in err or "height" in err for err in result.errors)


def test_validate_media_rejects_too_large_video_duration():
    adapter = InstagramAdapter()
    result = adapter.validate_media(
        MediaValidationRequest(
            mime_type="video/mp4",
            size_bytes=100_000_000,
            duration_seconds=120,
        )
    )
    assert result.is_valid is False
    assert any("maximum" in err.lower() and "90" in err for err in result.errors)


@pytest.mark.asyncio
async def test_publish_constructs_graph_calls_and_returns_id(monkeypatch):
    adapter = InstagramAdapter()
    captured_posts: list[dict] = []

    async def fake_post(self, url, data=None, json=None, **kwargs):  # noqa: A002
        request = httpx.Request("POST", url)
        captured_posts.append({"url": url, "data": dict(data) if data is not None else None})
        if len(captured_posts) == 1:
            return httpx.Response(200, json={"id": "17891234567890123"}, request=request)
        return httpx.Response(200, json={"id": "17841405793187218"}, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    response = await adapter.publish(
        PublishContentRequest(
            account_external_id="17841405793187218",
            text="Hello Instagram",
            media_urls=["https://example.com/image.jpg"],
        )
    )
    assert response.external_post_id == "17841405793187218"
    assert response.platform == "instagram"
    assert response.permalink == "https://www.instagram.com/p/17841405793187218"
    assert len(captured_posts) == 2
    assert captured_posts[0]["url"].rstrip("/").endswith("/17841405793187218/media")
    assert "/media_publish" in captured_posts[1]["url"]


@pytest.mark.asyncio
async def test_fetch_metrics_parses_insights(monkeypatch):
    adapter = InstagramAdapter()

    async def fake_get(self, url, params=None, **kwargs):
        request = httpx.Request("GET", url)
        payload = {
            "data": [
                {"name": "impressions", "values": [{"value": 200}]},
                {"name": "engagement", "values": [{"value": 20}]},
            ]
        }
        return httpx.Response(200, json=payload, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    response = await adapter.fetch_metrics(
        MetricsRequest(account_external_id="17841405793187218", external_post_id="17841405793187218")
    )
    assert response.impressions == 200
    assert response.likes == 20


@pytest.mark.asyncio
async def test_delete_calls_graph_delete(monkeypatch):
    adapter = InstagramAdapter()

    async def fake_delete(self, url, data=None, **kwargs):
        request = httpx.Request("DELETE", url)
        return httpx.Response(200, json={"success": True}, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "delete", fake_delete)

    await adapter.delete(
        DeleteContentRequest(account_external_id="abc", external_post_id="123")
    )


@pytest.mark.asyncio
async def test_delete_raises_external_service_error(monkeypatch):
    adapter = InstagramAdapter()

    async def fake_delete(self, url, data=None, **kwargs):
        request = httpx.Request("DELETE", url)
        return httpx.Response(400, json={"error": {"message": "bad"}}, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "delete", fake_delete)

    from app.core.exceptions import ExternalServiceError

    with pytest.raises(ExternalServiceError, match="Instagram delete failed"):
        await adapter.delete(
            DeleteContentRequest(account_external_id="abc", external_post_id="123")
        )


@pytest.mark.asyncio
async def test_schedule_returns_synthetic_schedule_id():
    from datetime import datetime, timezone

    adapter = InstagramAdapter()
    response = await adapter.schedule(
        ScheduleContentRequest(
            account_external_id="abc",
            text="hello",
            scheduled_at=datetime.now(timezone.utc),
        )
    )
    assert response.external_schedule_id.startswith("ig-sched:")
    assert response.platform == "instagram"




# ---------------------------------------------------------------------------
# Instagram Login flow contract
# ---------------------------------------------------------------------------
# Added 2026-07-24. The adapter previously mixed Instagram Login's authorize URL with
# Facebook Login's scopes, host, and token grant type — a combination that fails at
# authorization. The whole suite passed before AND after that was corrected, because
# nothing asserted any of these values. These tests exist so a regression back to the
# Facebook Login flow fails loudly instead of silently.


def test_authorization_url_requests_instagram_login_scopes():
    """Facebook Login's unprefixed scope names were deprecated for this flow 2025-01-27."""
    url = InstagramAdapter().build_authorization_url(state="s")
    assert "instagram_business_basic" in url
    assert "instagram_business_content_publish" in url
    # The Facebook Login names must not appear, not even as a substring of the new ones:
    # 'instagram_basic' is not a substring of 'instagram_business_basic'.
    assert "instagram_basic" not in url
    assert "instagram_content_publish" not in url


def test_api_base_is_instagram_login_host_and_supported_version():
    """graph.facebook.com belongs to the Facebook Login flow, which needs a linked Page."""
    adapter = InstagramAdapter()
    assert adapter.api_base.startswith("https://graph.instagram.com/")
    assert "graph.facebook.com" not in adapter.api_base
    # Meta supports a Graph API version for roughly two years; v20.0 was past that.
    assert adapter.api_base.endswith(INSTAGRAM_GRAPH_VERSION)
    assert INSTAGRAM_GRAPH_VERSION != "v20.0"


def test_long_lived_token_endpoints_are_instagram_login():
    assert INSTAGRAM_LONG_TOKEN_URL == "https://graph.instagram.com/access_token"
    assert INSTAGRAM_REFRESH_TOKEN_URL == "https://graph.instagram.com/refresh_access_token"


@pytest.mark.asyncio
async def test_long_lived_exchange_uses_ig_exchange_token_grant():
    """Instagram Login uses ig_exchange_token + access_token, not fb_exchange_token."""
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json={"access_token": "long-lived-token"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        token = await InstagramAdapter()._exchange_for_long_lived_token(client, "short-token")

    assert token == "long-lived-token"
    assert seen["params"]["grant_type"] == "ig_exchange_token"
    assert seen["params"]["access_token"] == "short-token"
    assert "fb_exchange_token" not in seen["params"]
    assert seen["url"].startswith("https://graph.instagram.com/access_token")
