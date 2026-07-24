"""IntegrationService: ingest campaign intent from an external system (WS3.3).

This is the SMM side of the bridge described in INTEGRATION_PLAN.md. WS3.3
owns intake and holds the customer relationship; SMM owns creative and
platform execution. A single inbound "intent" therefore has to materialize a
complete, reviewable slice of SMM's domain model:

    Campaign
      └── Post (one per requested platform)
            ├── PostVersion  (v1 — immutable content snapshot)
            └── Approval     (PENDING — the review checkpoint)

plus an execution graph in ``execution_nodes`` mirroring that structure, so a
cold start can reconstruct exactly where an ingest got to without any
in-memory session state (RETAINED_GRAPH_MODEL.md / INTEGRATION_PLAN.md
"Retained graph model").

TRANSACTION BOUNDARY
Nothing here commits. The router owns the single commit, so a failure at any
point — brand lookup, post creation, graph write — leaves the database with
zero rows from the attempt rather than a half-ingested campaign that a
retry would then duplicate. Every write is a ``flush`` inside the caller's
transaction.

STATUS AUTHORITY
``post.status`` is never assigned here. Posts are created at the model
default (DRAFT) and moved to INTERNAL_REVIEW through
``ApprovalStateMachine.transition``, which validates the transition and
writes its own audit row. That is why the contract's ``pending_review``
status maps to PostStatus.INTERNAL_REVIEW rather than to a new state.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.models.approval import Approval
from app.models.audit_log import AuditLog
from app.models.brand import Brand
from app.models.campaign import Campaign
from app.models.client import Client
from app.models.enums import (
    ApprovalStatus,
    AuditAction,
    CampaignStatus,
    ExecutionNodeRefType,
    PostStatus,
    WorkflowNodeStatus,
    WorkflowNodeType,
)
from app.models.integration_mount import MOUNT_MODES, IntegrationMount
from app.models.post import Post
from app.models.post_version import PostVersion
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.brand_repository import BrandRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.client_repository import ClientRepository
from app.repositories.integration_mount_repository import IntegrationMountRepository
from app.repositories.post_repository import PostRepository
from app.repositories.post_version_repository import PostVersionRepository
from app.schemas.integration import IntentRequest, IntentResponse, MountRequest
from app.services.approval_state_machine import ApprovalStateMachine
from app.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)

#: Fallback platform when neither the intent nor the mount names one. Posts
#: are per-platform in this schema, so an ingest must pick something; using
#: the only fully-implemented adapter keeps the row actionable.
_DEFAULT_PLATFORM = "linkedin"

#: Review stage every bootstrapped Approval is opened at.
_BOOTSTRAP_STAGE = "internal"


class IntegrationService:
    """Application service for the WS3.3 -> SMM integration endpoints."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.mounts = IntegrationMountRepository(db)
        self.brands = BrandRepository(db)
        self.clients = ClientRepository(db)
        self.campaigns = CampaignRepository(db)
        self.posts = PostRepository(db)
        self.post_versions = PostVersionRepository(db)
        self.approvals = ApprovalRepository(db)
        self.audit = AuditLogRepository(db)
        self.workflow = WorkflowService(db)
        self.state_machine = ApprovalStateMachine(db)

    # ------------------------------------------------------------------
    # mount
    # ------------------------------------------------------------------

    async def create_mount(
        self,
        organization_id: uuid.UUID,
        payload: MountRequest,
    ) -> IntegrationMount:
        """Bind an external tenant to the caller's organization.

        Raises ConflictError if the same (org, system, tenant) is mounted
        twice — the caller should reuse the existing mount_id rather than
        silently ending up with two graphs for one tenant.
        """
        if payload.mode not in MOUNT_MODES:
            raise ValidationAppError(
                f"Unknown mount mode '{payload.mode}'. Expected one of: {', '.join(MOUNT_MODES)}."
            )

        # `social_tenant_id` is the SMM-side identity in the contract. It must
        # agree with the verified JWT's org claim; otherwise a caller could
        # mount an external tenant onto an organization it does not own.
        if payload.social_tenant_id != str(organization_id):
            raise ForbiddenError(
                "social_tenant_id does not match the authenticated organization."
            )

        existing = await self.mounts.get_by_external_tenant(
            organization_id,
            external_system=payload.external_system,
            external_tenant_id=payload.tenant_id,
        )
        if existing is not None:
            raise ConflictError(
                f"Tenant '{payload.tenant_id}' from '{payload.external_system}' is already mounted.",
                details={"mount_id": str(existing.id)},
            )

        if payload.default_brand_id is not None:
            brand = await self.brands.get_by_id(organization_id, payload.default_brand_id)
            if brand is None:
                raise NotFoundError(f"Brand {payload.default_brand_id} not found.")

        if payload.default_client_id is not None:
            client = await self.clients.get_by_id(
                organization_id, payload.default_client_id
            )
            if client is None:
                raise NotFoundError(f"Client {payload.default_client_id} not found.")

        mount = IntegrationMount(
            organization_id=organization_id,
            external_system=payload.external_system,
            external_tenant_id=payload.tenant_id,
            platforms=list(payload.platforms),
            default_brand_id=payload.default_brand_id,
            default_client_id=payload.default_client_id,
            mode=payload.mode,
        )
        await self.mounts.create(mount)

        await self.audit.create(
            AuditLog(
                organization_id=organization_id,
                actor_user_id=None,
                action=AuditAction.CREATE,
                entity_type="IntegrationMount",
                entity_id=mount.id,
                description=(
                    f"Mounted external tenant '{payload.tenant_id}' "
                    f"from '{payload.external_system}' in mode '{payload.mode}'."
                ),
                metadata_json={
                    "external_system": payload.external_system,
                    "external_tenant_id": payload.tenant_id,
                    "platforms": list(payload.platforms),
                    "mode": payload.mode,
                },
            )
        )
        return mount

    # ------------------------------------------------------------------
    # intent
    # ------------------------------------------------------------------

    async def ingest_intent(
        self,
        organization_id: uuid.UUID,
        mount_id: uuid.UUID,
        payload: IntentRequest,
        *,
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> IntentResponse:
        """Materialize an inbound campaign intent into SMM's domain model.

        Every write below happens in the caller's transaction; the router
        commits once at the end. No commit here — see module docstring.
        """
        mount = await self.mounts.get_by_id(organization_id, mount_id)
        if mount is None:
            # Same 404 for "no such mount" and "another org's mount": a
            # caller must not be able to probe for foreign mount ids.
            raise NotFoundError(f"Integration mount {mount_id} not found.")

        intent = payload.campaign_intent
        draft = payload.post_draft

        brand = await self._resolve_brand(organization_id, intent.brand_id, mount)
        client = await self._resolve_client(organization_id, mount, brand)
        platforms = self._resolve_platforms(intent.platforms, mount)

        # --- execution graph root -------------------------------------
        workflow_instance_id = uuid.uuid4()
        root = await self.workflow.create_workflow_instance(
            organization_id,
            workflow_instance_id=workflow_instance_id,
            display_name=f"intent:{mount.external_system}:{mount.external_tenant_id}",
        )

        # --- the integration event itself, as a graph node -------------
        intake_node = await self.workflow.append_child_node(
            organization_id,
            workflow_instance_id=workflow_instance_id,
            parent_node_id=root.id,
            node_type=WorkflowNodeType.INTEGRATION_EVENT,
            display_name=f"intent-received:{mount.external_tenant_id}",
        )

        # --- campaign --------------------------------------------------
        campaign = Campaign(
            organization_id=organization_id,
            client_id=client.id,
            brand_id=brand.id if brand is not None else None,
            name=self._campaign_name(intent.objective, draft.headline),
            goal=intent.objective,
            status=CampaignStatus.DRAFT,
            start_date=intent.start,
            end_date=intent.end,
            budget_cents=intent.budget_cents,
        )
        await self.campaigns.create(campaign)

        root.ref_id = campaign.id
        root.ref_type = ExecutionNodeRefType.CAMPAIGN
        await self.db.flush()

        # --- posts, versions, approvals, graph nodes -------------------
        post_ids: list[uuid.UUID] = []
        for platform in platforms:
            post = await self._create_post(
                organization_id,
                campaign=campaign,
                platform=platform,
                draft=draft,
                actor_user_id=actor_user_id,
            )
            post_ids.append(post.id)

            post_node = await self.workflow.append_child_node(
                organization_id,
                workflow_instance_id=workflow_instance_id,
                parent_node_id=root.id,
                node_type=WorkflowNodeType.POST,
                display_name=f"post:{platform}",
            )
            post_node.ref_id = post.id
            post_node.ref_type = ExecutionNodeRefType.POST

            approval = await self._bootstrap_approval(organization_id, post)

            approval_node = await self.workflow.append_child_node(
                organization_id,
                workflow_instance_id=workflow_instance_id,
                parent_node_id=post_node.id,
                node_type=WorkflowNodeType.APPROVAL,
                display_name=f"approval:{_BOOTSTRAP_STAGE}",
            )
            approval_node.ref_id = approval.id
            approval_node.ref_type = ExecutionNodeRefType.APPROVAL
            await self.db.flush()

        # --- audit + close out the intake node -------------------------
        await self.audit.create(
            AuditLog(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action=AuditAction.CREATE,
                entity_type="IntegrationIntent",
                entity_id=campaign.id,
                description=(
                    f"Ingested campaign intent from '{mount.external_system}' "
                    f"tenant '{mount.external_tenant_id}' "
                    f"({len(post_ids)} post(s) across {', '.join(platforms)})."
                ),
                metadata_json={
                    "mount_id": str(mount.id),
                    "external_system": mount.external_system,
                    "external_tenant_id": mount.external_tenant_id,
                    "workflow_instance_id": str(workflow_instance_id),
                    "campaign_id": str(campaign.id),
                    "post_ids": [str(p) for p in post_ids],
                    "objective": intent.objective,
                    "platforms": platforms,
                },
            )
        )

        await self.workflow.update_node_status(
            organization_id,
            node_id=intake_node.id,
            new_status=WorkflowNodeStatus.SUCCEEDED,
        )

        return IntentResponse(
            status="pending_review",
            workflow_instance_id=str(workflow_instance_id),
            approval_url=f"/approvals/{workflow_instance_id}",
            campaign_id=campaign.id,
            post_ids=post_ids,
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    async def _resolve_brand(
        self,
        organization_id: uuid.UUID,
        requested_brand_id: Optional[uuid.UUID],
        mount: IntegrationMount,
    ) -> Optional[Brand]:
        """Intent brand wins over the mount default; both are org-scoped."""
        brand_id = requested_brand_id or mount.default_brand_id
        if brand_id is None:
            return None
        brand = await self.brands.get_by_id(organization_id, brand_id)
        if brand is None:
            raise NotFoundError(f"Brand {brand_id} not found.")
        return brand

    async def _resolve_client(
        self,
        organization_id: uuid.UUID,
        mount: IntegrationMount,
        brand: Optional[Brand],
    ) -> Client:
        """Find the Client a campaign should hang off.

        ``campaigns.client_id`` is NOT NULL, but the intent contract carries
        no client. Resolution order:
          1. ``mount.default_client_id`` — the customer an operator bound when
             mounting this external tenant. This is the intended path;
          2. the resolved brand's client (accurate whenever a brand is named);
          3. an existing placeholder previously auto-created for this tenant;
          4. a new placeholder Client, flagged ``is_placeholder=True``.

        Step 4 is deliberate rather than a 400: WS3.3 owns the customer
        relationship, so refusing the ingest would drop data SMM cannot
        re-request. But an unbound mount is a setup gap, not a steady state —
        the flag makes the resulting rows listable so operators can merge them,
        rather than leaving them to be recognized by name convention.
        """
        if mount.default_client_id is not None:
            client = await self.clients.get_by_id(
                organization_id, mount.default_client_id
            )
            if client is not None:
                return client
            logger.warning(
                "Mount %s names default_client_id %s which no longer resolves in "
                "org %s; falling back to brand/placeholder resolution.",
                mount.id,
                mount.default_client_id,
                organization_id,
            )

        if brand is not None:
            client = await self.clients.get_by_id(organization_id, brand.client_id)
            if client is not None:
                return client

        placeholder_name = f"{mount.external_system}:{mount.external_tenant_id}"
        page = await self.clients.list_paginated(
            organization_id,
            page=1,
            page_size=1,
            extra_filters=[
                Client.name == placeholder_name,
                Client.is_placeholder.is_(True),
            ],
        )
        if page.items:
            return page.items[0]

        logger.warning(
            "Mount %s (%s:%s) has no default_client_id and the intent named no "
            "brand; creating a placeholder Client. Bind a real client on the "
            "mount to stop this.",
            mount.id,
            mount.external_system,
            mount.external_tenant_id,
        )
        client = Client(
            organization_id=organization_id,
            name=placeholder_name,
            is_placeholder=True,
            notes=(
                "Auto-created by the WS3.3 integration bridge because the mount had "
                "no default_client_id and the inbound campaign intent named no brand. "
                "Merge into a real Client and set the mount's default_client_id."
            ),
        )
        await self.clients.create(client)
        return client

    def _resolve_platforms(
        self, requested: Sequence[str], mount: IntegrationMount
    ) -> list[str]:
        """Intent platforms win; fall back to the mount's, then a default.

        Deduplicated while preserving order so a caller sending
        ``["meta", "meta"]`` does not get two identical posts.
        """
        candidates = list(requested) or list(mount.platforms or []) or [_DEFAULT_PLATFORM]
        seen: set[str] = set()
        ordered: list[str] = []
        for platform in candidates:
            normalized = platform.strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
        return ordered or [_DEFAULT_PLATFORM]

    @staticmethod
    def _campaign_name(objective: str, headline: str) -> str:
        name = (headline or objective or "Untitled campaign").strip()
        return name[:255]

    @staticmethod
    def _caption(headline: str, body: str) -> str:
        parts = [p for p in (headline.strip(), body.strip()) if p]
        return "\n\n".join(parts)

    async def _create_post(
        self,
        organization_id: uuid.UUID,
        *,
        campaign: Campaign,
        platform: str,
        draft,
        actor_user_id: Optional[uuid.UUID],
    ) -> Post:
        """Create a Post at DRAFT plus its immutable v1 content snapshot,
        then move it to INTERNAL_REVIEW through the state machine."""
        caption = self._caption(draft.headline, draft.body)
        post = Post(
            organization_id=organization_id,
            campaign_id=campaign.id,
            created_by_user_id=actor_user_id,
            platform=platform[:50],
            post_type="standard",
            caption=caption,
            status=PostStatus.DRAFT,
        )
        await self.posts.create(post)

        await self.post_versions.create(
            PostVersion(
                post_id=post.id,
                version_number=1,
                caption=caption,
                edited_by_user_id=actor_user_id,
                change_summary="Initial draft ingested from the WS3.3 integration bridge.",
            )
        )

        # Status authority: never assign post.status outside the machine.
        await self.state_machine.transition(
            post=post,
            organization_id=organization_id,
            target_status=PostStatus.INTERNAL_REVIEW,
            actor_user_id=actor_user_id,
            reason="Awaiting review after external campaign intent ingest.",
        )
        return post

    async def _bootstrap_approval(
        self, organization_id: uuid.UUID, post: Post
    ) -> Approval:
        """Open a PENDING review checkpoint without moving the Post.

        ``record_decision`` with ApprovalStatus.PENDING is explicitly the
        no-transition branch of the state machine, so this creates the
        Approval row while leaving status authority intact.
        """
        return await self.state_machine.record_decision(
            post=post,
            organization_id=organization_id,
            reviewer_user_id=None,
            stage=_BOOTSTRAP_STAGE,
            decision_status=ApprovalStatus.PENDING,
        )
