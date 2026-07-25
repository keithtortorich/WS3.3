"""Unit tests for the LinkedIn social platform adapter, with httpx mocked."""
from __future__ import annotations

import httpx
import pytest

from app.social.platforms.linkedin import LinkedInAdapter, MAX_IMAGE_BYTES
from app.social.schemas import (
    DeleteContentRequest,
    MediaValidationRequest,
    MetricsRequest,
    PublishContentRequest,
)


def test_build_authorization_url_contains_required_params():
    adapter = LinkedInAdapter()
    url = adapter.build_authorization_url(state="abc123")
    assert "response_type=code" in url
    assert "state=abc123" in url
    assert "client_id=" in url
    assert url.startswith("https://www.linkedin.com/oauth/v2/authorization")


def test_validate_media_accepts_valid_jpeg():
    adapter = LinkedInAdapter()
    result = adapter.validate_media(
        MediaValidationRequest(mime_type="image/jpeg", size_bytes=1_000_000)
    )
    assert result.is_valid is True
    assert result.errors == []


def test_validate_media_rejects_oversized_image():
    adapter = LinkedInAdapter()
    result = adapter.validate_media(
        MediaValidationRequest(mime_type="image/png", size_bytes=MAX_IMAGE_BYTES + 1)
    )
    assert result.is_valid is False
    assert "exceeds LinkedIn's" in result.errors[0]


def test_validate_media_rejects_unsupported_mime_type():
    adapter = LinkedInAdapter()
    result = adapter.validate_media(
        MediaValidationRequest(mime_type="image/bmp", size_bytes=1000)
    )
    assert result.is_valid is False
    assert "Unsupported mime type" in result.errors[0]


@pytest.mark.asyncio
async def test_publish_constructs_ugc_post_and_returns_id(monkeypatch):
    adapter = LinkedInAdapter()

    async def fake_post(self, url, json=None, **kwargs):
        assert url.endswith("/ugcPosts")
        assert json["lifecycleState"] == "PUBLISHED"
        assert json["specificContent"]["com.linkedin.ugc.ShareContent"]["shareCommentary"]["text"] == "Hello LinkedIn"
        request = httpx.Request("POST", url)
        return httpx.Response(
            201,
            json={},
            headers={"x-restli-id": "urn:li:share:12345"},
            request=request,
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    response = await adapter.publish(
        PublishContentRequest(account_external_id="abc", text="Hello LinkedIn")
    )
    assert response.external_post_id == "urn:li:share:12345"
    assert response.platform == "linkedin"
    assert "urn:li:share:12345" in response.permalink


@pytest.mark.asyncio
async def test_fetch_metrics_parses_share_statistics(monkeypatch):
    adapter = LinkedInAdapter()

    async def fake_get(self, url, params=None, **kwargs):
        assert url.endswith("/organizationalEntityShareStatistics")
        request = httpx.Request("GET", url)
        payload = {
            "elements": [
                {
                    "totalShareStatistics": {
                        "impressionCount": 100,
                        "likeCount": 10,
                        "commentCount": 2,
                        "shareCount": 1,
                        "clickCount": 5,
                    }
                }
            ]
        }
        return httpx.Response(200, json=payload, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    response = await adapter.fetch_metrics(
        MetricsRequest(account_external_id="urn:li:organization:1", external_post_id="urn:li:share:12345")
    )
    assert response.impressions == 100
    assert response.likes == 10


@pytest.mark.asyncio
async def test_schedule_raises_not_implemented():
    adapter = LinkedInAdapter()
    from app.social.schemas import ScheduleContentRequest
    from datetime import datetime, timezone

    with pytest.raises(NotImplementedError, match="no native 'schedule for later'"):
        await adapter.schedule(
            ScheduleContentRequest(
                account_external_id="abc",
                text="hi",
                scheduled_at=datetime.now(timezone.utc),
            )
        )
