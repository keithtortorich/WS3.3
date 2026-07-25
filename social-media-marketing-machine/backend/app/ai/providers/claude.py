"""Anthropic Claude provider — typed stub. See app/ai/providers/_stub_base.py."""
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


class ClaudeProvider(AIProvider):
    """Stub for Anthropic Claude. Not implemented in this scaffold."""

    name = "claude"

    async def generate_text(self, request: TextGenerationRequest) -> TextGenerationResponse:
        raise not_implemented("Claude", "generate_text", "CLAUDE_API_KEY")

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        raise not_implemented("Claude", "generate_image", "CLAUDE_API_KEY")

    async def generate_video_prompt(self, request: VideoPromptRequest) -> VideoPromptResponse:
        raise not_implemented("Claude", "generate_video_prompt", "CLAUDE_API_KEY")

    async def summarize(self, request: SummarizeRequest) -> SummarizeResponse:
        raise not_implemented("Claude", "summarize", "CLAUDE_API_KEY")

    async def rewrite(self, request: RewriteRequest) -> RewriteResponse:
        raise not_implemented("Claude", "rewrite", "CLAUDE_API_KEY")

    async def moderate(self, request: ModerationRequest) -> ModerationResponse:
        raise not_implemented("Claude", "moderate", "CLAUDE_API_KEY")

    async def embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        raise not_implemented("Claude", "embeddings", "CLAUDE_API_KEY")
