"""Strongly-typed request/response models shared by every AI provider.

Keeping these Pydantic models provider-agnostic is what makes the
:class:`app.ai.base.AIProvider` abstraction swappable: callers (the prompt
template engine, routers, etc.) only ever see these types, never a
provider-specific payload shape.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class TextGenerationRequest(BaseModel):
    prompt: str = Field(min_length=1)
    model: Optional[str] = None
    max_tokens: int = Field(default=512, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    system_prompt: Optional[str] = None


class TextGenerationResponse(BaseModel):
    text: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(min_length=1)
    model: Optional[str] = None
    width: int = Field(default=1024, ge=64, le=4096)
    height: int = Field(default=1024, ge=64, le=4096)
    n: int = Field(default=1, ge=1, le=4)


class ImageGenerationResponse(BaseModel):
    image_urls: list[str]
    model: str
    provider: str


class VideoPromptRequest(BaseModel):
    """Generates a structured *prompt* for a downstream video generation
    tool (this scaffold does not call a video-generation API directly)."""

    concept: str = Field(min_length=1)
    duration_seconds: int = Field(default=15, ge=1, le=180)
    style: Optional[str] = None


class VideoPromptResponse(BaseModel):
    prompt: str
    provider: str
    model: str


class SummarizeRequest(BaseModel):
    text: str = Field(min_length=1)
    max_length_words: int = Field(default=100, ge=10, le=2000)


class SummarizeResponse(BaseModel):
    summary: str
    provider: str
    model: str


class RewriteRequest(BaseModel):
    text: str = Field(min_length=1)
    instructions: str = Field(min_length=1)


class RewriteResponse(BaseModel):
    rewritten_text: str
    provider: str
    model: str


class ModerationRequest(BaseModel):
    text: str = Field(min_length=1)


class ModerationResponse(BaseModel):
    flagged: bool
    categories: list[str] = Field(default_factory=list)
    provider: str


class EmbeddingsRequest(BaseModel):
    input_text: str = Field(min_length=1)
    model: Optional[str] = None


class EmbeddingsResponse(BaseModel):
    embedding: list[float]
    provider: str
    model: str
    dimensions: int
