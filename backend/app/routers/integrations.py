"""WS3.3 -> SMM integration bridge router.

Implements INTEGRATION_PLAN.md's two-endpoint contract:

    POST /integrations/social-media-marketing/mount
        -> 204, Location: /integrations/social-media-marketing/mount/{mount_id}

    POST /integrations/social-media-marketing/mount/{mount_id}/intent
        -> 200, {"status": "pending_review", "workflow_instance_id", "approval_url"}

Both endpoints use the same auth dependencies as ``app/routers/campaigns.py``
(``get_current_org`` over a verified Clerk bearer token) and are strictly
org-scoped: the mount id in the path is resolved through the org-scoped
repository, so another organization's mount is a 404, not a leak.

This router owns the transaction boundary for ingest. ``IntegrationService``
never commits; on any failure the session is rolled back so a partial ingest
leaves no rows behind, and the original typed error still surfaces to the
client through the app's registered exception handlers.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_org
from app.core.db import get_db
from app.schemas.integration import IntentRequest, IntentResponse, MountRequest
from app.services.integration_service import IntegrationService

router = APIRouter(
    prefix="/integrations/social-media-marketing",
    tags=["integrations"],
)


@router.post("/mount", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def create_mount(
    payload: MountRequest,
    response: Response,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Bind an external system's tenant to the caller's organization."""
    service = IntegrationService(db)
    try:
        mount = await service.create_mount(uuid.UUID(org_id), payload)
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers={"Location": f"{router.prefix}/mount/{mount.id}"},
    )


@router.post("/mount/{mount_id}/intent", response_model=IntentResponse)
async def submit_intent(
    mount_id: uuid.UUID,
    payload: IntentRequest,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> IntentResponse:
    """Ingest a campaign intent + post draft into SMM's domain model.

    All-or-nothing: Campaign, Posts, PostVersions, Approvals, execution
    graph nodes and the audit row commit together or not at all.
    """
    service = IntegrationService(db)
    try:
        result = await service.ingest_intent(uuid.UUID(org_id), mount_id, payload)
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    return result
