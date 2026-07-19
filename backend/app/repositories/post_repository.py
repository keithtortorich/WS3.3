from __future__ import annotations

from app.models.post import Post
from app.repositories.base import OrgScopedRepository


class PostRepository(OrgScopedRepository[Post]):
    model = Post
