"""Post CRUD router — reference-quality implementation.

NOTE: this router only handles content CRUD. Status transitions (Draft ->
Internal Review -> ... -> Published) are handled exclusively by
``app/routers/approvals.py`` via the approval state machine (task #8), so
that version history + audit logging are never bypassed.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_org
from app.core.db import get_db
from app.core.exceptions import NotFoundError
from app.models.post import Post
from app.models.post_version import PostVersion
from app.repositories.post_repository import PostRepository
from app.repositories.post_version_repository import PostVersionRepository
from app.schemas.common import Page
from app.schemas.post import PostCreate, PostRead, PostUpdate

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])


@router.post("", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_post(
    payload: PostCreate,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Post:
    """Create a new Post (starts in Draft status) under a Campaign."""
    repo = PostRepository(db)
    post = Post(organization_id=uuid.UUID(org_id), **payload.model_dump())
    post = await repo.create(post)
    # Seed version 1 so version history is never empty for a Post that exists.
    version_repo = PostVersionRepository(db)
    await version_repo.create(
        PostVersion(
            post_id=post.id,
            version_number=1,
            caption=post.caption,
            hashtags=post.hashtags,
            change_summary="Initial creation.",
        )
    )
    await db.commit()
    await db.refresh(post)
    return post


@router.get("", response_model=Page[PostRead])
async def list_posts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    campaign_id: uuid.UUID | None = Query(default=None),
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Page[PostRead]:
    """List posts for the caller's organization, optionally filtered by campaign."""
    repo = PostRepository(db)
    extra_filters = [Post.campaign_id == campaign_id] if campaign_id else None
    result = await repo.list_paginated(
        uuid.UUID(org_id), page=page, page_size=page_size, extra_filters=extra_filters
    )
    return Page[PostRead](
        items=[PostRead.model_validate(p) for p in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.get("/{post_id}", response_model=PostRead)
async def get_post(
    post_id: uuid.UUID,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Post:
    """Fetch a single Post by id."""
    repo = PostRepository(db)
    post = await repo.get_by_id(uuid.UUID(org_id), post_id)
    if post is None:
        raise NotFoundError(f"Post {post_id} not found.")
    return post


@router.patch("/{post_id}", response_model=PostRead)
async def update_post(
    post_id: uuid.UUID,
    payload: PostUpdate,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> Post:
    """Edit a Post's content, recording a new PostVersion snapshot."""
    repo = PostRepository(db)
    post = await repo.get_by_id(uuid.UUID(org_id), post_id)
    if post is None:
        raise NotFoundError(f"Post {post_id} not found.")

    updates = payload.model_dump(exclude_unset=True, exclude={"change_summary"})
    if updates:
        post = await repo.update(post, **updates)
        version_repo = PostVersionRepository(db)
        next_version = await version_repo.get_latest_version_number(post.id) + 1
        await version_repo.create(
            PostVersion(
                post_id=post.id,
                version_number=next_version,
                caption=post.caption,
                hashtags=post.hashtags,
                change_summary=payload.change_summary or "Content updated.",
            )
        )
    await db.commit()
    await db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_post(
    post_id: uuid.UUID,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a Post (cascades to versions/media/approvals/comments)."""
    repo = PostRepository(db)
    post = await repo.get_by_id(uuid.UUID(org_id), post_id)
    if post is None:
        raise NotFoundError(f"Post {post_id} not found.")
    await repo.delete(post)
    await db.commit()
