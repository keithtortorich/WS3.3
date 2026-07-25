"""OpenAI provider — typed stub. See app/ai/providers/_stub_base.py."""
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


class OpenAIProvider(AIProvider):
    """Stub for OpenAI (GPT-4/GPT-4o/DALL-E). Not implemented in this scaffold."""

    name = "openai"

    async def generate_text(self, request: TextGenerationRequest) -> TextGenerationResponse:
        raise not_implemented("OpenAI", "generate_text", "OPENAI_API_KEY")

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        raise not_implemented("OpenAI", "generate_image", "OPENAI_API_KEY")

    async def generate_video_prompt(self, request: VideoPromptRequest) -> VideoPromptResponse:
        raise not_implemented("OpenAI", "generate_video_prompt", "OPENAI_API_KEY")

    async def summarize(self, request: SummarizeRequest) -> SummarizeResponse:
        raise not_implemented("OpenAI", "summarize", "OPENAI_API_KEY")

    async def rewrite(self, request: RewriteRequest) -> RewriteResponse:
        raise not_implemented("OpenAI", "rewrite", "OPENAI_API_KEY")

    async def moderate(self, request: ModerationRequest) -> ModerationResponse:
        raise not_implemented("OpenAI", "moderate", "OPENAI_API_KEY")

    async def embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        raise not_implemented("OpenAI", "embeddings", "OPENAI_API_KEY")
