"""Media router: register + list media assets.

Actual binary upload happens client-side against a pre-signed S3/MinIO URL
(out of scope to fully implement transport here); this router persists the
resulting metadata row once the upload completes.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_org
from app.core.db import get_db
from app.core.exceptions import NotFoundError
from app.models.media import Media
from app.repositories.media_repository import MediaRepository
from app.schemas.common import Page
from app.schemas.media import MediaCreate, MediaRead

router = APIRouter(prefix="/api/v1/media", tags=["media"])


@router.post("", response_model=MediaRead, status_code=status.HTTP_201_CREATED)
async def register_media(
    payload: MediaCreate,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Media:
    """Register a media asset that has already been uploaded to object storage."""
    repo = MediaRepository(db)
    media = Media(organization_id=uuid.UUID(org_id), **payload.model_dump())
    media = await repo.create(media)
    await db.commit()
    await db.refresh(media)
    return media


@router.get("", response_model=Page[MediaRead])
async def list_media(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    post_id: uuid.UUID | None = Query(default=None),
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Page[MediaRead]:
    """List media assets, optionally filtered by post."""
    repo = MediaRepository(db)
    extra_filters = [Media.post_id == post_id] if post_id else None
    result = await repo.list_paginated(
        uuid.UUID(org_id), page=page, page_size=page_size, extra_filters=extra_filters
    )
    return Page[MediaRead](
        items=[MediaRead.model_validate(m) for m in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.get("/{media_id}", response_model=MediaRead)
async def get_media(
    media_id: uuid.UUID,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Media:
    """Fetch a single media asset by id."""
    repo = MediaRepository(db)
    media = await repo.get_by_id(uuid.UUID(org_id), media_id)
    if media is None:
        raise NotFoundError(f"Media {media_id} not found.")
    return media


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_media(
    media_id: uuid.UUID,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a media asset's metadata row (does not delete the S3 object —
    that is handled by a lifecycle policy / separate cleanup job)."""
    repo = MediaRepository(db)
    media = await repo.get_by_id(uuid.UUID(org_id), media_id)
    if media is None:
        raise NotFoundError(f"Media {media_id} not found.")
    await repo.delete(media)
    await db.commit()
