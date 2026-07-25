"""Base repository with mandatory organization-scoping.

WHY THIS LIVES HERE (AND NOT JUST IN ROUTERS):
Multi-tenant data leaks are usually not caused by a missing feature — they
are caused by a *forgotten* ``WHERE organization_id = ...`` clause in one
query, buried in one endpoint, that nobody notices until a customer reports
seeing another tenant's data. Relying on every router author to remember to
filter by org on every single query is a single point of failure.

Instead, we push org-scoping down into the repository layer: every
tenant-scoped repository extends :class:`OrgScopedRepository`, and every
read/update/delete method requires an ``organization_id`` argument that is
applied via a ``WHERE`` clause *before* the query is ever executed. A
developer would have to actively bypass the repository (going straight to
`session.execute(...)`) to leak data across tenants — which is a much more
visible, reviewable action than silently omitting a filter. This is
defense-in-depth: the router/service layer is ALSO expected to pass the
correct ``organization_id`` (extracted from the authenticated JWT via
``get_current_org`` — see ``app/core/auth.py``), but even if that layer had
a bug, the repository is the last line of defense.
"""
from __future__ import annotations

import uuid
from typing import Any, Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class PageResult(Generic[ModelT]):
    """Simple pagination envelope returned by ``list_paginated``."""

    def __init__(self, items: Sequence[ModelT], total: int, page: int, page_size: int) -> None:
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size

    @property
    def total_pages(self) -> int:
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


class OrgScopedRepository(Generic[ModelT]):
    """Base class for repositories operating on tables with an
    ``organization_id`` column. Subclasses set ``model`` to the ORM class.

    Every method that reads/writes a specific row takes ``organization_id``
    explicitly and folds it into the query filter — callers cannot
    accidentally omit it because it is a required positional/keyword
    argument, not an afterthought.
    """

    model: Type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, organization_id: uuid.UUID, obj_id: uuid.UUID) -> Optional[ModelT]:
        stmt = select(self.model).where(
            self.model.id == obj_id,
            self.model.organization_id == organization_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        organization_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        extra_filters: Optional[list[Any]] = None,
        order_by: Optional[Any] = None,
    ) -> PageResult[ModelT]:
        page = max(page, 1)
        page_size = max(1, min(page_size, 200))
        filters = [self.model.organization_id == organization_id]
        if extra_filters:
            filters.extend(extra_filters)

        count_stmt = select(func.count()).select_from(self.model).where(*filters)
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = select(self.model).where(*filters)
        stmt = stmt.order_by(order_by) if order_by is not None else stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        return PageResult(items=items, total=total, page=page, page_size=page_size)

    async def create(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(self, obj: ModelT, **fields: Any) -> ModelT:
        for key, value in fields.items():
            setattr(obj, key, value)
        await self.session.flush()
        return obj

    async def delete(self, obj: ModelT) -> None:
        await self.session.delete(obj)
        await self.session.flush()
