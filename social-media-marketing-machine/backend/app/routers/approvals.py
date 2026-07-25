"""Approvals router: reviewer decisions + explicit state machine transitions.

Delegates all status changes to ``app.services.approval_state_machine`` so
that version history, audit logs, and legal-transition checks (task #8)
are always enforced — this router never writes ``Post.status`` directly.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthContext, get_current_org, get_current_user
from app.core.db import get_db
from app.core.exceptions import NotFoundError
from app.models.approval import Approval
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.post_repository import PostRepository
from app.schemas.approval import ApprovalDecisionRequest, ApprovalRead, PostStateRead, TransitionRequest
from app.schemas.common import Page
from app.services.approval_state_machine import ApprovalStateMachine

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


@router.get("/posts/{post_id}", response_model=Page[ApprovalRead])
async def list_approvals_for_post(
    post_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Page[ApprovalRead]:
    """List all approval decisions recorded for a Post."""
    repo = ApprovalRepository(db)
    result = await repo.list_paginated(
        uuid.UUID(org_id), page=page, page_size=page_size, extra_filters=[Approval.post_id == post_id]
    )
    return Page[ApprovalRead](
        items=[ApprovalRead.model_validate(a) for a in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.post("/posts/{post_id}/decisions", response_model=ApprovalRead, status_code=status.HTTP_201_CREATED)
async def record_decision(
    post_id: uuid.UUID,
    payload: ApprovalDecisionRequest,
    auth: AuthContext = Depends(get_current_user),
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Approval:
    """Record a reviewer decision and let the state machine advance the
    Post's status accordingly (approve -> next stage, reject -> Rejected)."""
    post_repo = PostRepository(db)
    post = await post_repo.get_by_id(uuid.UUID(org_id), post_id)
    if post is None:
        raise NotFoundError(f"Post {post_id} not found.")

    machine = ApprovalStateMachine(db)
    reviewer_id = uuid.UUID(auth.user_id) if _is_uuid(auth.user_id) else None
    approval = await machine.record_decision(
        post=post,
        organization_id=uuid.UUID(org_id),
        reviewer_user_id=reviewer_id,
        stage=payload.stage,
        decision_status=payload.status,
        feedback=payload.feedback,
    )
    await db.commit()
    await db.refresh(approval)
    return approval


@router.post("/posts/{post_id}/transition", response_model=PostStateRead)
async def transition_post(
    post_id: uuid.UUID,
    payload: TransitionRequest,
    auth: AuthContext = Depends(get_current_user),
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> PostStateRead:
    """Explicitly transition a Post's status (e.g. submit for review)."""
    post_repo = PostRepository(db)
    post = await post_repo.get_by_id(uuid.UUID(org_id), post_id)
    if post is None:
        raise NotFoundError(f"Post {post_id} not found.")

    machine = ApprovalStateMachine(db)
    actor_id = uuid.UUID(auth.user_id) if _is_uuid(auth.user_id) else None
    post = await machine.transition(
        post=post,
        organization_id=uuid.UUID(org_id),
        target_status=payload.target_status,
        actor_user_id=actor_id,
        reason=payload.reason,
    )
    await db.commit()
    await db.refresh(post)
    return PostStateRead(post_id=post.id, status=post.status)


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False
