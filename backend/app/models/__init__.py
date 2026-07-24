"""SQLAlchemy 2.0 declarative models for the Social Media Marketing Machine.

Import order matters for Alembic autogenerate: every model module must be
imported here so that ``Base.metadata`` is fully populated before
``alembic/env.py`` (or any test fixture) calls ``Base.metadata.create_all``.
"""
from app.models.base import Base
from app.models.enums import (
    ApprovalStatus,
    AuditAction,
    CampaignStatus,
    ExecutionNodeRefType,
    MediaType,
    NotificationType,
    OrgRole,
    PlatformName,
    PostStatus,
    PublishJobStatus,
    TaskStatus,
    WorkflowNodeStatus,
    WorkflowNodeType,
)
from app.models.organization import Organization
from app.models.user import User, OrganizationMembership
from app.models.team import Team, TeamMembership
from app.models.client import Client
from app.models.brand import Brand
from app.models.campaign import Campaign
from app.models.post import Post
from app.models.post_version import PostVersion
from app.models.media import Media
from app.models.approval import Approval
from app.models.comment import Comment
from app.models.task import Task
from app.models.platform_account import PlatformAccount
from app.models.schedule import Schedule
from app.models.publish_job import PublishJob
from app.models.analytics import Analytics
from app.models.ai_request import AIRequest
from app.models.prompt_template import PromptTemplate
from app.models.agent_template import AgentTemplate
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.models.execution_node import ExecutionNode
from app.models.integration_mount import IntegrationMount

__all__ = [
    "Base",
    "ApprovalStatus",
    "AuditAction",
    "CampaignStatus",
    "ExecutionNodeRefType",
    "MediaType",
    "NotificationType",
    "OrgRole",
    "PlatformName",
    "PostStatus",
    "PublishJobStatus",
    "TaskStatus",
    "WorkflowNodeStatus",
    "WorkflowNodeType",
    "Organization",
    "User",
    "OrganizationMembership",
    "Team",
    "TeamMembership",
    "Client",
    "Brand",
    "Campaign",
    "Post",
    "PostVersion",
    "Media",
    "Approval",
    "Comment",
    "Task",
    "PlatformAccount",
    "Schedule",
    "PublishJob",
    "Analytics",
    "AIRequest",
    "PromptTemplate",
    "AgentTemplate",
    "AuditLog",
    "Notification",
    "ExecutionNode",
    "IntegrationMount",
]
