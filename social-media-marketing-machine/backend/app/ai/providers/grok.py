"""xAI Grok provider — typed stub. See app/ai/providers/_stub_base.py."""
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


class GrokProvider(AIProvider):
    """Stub for xAI Grok. Not implemented in this scaffold."""

    name = "grok"

    async def generate_text(self, request: TextGenerationRequest) -> TextGenerationResponse:
        raise not_implemented("Grok", "generate_text", "GROK_API_KEY")

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        raise not_implemented("Grok", "generate_image", "GROK_API_KEY")

    async def generate_video_prompt(self, request: VideoPromptRequest) -> VideoPromptResponse:
        raise not_implemented("Grok", "generate_video_prompt", "GROK_API_KEY")

    async def summarize(self, request: SummarizeRequest) -> SummarizeResponse:
        raise not_implemented("Grok", "summarize", "GROK_API_KEY")

    async def rewrite(self, request: RewriteRequest) -> RewriteResponse:
        raise not_implemented("Grok", "rewrite", "GROK_API_KEY")

    async def moderate(self, request: ModerationRequest) -> ModerationResponse:
        raise not_implemented("Grok", "moderate", "GROK_API_KEY")

    async def embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        raise not_implemented("Grok", "embeddings", "GROK_API_KEY")
