from __future__ import annotations

from app.models.comment import Comment
from app.repositories.base import OrgScopedRepository


class CommentRepository(OrgScopedRepository[Comment]):
    model = Comment
