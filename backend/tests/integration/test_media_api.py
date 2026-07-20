"""Integration tests for the media router.

Covers:
- Presigned upload URL generation via ``POST /api/v1/media/upload-url``.
- ``/confirm`` flow persisting a ``Media`` row to SQLite.
- Existing register/list endpoint still works.
"""
from __future__ import annotations

import http
import uuid
from unittest.mock import patch

import pytest

from app.models.media import Media
from app.models.post import Post
from app.schemas.media import MediaCreate


VALID_MEDIA_CREATE = {
    "post_id": None,
    "media_type": "image",
    "storage_key": "invoices/abc123-cover.jpeg",
    "url": "http://localhost:9000/smm-media/invoices/abc123-cover.jpeg",
    "mime_type": "image/jpeg",
    "size_bytes": 1024,
    "width": 1200,
    "height": 800,
    "alt_text": "Cover art",
    "ai_generated": False,
}


def _make_fake_s3_client():
    """Return a fake boto3 client that always issues a deterministic presigned URL."""

    class _FakeS3:
        def __init__(self):
            self.bucket_name = None

        def generate_presigned_url(self, *args, **kwargs):
            params = kwargs.get("Params", args[1] if len(args) > 1 else {})
            self.bucket_name = params.get("Bucket", "")
            key = params.get("Key", "")
            return f"http://fake-minio:9000/presigned/{key}"

    return _FakeS3()


@pytest.mark.asyncio
async def test_generate_upload_url_returns_presigned_link(client):
    from app.routers import media as media_router

    fake = _make_fake_s3_client()
    with patch.object(media_router, "_get_s3_client", return_value=fake, create=True):
        response = await client.post(
            "/api/v1/media/upload-url",
            params={
                "filename": "hero.png",
                "content_type": "image/png",
            },
        )

    assert response.status_code == http.HTTPStatus.OK, response.text
    body = response.json()
    assert "/" in body["storage_key"]
    assert body["upload_url"] == f"http://fake-minio:9000/presigned/{body['storage_key']}"
    assert body["public_url"].endswith(body["storage_key"])
    assert body["content_type"] == "image/png"
    assert isinstance(body["expires_in"], int)
    assert body["expires_in"] == 900


@pytest.mark.asyncio
async def test_confirm_upload_persists_media_row(client, db_session):
    from tests.conftest import TEST_ORG_ID

    storage_key = f"{TEST_ORG_ID}/{uuid.uuid4().hex}-avatar.png"
    payload = {
        **VALID_MEDIA_CREATE,
        "storage_key": storage_key,
        "url": f"http://localhost:9000/smm-media/{storage_key}",
    }

    response = await client.post("/api/v1/media/confirm", json=payload)
    assert response.status_code == http.HTTPStatus.CREATED, response.text
    created = response.json()
    assert created["media_type"] == "image"
    assert created["url"] == payload["url"]
    assert "id" in created
    assert "created_at" in created
    assert created["id"] not in (None, "")

    # Re-fetch via list to ensure it is durable.
    list_response = await client.get("/api/v1/media")
    assert list_response.status_code == http.HTTPStatus.OK
    page = list_response.json()
    assert page["total"] == 1
    assert page["items"][0]["url"] == payload["url"]


@pytest.mark.asyncio
async def test_register_media_still_works(client, db_session):
    storage_key = f"{uuid.uuid4()}/legacy.jpg"
    url = f"http://localhost:9000/smm-media/{storage_key}"
    payload = {
        **VALID_MEDIA_CREATE,
        "storage_key": storage_key,
        "url": url,
    }

    response = await client.post("/api/v1/media", json=payload)
    assert response.status_code == http.HTTPStatus.CREATED, response.text
    body = response.json()
    assert body["url"] == url


@pytest.mark.asyncio
async def test_list_media_pagination(client, db_session):
    from tests.conftest import TEST_ORG_ID

    for i in range(3):
        storage_key = f"{TEST_ORG_ID}/item-{i}.png"
        payload = {
            **VALID_MEDIA_CREATE,
            "storage_key": storage_key,
            "url": f"http://localhost:9000/smm-media/{storage_key}",
        }
        resp = await client.post("/api/v1/media", json=payload)
        assert resp.status_code == http.HTTPStatus.CREATED

    response = await client.get("/api/v1/media?page=1&page_size=2")
    assert response.status_code == http.HTTPStatus.OK
    page = response.json()
    assert page["total"] == 3
    assert page["page_size"] == 2
    assert len(page["items"]) == 2
    assert page["total_pages"] == 2
