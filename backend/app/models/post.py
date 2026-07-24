"""Post: a single piece of social content moving through the approval
state machine (task #8) toward publication."""
from __future__ import annotations

import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Iterator, List

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.db_types import GUID, StringArrayCompat
from app.core.exceptions import InvalidTransitionError
from app.models.base import Base, OrgScopedMixin, TimestampMixin, UUIDPkMixin
from app.models.enums import PostStatus

# ---------------------------------------------------------------------------
# Status-write guard
# ---------------------------------------------------------------------------
# Architecture invariant #3: ``post.status`` changes ONLY through
# ``app/services/approval_state_machine.py``. A docstring saying so is not an
# enforcement mechanism — a future router/worker/task can still write
# ``post.status = ...`` and silently bypass transition validation, audit
# logging, and the whole approval workflow.
#
# This ContextVar + ``@validates`` hook makes the bypass *impossible* rather
# than merely discouraged: reassigning ``status`` on an already-persisted Post
# raises unless the write happens inside ``allow_status_transition()``, which
# only the state machine enters. Assigning a status at construction time (on a
# transient object, before it is flushed) is still allowed — that is creation,
# not a transition.
_STATUS_TRANSITION_ALLOWED: ContextVar[bool] = ContextVar(
    "post_status_transition_allowed", default=False
)


@contextmanager
def allow_status_transition() -> Iterator[None]:
    """Permit a ``Post.status`` write for the duration of the block.

    Intended for exclusive use by
    :class:`app.services.approval_state_machine.ApprovalStateMachine`.
    """
    token = _STATUS_TRANSITION_ALLOWED.set(True)
    try:
        yield
    finally:
        _STATUS_TRANSITION_ALLOWED.reset(token)

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.user import User
    from app.models.post_version import PostVersion
    from app.models.media import Media
    from app.models.approval import Approval
    from app.models.comment import Comment
    from app.models.schedule import Schedule
    from app.models.publish_job import PublishJob


class Post(UUIDPkMixin, OrgScopedMixin, TimestampMixin, Base):
    """A social media post. ``platform`` denotes the target platform;
    ``status`` mirrors :class:`app.models.enums.PostStatus` and is
    transitioned exclusively via ``app.services.approval_state_machine``.
    """

    __tablename__ = "posts"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    post_type: Mapped[str] = mapped_column(String(50), nullable=False, default="standard")
    caption: Mapped[str] = mapped_column(Text, nullable=False, default="")
    hashtags: Mapped[list | None] = mapped_column(StringArrayCompat)
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus, name="post_status"), nullable=False, default=PostStatus.DRAFT, index=True
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="posts")
    created_by: Mapped["User | None"] = relationship()
    versions: Mapped[List["PostVersion"]] = relationship(
        back_populates="post", cascade="all, delete-orphan", order_by="PostVersion.version_number"
    )
    media_items: Mapped[List["Media"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    approvals: Mapped[List["Approval"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    comments: Mapped[List["Comment"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    publish_jobs: Mapped[List["PublishJob"]] = relationship(back_populates="post", cascade="all, delete-orphan")

    @validates("status")
    def _guard_status_write(self, key: str, value: PostStatus) -> PostStatus:
        """Reject direct ``post.status`` writes outside the state machine.

        Fires only on Python-side attribute assignment — loading a row from
        the database does not go through ``@validates``, so this costs
        nothing on reads and cannot interfere with ``session.refresh()``.
        """
        if _STATUS_TRANSITION_ALLOWED.get():
            return value
        state = sa_inspect(self)
        if state.persistent or state.detached:
            raise InvalidTransitionError(
                "Post.status cannot be assigned directly. All status changes must go "
                "through app.services.approval_state_machine.ApprovalStateMachine so "
                "that transition validation and audit logging are never bypassed."
            )
        # Transient/pending object: this is creation, not a transition.
        return value

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Post id={self.id} platform={self.platform} status={self.status}>"
