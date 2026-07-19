"""Notifications router: list + mark-as-read for the current user."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthContext, get_current_org, get_current_user
from app.core.db import get_db
from app.core.exceptions import NotFoundError
from app.models.notification import Notification
from app.repositories.notification_repository import NotificationRepository
from app.schemas.common import Page
from app.schemas.notification import NotificationMarkReadRequest, NotificationRead

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("", response_model=Page[NotificationRead])
async def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    unread_only: bool = Query(default=False),
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Page[NotificationRead]:
    """List notifications for the caller's organization (optionally unread only)."""
    repo = NotificationRepository(db)
    extra_filters = [Notification.is_read.is_(False)] if unread_only else None
    result = await repo.list_paginated(
        uuid.UUID(org_id), page=page, page_size=page_size, extra_filters=extra_filters
    )
    return Page[NotificationRead](
        items=[NotificationRead.model_validate(n) for n in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.patch("/{notification_id}", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: uuid.UUID,
    payload: NotificationMarkReadRequest,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Notification:
    """Mark a notification read/unread."""
    repo = NotificationRepository(db)
    notification = await repo.get_by_id(uuid.UUID(org_id), notification_id)
    if notification is None:
        raise NotFoundError(f"Notification {notification_id} not found.")
    notification = await repo.update(notification, is_read=payload.is_read)
    await db.commit()
    await db.refresh(notification)
    return notification
