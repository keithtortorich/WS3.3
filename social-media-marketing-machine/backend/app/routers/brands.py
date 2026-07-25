"""Brand CRUD router — reference-quality implementation."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_org
from app.core.db import get_db
from app.core.exceptions import NotFoundError
from app.models.brand import Brand
from app.repositories.brand_repository import BrandRepository
from app.schemas.brand import BrandCreate, BrandRead, BrandUpdate
from app.schemas.common import Page

router = APIRouter(prefix="/api/v1/brands", tags=["brands"])


@router.post("", response_model=BrandRead, status_code=status.HTTP_201_CREATED)
async def create_brand(
    payload: BrandCreate,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Brand:
    """Create a new Brand under a Client belonging to the caller's organization."""
    repo = BrandRepository(db)
    brand = Brand(organization_id=uuid.UUID(org_id), **payload.model_dump())
    brand = await repo.create(brand)
    await db.commit()
    await db.refresh(brand)
    return brand


@router.get("", response_model=Page[BrandRead])
async def list_brands(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    client_id: uuid.UUID | None = Query(default=None),
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Page[BrandRead]:
    """List brands for the caller's organization, optionally filtered by client."""
    repo = BrandRepository(db)
    extra_filters = [Brand.client_id == client_id] if client_id else None
    result = await repo.list_paginated(
        uuid.UUID(org_id), page=page, page_size=page_size, extra_filters=extra_filters
    )
    return Page[BrandRead](
        items=[BrandRead.model_validate(b) for b in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.get("/{brand_id}", response_model=BrandRead)
async def get_brand(
    brand_id: uuid.UUID,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Brand:
    """Fetch a single Brand by id."""
    repo = BrandRepository(db)
    brand = await repo.get_by_id(uuid.UUID(org_id), brand_id)
    if brand is None:
        raise NotFoundError(f"Brand {brand_id} not found.")
    return brand


@router.patch("/{brand_id}", response_model=BrandRead)
async def update_brand(
    brand_id: uuid.UUID,
    payload: BrandUpdate,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Brand:
    """Partially update a Brand."""
    repo = BrandRepository(db)
    brand = await repo.get_by_id(uuid.UUID(org_id), brand_id)
    if brand is None:
        raise NotFoundError(f"Brand {brand_id} not found.")
    updates = payload.model_dump(exclude_unset=True)
    brand = await repo.update(brand, **updates)
    await db.commit()
    await db.refresh(brand)
    return brand


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_brand(
    brand_id: uuid.UUID,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a Brand."""
    repo = BrandRepository(db)
    brand = await repo.get_by_id(uuid.UUID(org_id), brand_id)
    if brand is None:
        raise NotFoundError(f"Brand {brand_id} not found.")
    await repo.delete(brand)
    await db.commit()
