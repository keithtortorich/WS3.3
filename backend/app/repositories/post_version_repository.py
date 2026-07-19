"""PostVersion repository.

Not org-scoped directly (PostVersion has no organization_id column — it is
always accessed via its parent Post, which IS org-scoped), so this does not
extend OrgScopedRepository. Callers must first verify Post org-ownership.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post_version import PostVersion


class PostVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_post(self, post_id: uuid.UUID) -> list[PostVersion]:
        stmt = select(PostVersion).where(PostVersion.post_id == post_id).order_by(PostVersion.version_number)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_version_number(self, post_id: uuid.UUID) -> int:
        versions = await self.list_for_post(post_id)
        return versions[-1].version_number if versions else 0

    async def create(self, version: PostVersion) -> PostVersion:
        self.session.add(version)
        await self.session.flush()
        return version
