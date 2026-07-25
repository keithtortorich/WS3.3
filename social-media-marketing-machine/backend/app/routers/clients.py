"""Client CRUD router — reference-quality implementation.

Every endpoint requires an authenticated org context (``get_current_org``)
and delegates persistence to :class:`ClientRepository`, which enforces
org-scoping at the query layer (see ``app/repositories/base.py``).
"""
from __future__ import annotations

import math
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_org
from app.core.db import get_db
from app.core.exceptions import NotFoundError
from app.models.client import Client
from app.repositories.client_repository import ClientRepository
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.schemas.common import Page

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: ClientCreate,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Client:
    """Create a new Client under the caller's organization."""
    repo = ClientRepository(db)
    client = Client(organization_id=uuid.UUID(org_id), **payload.model_dump())
    client = await repo.create(client)
    await db.commit()
    await db.refresh(client)
    return client


@router.get("", response_model=Page[ClientRead])
async def list_clients(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Page[ClientRead]:
    """List clients for the caller's organization, paginated."""
    repo = ClientRepository(db)
    result = await repo.list_paginated(uuid.UUID(org_id), page=page, page_size=page_size)
    return Page[ClientRead](
        items=[ClientRead.model_validate(c) for c in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    client_id: uuid.UUID,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Client:
    """Fetch a single Client by id (404 if not found or not in caller's org)."""
    repo = ClientRepository(db)
    client = await repo.get_by_id(uuid.UUID(org_id), client_id)
    if client is None:
        raise NotFoundError(f"Client {client_id} not found.")
    return client


@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: uuid.UUID,
    payload: ClientUpdate,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Client:
    """Partially update a Client."""
    repo = ClientRepository(db)
    client = await repo.get_by_id(uuid.UUID(org_id), client_id)
    if client is None:
        raise NotFoundError(f"Client {client_id} not found.")
    updates = payload.model_dump(exclude_unset=True)
    client = await repo.update(client, **updates)
    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_client(
    client_id: uuid.UUID,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a Client (cascades to Brands/Campaigns per FK ondelete rules)."""
    repo = ClientRepository(db)
    client = await repo.get_by_id(uuid.UUID(org_id), client_id)
    if client is None:
        raise NotFoundError(f"Client {client_id} not found.")
    await repo.delete(client)
    await db.commit()
