"""PostVersion repository.

Not org-scoped directly (PostVersion has no organization_id column — it is
always accessed via its parent Post, which IS org-scoped), so this does not
extend OrgScopedRepository. Callers must first verify Post org-ownership.

Version numbering is the interesting part here: ``MAX(version_number) + 1``
computed in the application is inherently racy — two concurrent edits of the
same Post can both read the same max and both try to insert the same number.
The ``uq_post_version_number`` unique constraint turns that race into an
IntegrityError instead of silent history corruption, and ``snapshot_post``
below retries inside a SAVEPOINT so the losing writer transparently lands on
the next free number rather than failing the request.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.models.post import Post
from app.models.post_version import PostVersion

# Bounded so a genuinely stuck contention loop surfaces as an error rather
# than spinning forever.
_MAX_VERSION_INSERT_ATTEMPTS = 5


class PostVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_post(self, post_id: uuid.UUID) -> list[PostVersion]:
        stmt = select(PostVersion).where(PostVersion.post_id == post_id).order_by(PostVersion.version_number)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_version_number(self, post_id: uuid.UUID) -> int:
        stmt = select(func.coalesce(func.max(PostVersion.version_number), 0)).where(
            PostVersion.post_id == post_id
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def create(self, version: PostVersion) -> PostVersion:
        self.session.add(version)
        await self.session.flush()
        return version

    async def snapshot_post(
        self,
        post: Post,
        *,
        change_summary: Optional[str] = None,
        edited_by_user_id: Optional[uuid.UUID] = None,
    ) -> PostVersion:
        """Append an immutable snapshot of ``post``'s current content.

        Retries on unique-constraint collision so that concurrent edits can
        never produce two rows sharing a ``(post_id, version_number)`` pair.
        """
        last_error: Optional[IntegrityError] = None
        for _ in range(_MAX_VERSION_INSERT_ATTEMPTS):
            next_number = await self.get_latest_version_number(post.id) + 1
            version = PostVersion(
                post_id=post.id,
                version_number=next_number,
                caption=post.caption,
                hashtags=post.hashtags,
                edited_by_user_id=edited_by_user_id,
                change_summary=change_summary or "Content updated.",
            )
            savepoint = await self.session.begin_nested()
            try:
                self.session.add(version)
                await self.session.flush()
            except IntegrityError as exc:
                last_error = exc
                # Rolling back to the savepoint also expunges the failed
                # pending INSERT, so the session is clean for the retry.
                await savepoint.rollback()
                continue
            await savepoint.commit()
            return version

        raise ConflictError(
            f"Could not allocate a version number for post {post.id} after "
            f"{_MAX_VERSION_INSERT_ATTEMPTS} attempts due to concurrent edits."
        ) from last_error
