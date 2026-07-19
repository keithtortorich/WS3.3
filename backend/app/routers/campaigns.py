"""Campaign CRUD router — reference-quality implementation.

This is the router exercised end-to-end by the frontend's Campaigns page
(task #10) and by the integration test in task #12
(POST /api/v1/campaigns then GET it back).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_org
from app.core.db import get_db
from app.core.exceptions import NotFoundError
from app.models.campaign import Campaign
from app.repositories.campaign_repository import CampaignRepository
from app.schemas.campaign import CampaignCreate, CampaignRead, CampaignUpdate
from app.schemas.common import Page

router = APIRouter(prefix="/api/v1/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Campaign:
    """Create a new Campaign under a Client belonging to the caller's organization."""
    repo = CampaignRepository(db)
    campaign = Campaign(organization_id=uuid.UUID(org_id), **payload.model_dump())
    campaign = await repo.create(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.get("", response_model=Page[CampaignRead])
async def list_campaigns(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    client_id: uuid.UUID | None = Query(default=None),
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Page[CampaignRead]:
    """List campaigns for the caller's organization, optionally filtered by client."""
    repo = CampaignRepository(db)
    extra_filters = [Campaign.client_id == client_id] if client_id else None
    result = await repo.list_paginated(
        uuid.UUID(org_id), page=page, page_size=page_size, extra_filters=extra_filters
    )
    return Page[CampaignRead](
        items=[CampaignRead.model_validate(c) for c in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.get("/{campaign_id}", response_model=CampaignRead)
async def get_campaign(
    campaign_id: uuid.UUID,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Campaign:
    """Fetch a single Campaign by id."""
    repo = CampaignRepository(db)
    campaign = await repo.get_by_id(uuid.UUID(org_id), campaign_id)
    if campaign is None:
        raise NotFoundError(f"Campaign {campaign_id} not found.")
    return campaign


@router.patch("/{campaign_id}", response_model=CampaignRead)
async def update_campaign(
    campaign_id: uuid.UUID,
    payload: CampaignUpdate,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Campaign:
    """Partially update a Campaign."""
    repo = CampaignRepository(db)
    campaign = await repo.get_by_id(uuid.UUID(org_id), campaign_id)
    if campaign is None:
        raise NotFoundError(f"Campaign {campaign_id} not found.")
    updates = payload.model_dump(exclude_unset=True)
    campaign = await repo.update(campaign, **updates)
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_campaign(
    campaign_id: uuid.UUID,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a Campaign (cascades to Posts per FK ondelete rules)."""
    repo = CampaignRepository(db)
    campaign = await repo.get_by_id(uuid.UUID(org_id), campaign_id)
    if campaign is None:
        raise NotFoundError(f"Campaign {campaign_id} not found.")
    await repo.delete(campaign)
    await db.commit()
