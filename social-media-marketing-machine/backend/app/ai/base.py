"""Abstract base for pluggable AI providers.

Every capability the platform needs from an LLM/image provider is defined
here as an abstract async method with strongly-typed Pydantic request/
response models (``app/ai/schemas.py``). Concrete providers
(``app/ai/providers/*.py``) implement this interface; callers depend only
on :class:`AIProvider`, never on a concrete provider class, so swapping
``AI_PROVIDER=ollama`` for ``AI_PROVIDER=openai`` in ``.env`` is a
zero-code-change operation (see ``app/ai/factory.py``).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

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


class AIProvider(ABC):
    """Abstract interface every AI provider adapter must implement."""

    name: str

    @abstractmethod
    async def generate_text(self, request: TextGenerationRequest) -> TextGenerationResponse:
        """Generate freeform text (e.g. a social post caption) from a prompt."""

    @abstractmethod
    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        """Generate one or more images from a text prompt."""

    @abstractmethod
    async def generate_video_prompt(self, request: VideoPromptRequest) -> VideoPromptResponse:
        """Generate a structured prompt suitable for a downstream video
        generation tool (this layer does not render video itself)."""

    @abstractmethod
    async def summarize(self, request: SummarizeRequest) -> SummarizeResponse:
        """Summarize a longer piece of text."""

    @abstractmethod
    async def rewrite(self, request: RewriteRequest) -> RewriteResponse:
        """Rewrite text per free-form instructions (tone shift, shorten, etc.)."""

    @abstractmethod
    async def moderate(self, request: ModerationRequest) -> ModerationResponse:
        """Classify text for policy-violating content before it's scheduled."""

    @abstractmethod
    async def embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        """Compute a vector embedding for the given input text."""
