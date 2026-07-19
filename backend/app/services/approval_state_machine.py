"""Explicit approval workflow state machine.

States (mirrors ``app.models.enums.PostStatus``):
    Draft -> Internal Review -> Client Review -> Approved -> Scheduled -> Published -> Archived
    (Internal Review | Client Review) -> Rejected -> Draft (revise and resubmit)

Every transition:
  1. Is validated against the explicit ``_ALLOWED_TRANSITIONS`` table —
     illegal transitions raise :class:`InvalidTransitionError` rather than
     silently mutating state.
  2. Writes an :class:`AuditLog` row (who/when/what changed).
  3. For decision-driven transitions (record_decision), also writes an
     :class:`Approval` row.

Version history (``PostVersion``) is written on CONTENT changes (see
``app/routers/posts.py``), not on status transitions — a status change
alone doesn't alter the caption/hashtags, so no new version snapshot is
needed there.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidTransitionError
from app.models.approval import Approval
from app.models.audit_log import AuditLog
from app.models.enums import ApprovalStatus, AuditAction, PostStatus
from app.models.post import Post
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.audit_log_repository import AuditLogRepository

# Explicit transition table: current status -> set of legal next statuses.
_ALLOWED_TRANSITIONS: dict[PostStatus, set[PostStatus]] = {
    PostStatus.DRAFT: {PostStatus.INTERNAL_REVIEW, PostStatus.ARCHIVED},
    PostStatus.INTERNAL_REVIEW: {PostStatus.CLIENT_REVIEW, PostStatus.REJECTED, PostStatus.DRAFT},
    PostStatus.CLIENT_REVIEW: {PostStatus.APPROVED, PostStatus.REJECTED, PostStatus.DRAFT},
    PostStatus.APPROVED: {PostStatus.SCHEDULED, PostStatus.ARCHIVED},
    PostStatus.REJECTED: {PostStatus.DRAFT, PostStatus.ARCHIVED},
    PostStatus.SCHEDULED: {PostStatus.PUBLISHED, PostStatus.DRAFT, PostStatus.ARCHIVED},
    PostStatus.PUBLISHED: {PostStatus.ARCHIVED},
    PostStatus.ARCHIVED: set(),
}


class ApprovalStateMachine:
    """Encapsulates all legal Post status transitions plus their side effects
    (audit logging, approval recording). Routers must go through this class
    rather than setting ``post.status`` directly.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit_repo = AuditLogRepository(session)
        self.approval_repo = ApprovalRepository(session)

    def _assert_legal(self, current: PostStatus, target: PostStatus) -> None:
        allowed = _ALLOWED_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidTransitionError(
                f"Cannot transition Post from '{current.value}' to '{target.value}'. "
                f"Allowed transitions from '{current.value}': "
                f"{sorted(s.value for s in allowed) or 'none (terminal state)'}."
            )

    async def transition(
        self,
        *,
        post: Post,
        organization_id: uuid.UUID,
        target_status: PostStatus,
        actor_user_id: Optional[uuid.UUID],
        reason: Optional[str] = None,
    ) -> Post:
        """Validate and apply a direct status transition, writing an audit log."""
        self._assert_legal(post.status, target_status)
        previous_status = post.status
        post.status = target_status
        await self.session.flush()

        await self.audit_repo.create(
            AuditLog(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action=AuditAction.STATE_TRANSITION,
                entity_type="Post",
                entity_id=post.id,
                description=(
                    f"Post transitioned from {previous_status.value} to {target_status.value}"
                    + (f": {reason}" if reason else "")
                ),
                metadata_json={"from": previous_status.value, "to": target_status.value, "reason": reason},
            )
        )
        return post

    async def record_decision(
        self,
        *,
        post: Post,
        organization_id: uuid.UUID,
        reviewer_user_id: Optional[uuid.UUID],
        stage: str,
        decision_status: ApprovalStatus,
        feedback: Optional[str] = None,
    ) -> Approval:
        """Record a reviewer decision (Approval row) and, if the decision is
        conclusive, advance the Post's status accordingly:
          - APPROVED at 'internal' stage -> Post moves to CLIENT_REVIEW
          - APPROVED at 'client' stage   -> Post moves to APPROVED
          - REJECTED (any stage)         -> Post moves to REJECTED
          - CHANGES_REQUESTED            -> Post moves back to DRAFT
          - PENDING                      -> no Post transition (decision recorded only)
        """
        approval = Approval(
            organization_id=organization_id,
            post_id=post.id,
            reviewer_user_id=reviewer_user_id,
            stage=stage,
            status=decision_status,
            feedback=feedback,
        )
        await self.approval_repo.create(approval)

        target_status: Optional[PostStatus] = None
        if decision_status == ApprovalStatus.APPROVED:
            if stage == "internal":
                target_status = PostStatus.CLIENT_REVIEW
            elif stage == "client":
                target_status = PostStatus.APPROVED
        elif decision_status == ApprovalStatus.REJECTED:
            target_status = PostStatus.REJECTED
        elif decision_status == ApprovalStatus.CHANGES_REQUESTED:
            target_status = PostStatus.DRAFT

        if target_status is not None:
            await self.transition(
                post=post,
                organization_id=organization_id,
                target_status=target_status,
                actor_user_id=reviewer_user_id,
                reason=f"Approval decision '{decision_status.value}' at stage '{stage}'.",
            )

        return approval
