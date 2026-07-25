"""Pydantic schemas for approvals + state machine transitions (task #8)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ApprovalStatus, PostStatus


class ApprovalDecisionRequest(BaseModel):
    """Body for POST /approvals/{post_id}/decisions — records a reviewer
    decision and (if appropriate) advances the Post's state machine."""

    stage: str = Field(default="internal", max_length=50)
    status: ApprovalStatus
    feedback: Optional[str] = Field(default=None, max_length=4000)


class ApprovalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    post_id: uuid.UUID
    reviewer_user_id: Optional[uuid.UUID]
    stage: str
    status: ApprovalStatus
    feedback: Optional[str]
    created_at: datetime


class TransitionRequest(BaseModel):
    """Body for POST /approvals/{post_id}/transition — explicit state
    machine transition not tied to a reviewer decision (e.g. submit for
    review, schedule, archive)."""

    target_status: PostStatus
    reason: Optional[str] = Field(default=None, max_length=1000)


class PostStateRead(BaseModel):
    post_id: uuid.UUID
    status: PostStatus
