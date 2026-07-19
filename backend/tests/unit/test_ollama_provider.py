"""Unit tests for the Ollama AI provider adapter, with httpx mocked."""
from __future__ import annotations

import httpx
import pytest

from app.ai.providers.ollama import OllamaProvider
from app.ai.schemas import EmbeddingsRequest, TextGenerationRequest
from app.core.exceptions import ExternalServiceError


@pytest.mark.asyncio
async def test_generate_text_success(monkeypatch):
    provider = OllamaProvider()

    async def fake_post(self, url, json=None, **kwargs):
        assert url.endswith("/api/generate")
        assert json["model"] == provider.default_model
        assert json["stream"] is False
        request = httpx.Request("POST", url)
        return httpx.Response(200, json={"response": "Generated caption text."}, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    response = await provider.generate_text(TextGenerationRequest(prompt="Write a caption"))
    assert response.text == "Generated caption text."
    assert response.provider == "ollama"
    assert response.model == provider.default_model


@pytest.mark.asyncio
async def test_generate_text_connection_error(monkeypatch):
    provider = OllamaProvider()

    async def fake_post(self, url, json=None, **kwargs):
        raise httpx.ConnectError("connection refused", request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    with pytest.raises(ExternalServiceError, match="Could not connect to Ollama"):
        await provider.generate_text(TextGenerationRequest(prompt="Write a caption"))


@pytest.mark.asyncio
async def test_embeddings_success(monkeypatch):
    provider = OllamaProvider()

    async def fake_post(self, url, json=None, **kwargs):
        assert url.endswith("/api/embeddings")
        request = httpx.Request("POST", url)
        return httpx.Response(200, json={"embedding": [0.1, 0.2, 0.3]}, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    response = await provider.embeddings(EmbeddingsRequest(input_text="hello world"))
    assert response.dimensions == 3
    assert response.embedding == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_generate_image_not_implemented():
    provider = OllamaProvider()
    from app.ai.schemas import ImageGenerationRequest

    with pytest.raises(NotImplementedError, match="does not natively support image generation"):
        await provider.generate_image(ImageGenerationRequest(prompt="a cat"))


@pytest.mark.asyncio
async def test_moderate_flags_content(monkeypatch):
    provider = OllamaProvider()

    async def fake_post(self, url, json=None, **kwargs):
        request = httpx.Request("POST", url)
        return httpx.Response(200, json={"response": "FLAGGED\nhate, harassment"}, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    from app.ai.schemas import ModerationRequest

    result = await provider.moderate(ModerationRequest(text="something bad"))
    assert result.flagged is True
    assert "hate" in result.categories
