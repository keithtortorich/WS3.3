"""Hermes (Nous Research) provider — typed stub. See app/ai/providers/_stub_base.py."""
from __future__ import annotations

from app.ai.base import AIProvider
from app.ai.providers._stub_base import not_implemented
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


class HermesProvider(AIProvider):
    """Stub for Hermes (Nous Research). Not implemented in this scaffold."""

    name = "hermes"

    async def generate_text(self, request: TextGenerationRequest) -> TextGenerationResponse:
        raise not_implemented("Hermes", "generate_text", "HERMES_API_KEY")

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        raise not_implemented("Hermes", "generate_image", "HERMES_API_KEY")

    async def generate_video_prompt(self, request: VideoPromptRequest) -> VideoPromptResponse:
        raise not_implemented("Hermes", "generate_video_prompt", "HERMES_API_KEY")

    async def summarize(self, request: SummarizeRequest) -> SummarizeResponse:
        raise not_implemented("Hermes", "summarize", "HERMES_API_KEY")

    async def rewrite(self, request: RewriteRequest) -> RewriteResponse:
        raise not_implemented("Hermes", "rewrite", "HERMES_API_KEY")

    async def moderate(self, request: ModerationRequest) -> ModerationResponse:
        raise not_implemented("Hermes", "moderate", "HERMES_API_KEY")

    async def embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        raise not_implemented("Hermes", "embeddings", "HERMES_API_KEY")
