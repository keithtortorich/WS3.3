"""Ollama provider — the fully-implemented reference AI adapter.

WHY OLLAMA IS THE REFERENCE IMPLEMENTATION:
Every other supported provider (OpenAI, Claude, Gemini, Grok, Hermes)
requires a paid API key and outbound internet access to a third-party
vendor, which makes them a poor fit for a scaffold meant to be cloned and
run locally/in CI without secrets. Ollama runs entirely on the developer's
machine (or a `ollama` container in docker-compose), requires no API key,
and exposes a simple, stable, well-documented local REST API — so it's the
adapter we can fully implement, exercise in unit tests (with mocked
httpx), and use to prove the AIProvider abstraction actually works
end-to-end. Swapping in a real hosted provider later is a matter of
implementing the same interface in `openai.py` / `claude.py` / etc.
"""
from __future__ import annotations

import time

import httpx

from app.ai.base import AIProvider
from app.ai.schemas import (
    EmbeddingsRequest,
    EmbeddingsResponse,
    ImageGenerationRequest,
    ImageGenerationResponse,
    ModerationRequest,
    ModerationResponse,
    RewriteRequest,
    RewriteResponse,
    SummarizeRequest,
    SummarizeResponse,
    TextGenerationRequest,
    TextGenerationResponse,
    VideoPromptRequest,
    VideoPromptResponse,
)
from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError


class OllamaProvider(AIProvider):
    """Talks to a local (or containerized) Ollama server's REST API.

    Endpoints used (documented Ollama API shapes):
      - POST {base_url}/api/generate  {model, prompt, stream, system?}
      - POST {base_url}/api/embeddings {model, prompt}
    """

    name = "ollama"

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.default_model = settings.OLLAMA_DEFAULT_MODEL
        self.timeout_seconds = settings.OLLAMA_TIMEOUT_SECONDS

    async def _generate_raw(self, prompt: str, model: str, system: str | None = None) -> tuple[str, int]:
        """Call POST /api/generate with stream=False and return (text, latency_ms)."""
        payload: dict = {"model": model, "prompt": prompt, "stream": False}
        if system:
            payload["system"] = system

        started = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.ConnectError as exc:
            raise ExternalServiceError(
                f"Could not connect to Ollama at {self.base_url}. Is `ollama serve` running? "
                f"(Set OLLAMA_BASE_URL in .env if it's running elsewhere.)"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise ExternalServiceError(f"Ollama returned an error: {exc.response.text}") from exc
        except httpx.TimeoutException as exc:
            raise ExternalServiceError(
                f"Ollama request timed out after {self.timeout_seconds}s."
            ) from exc

        latency_ms = int((time.monotonic() - started) * 1000)
        return data.get("response", ""), latency_ms

    async def generate_text(self, request: TextGenerationRequest) -> TextGenerationResponse:
        model = request.model or self.default_model
        text, latency_ms = await self._generate_raw(request.prompt, model, request.system_prompt)
        return TextGenerationResponse(
            text=text.strip(),
            model=model,
            provider=self.name,
            tokens_used=None,  # Ollama's /api/generate response includes eval_count; omitted here for simplicity.
            latency_ms=latency_ms,
        )

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        raise NotImplementedError(
            "Ollama does not natively support image generation via its REST API. "
            "Configure AI_PROVIDER=openai (DALL-E) or another image-capable provider "
            "and implement OpenAIProvider.generate_image for this capability."
        )

    async def generate_video_prompt(self, request: VideoPromptRequest) -> VideoPromptResponse:
        model = request.model if hasattr(request, "model") else self.default_model
        prompt = (
            f"Write a detailed, shot-by-shot video generation prompt for a "
            f"{request.duration_seconds}-second video. Concept: {request.concept}. "
            f"Style: {request.style or 'modern, high-energy social media style'}. "
            f"Describe camera movement, pacing, and mood."
        )
        text, _ = await self._generate_raw(prompt, self.default_model)
        return VideoPromptResponse(prompt=text.strip(), provider=self.name, model=self.default_model)

    async def summarize(self, request: SummarizeRequest) -> SummarizeResponse:
        prompt = (
            f"Summarize the following text in no more than {request.max_length_words} words. "
            f"Be concise and preserve key facts:\n\n{request.text}"
        )
        text, _ = await self._generate_raw(prompt, self.default_model)
        return SummarizeResponse(summary=text.strip(), provider=self.name, model=self.default_model)

    async def rewrite(self, request: RewriteRequest) -> RewriteResponse:
        prompt = f"Rewrite the following text according to these instructions: {request.instructions}\n\nText:\n{request.text}"
        text, _ = await self._generate_raw(prompt, self.default_model)
        return RewriteResponse(rewritten_text=text.strip(), provider=self.name, model=self.default_model)

    async def moderate(self, request: ModerationRequest) -> ModerationResponse:
        """Ollama has no dedicated moderation endpoint; we approximate it by
        prompting the model to flag policy-violating content. This is a
        best-effort heuristic, NOT a production-grade moderation system —
        for production use, a dedicated moderation API/model is recommended.
        """
        prompt = (
            "You are a content moderation classifier. Respond with exactly "
            "'FLAGGED' or 'CLEAN' on the first line, followed by a comma-separated "
            "list of violated categories (hate, violence, sexual, harassment, "
            "self-harm, spam) if flagged, or 'none' if clean.\n\nText to review:\n"
            f"{request.text}"
        )
        text, _ = await self._generate_raw(prompt, self.default_model)
        lines = text.strip().splitlines()
        flagged = bool(lines) and lines[0].strip().upper().startswith("FLAGGED")
        categories: list[str] = []
        if flagged and len(lines) > 1:
            categories = [c.strip() for c in lines[1].split(",") if c.strip() and c.strip().lower() != "none"]
        return ModerationResponse(flagged=flagged, categories=categories, provider=self.name)

    async def embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        model = request.model or self.default_model
        payload = {"model": model, "prompt": request.input_text}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(f"{self.base_url}/api/embeddings", json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.ConnectError as exc:
            raise ExternalServiceError(
                f"Could not connect to Ollama at {self.base_url} for embeddings."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise ExternalServiceError(f"Ollama returned an error: {exc.response.text}") from exc

        embedding = data.get("embedding", [])
        return EmbeddingsResponse(
            embedding=embedding, provider=self.name, model=model, dimensions=len(embedding)
        )
