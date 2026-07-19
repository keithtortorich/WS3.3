"""Strongly-typed request/response models shared by every social platform adapter."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PublishContentRequest(BaseModel):
    account_external_id: str
    text: str
    media_urls: list[str] = Field(default_factory=list)
    link_url: Optional[str] = None


class PublishContentResponse(BaseModel):
    external_post_id: str
    platform: str
    published_at: datetime
    permalink: Optional[str] = None


class ScheduleContentRequest(PublishContentRequest):
    scheduled_at: datetime


class ScheduleContentResponse(BaseModel):
    external_schedule_id: str
    platform: str
    scheduled_at: datetime


class DeleteContentRequest(BaseModel):
    account_external_id: str
    external_post_id: str


class UpdateContentRequest(BaseModel):
    account_external_id: str
    external_post_id: str
    text: str


class MetricsRequest(BaseModel):
    account_external_id: str
    external_post_id: str


class MetricsResponse(BaseModel):
    external_post_id: str
    platform: str
    impressions: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    clicks: int = 0
    raw_payload: dict = Field(default_factory=dict)


class MediaValidationRequest(BaseModel):
    mime_type: str
    size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None


class MediaValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = Field(default_factory=list)


class OAuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_in_seconds: Optional[int] = None
    scope: Optional[str] = None
    raw_payload: dict = Field(default_factory=dict)
