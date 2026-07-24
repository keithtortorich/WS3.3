"""Python enums mapped to SQLAlchemy ``Enum`` columns.

Centralizing status/role vocabularies here (rather than scattering string
literals through the codebase) gives us a single source of truth that both
the ORM layer and the approval state machine (task #8) import from.
"""
from __future__ import annotations

import enum


class OrgRole(str, enum.Enum):
    """Role of a user within an organization (agency). Used for RBAC."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    CLIENT_VIEWER = "client_viewer"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class PostStatus(str, enum.Enum):
    """Mirrors the approval state machine states (task #8) 1:1."""

    DRAFT = "draft"
    INTERNAL_REVIEW = "internal_review"
    CLIENT_REVIEW = "client_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class MediaType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"
    DOCUMENT = "document"


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


class PlatformName(str, enum.Enum):
    """Supported (or stubbed) social platforms.

    LinkedIn is fully implemented (task #6); all others are typed stubs
    that raise ``NotImplementedError`` from their adapter methods.
    """

    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    X = "x"
    THREADS = "threads"
    TIKTOK = "tiktok"
    PINTEREST = "pinterest"
    YOUTUBE = "youtube"
    GOOGLE_BUSINESS = "google_business"


class PublishJobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    STATE_TRANSITION = "state_transition"
    LOGIN = "login"
    PUBLISH = "publish"
    OTHER = "other"


class NotificationType(str, enum.Enum):
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_RECEIVED = "approval_received"
    POST_PUBLISHED = "post_published"
    POST_FAILED = "post_failed"
    COMMENT_ADDED = "comment_added"
    TASK_ASSIGNED = "task_assigned"
    SYSTEM = "system"


class WorkflowNodeType(str, enum.Enum):
    """Canonical execution node kinds.

    Mirrors the SQL ``execution_nodes.node_type`` constraint so Python-side
    checks can validate before persisting workflow graph nodes.
    """

    INTAKE = "intake"
    CAMPAIGN = "campaign"
    POST = "post"
    PUBLISH_JOB = "publish_job"
    APPROVAL = "approval"
    INTEGRATION_EVENT = "integration_event"


class WorkflowNodeStatus(str, enum.Enum):
    """Status vocabulary for ``execution_nodes``.

    Mirrors the SQL ``execution_nodes.status`` constraint.
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionNodeRefType(str, enum.Enum):
    """Domain entity types that an execution node can reference."""

    CAMPAIGN = "campaign"
    POST = "post"
    SCHEDULE = "schedule"
    PUBLISH_JOB = "publish_job"
    APPROVAL = "approval"
    AUDIT_LOG = "audit_log"
