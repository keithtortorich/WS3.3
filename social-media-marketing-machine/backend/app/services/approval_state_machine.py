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

from app.core.exceptions import ForbiddenError, InvalidTransitionError
from app.models.approval import Approval
from app.models.audit_log import AuditLog
from app.models.enums import ApprovalStatus, AuditAction, PostStatus
from app.models.post import Post, allow_status_transition
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.audit_log_repository import AuditLogRepository

# Explicit transition table: current status -> set of legal next statuses.
# Mirrors ``smm.post_transition_rules`` in docs/sql/smm_gtm_bridge.sql §2d.
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

# Terminal states: no outgoing transitions at all. ARCHIVED is the only one —
# PUBLISHED is deliberately NOT terminal (a published post can still be
# archived), and this is asserted by a test rather than left to comment rot.
TERMINAL_STATUSES: frozenset[PostStatus] = frozenset(
    status for status, allowed in _ALLOWED_TRANSITIONS.items() if not allowed
)

# Fail loudly at import time if PostStatus grows a member nobody wired into
# the table — an unmapped status would otherwise silently behave as terminal.
_UNMAPPED = set(PostStatus) - set(_ALLOWED_TRANSITIONS)
if _UNMAPPED:  # pragma: no cover - guards against future enum drift
    raise RuntimeError(
        "PostStatus members missing from the approval transition table: "
        f"{sorted(s.name for s in _UNMAPPED)}"
    )


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

    @staticmethod
    def _assert_same_org(post: Post, organization_id: uuid.UUID) -> None:
        """Defense in depth against cross-tenant workflow actions.

        Routers already load the Post through ``OrgScopedRepository``, so a
        foreign Post normally 404s before reaching here. This check means a
        caller that obtained a Post some other way (worker, service, future
        endpoint) still cannot drive another org's approval workflow — and
        cannot mis-attribute the resulting Approval/AuditLog rows.
        """
        if post.organization_id != organization_id:
            raise ForbiddenError(
                f"Post {post.id} does not belong to organization {organization_id}."
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
        """Validate and apply a direct status transition, writing an audit log.

        Validation happens BEFORE any mutation, so a rejected transition
        leaves the Post row byte-for-byte unchanged. The audit write is not
        best-effort: it shares this method's session and therefore the
        caller's transaction, so the status change and its audit row commit
        together or not at all. An audit row that can be lost is not an audit.
        """
        self._assert_same_org(post, organization_id)
        self._assert_legal(post.status, target_status)
        previous_status = post.status

        # The only place in the codebase permitted to write Post.status —
        # see app/models/post.py's status guard.
        with allow_status_transition():
            post.status = target_status

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
        # Single flush after both writes: the status UPDATE and the AuditLog
        # INSERT reach the database as one unit of work.
        await self.session.flush()
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

        The implied transition is validated BEFORE the Approval row is
        created. Doing it the other way round (as the reference SQL in
        docs/sql/smm_gtm_bridge.sql §2b does) leaves an orphan Approval row
        recording a decision that was never actually applied.
        """
        self._assert_same_org(post, organization_id)

        target_status = self._target_status_for_decision(decision_status, stage)
        if target_status is not None:
            self._assert_legal(post.status, target_status)

        approval = Approval(
            organization_id=organization_id,
            post_id=post.id,
            reviewer_user_id=reviewer_user_id,
            stage=stage,
            status=decision_status,
            feedback=feedback,
        )
        await self.approval_repo.create(approval)

        if target_status is not None:
            await self.transition(
                post=post,
                organization_id=organization_id,
                target_status=target_status,
                actor_user_id=reviewer_user_id,
                reason=f"Approval decision '{decision_status.value}' at stage '{stage}'.",
            )

        return approval

    @staticmethod
    def _target_status_for_decision(
        decision_status: ApprovalStatus, stage: str
    ) -> Optional[PostStatus]:
        """Map a reviewer decision to the Post status it implies, or None
        when the decision records an opinion without advancing the workflow
        (PENDING, or an APPROVED decision at an unrecognized stage)."""
        if decision_status == ApprovalStatus.APPROVED:
            if stage == "internal":
                return PostStatus.CLIENT_REVIEW
            if stage == "client":
                return PostStatus.APPROVED
            return None
        if decision_status == ApprovalStatus.REJECTED:
            return PostStatus.REJECTED
        if decision_status == ApprovalStatus.CHANGES_REQUESTED:
            return PostStatus.DRAFT
        return None
