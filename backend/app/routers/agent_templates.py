"""AgentTemplate CRUD router.

Endpoints are intentionally read-heavy because the extracted HubSpot agents
are mostly content; runtime creation will be handled separately in a future
task. This router exposes organization-scoped listing, detail, and limited
update so admins can correct metadata or retire a generated template.
"""
from __future__ import annotations

from typing import List
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_org
from app.core.db import get_db
from app.core.exceptions import NotFoundError
from app.models.agent_template import AgentTemplate
from app.repositories.agent_template_repository import AgentTemplateRepository
from app.schemas.agent_template import AgentTemplateCreate, AgentTemplateRead, AgentTemplateUpdate

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.post("", response_model=AgentTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_agent_template(
    payload: AgentTemplateCreate,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> AgentTemplate:
    """Create a new AgentTemplate for the caller's organization."""
    repo = AgentTemplateRepository(db)
    template = AgentTemplate(organization_id=uuid.UUID(org_id), **payload.model_dump())
    template = await repo.create(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.get("", response_model=List[AgentTemplateRead])
async def list_agent_templates(
    category: str | None = Query(default=None),
    active_only: bool = Query(default=True),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> list[AgentTemplateRead]:
    """List AgentTemplates for the caller's organization."""
    repo = AgentTemplateRepository(db)
    extra_filters = []
    if active_only:
        extra_filters.append(AgentTemplate.is_active.is_(True))
    if category:
        extra_filters.append(AgentTemplate.category == category)

    result = await repo.list_paginated(
        uuid.UUID(org_id), page=page, page_size=page_size, extra_filters=extra_filters
    )
    return [AgentTemplateRead.model_validate(item) for item in result.items]


@router.get("/{agent_id}", response_model=AgentTemplateRead)
async def get_agent_template(
    agent_id: uuid.UUID,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> AgentTemplateRead:
    """Fetch a single AgentTemplate by id."""
    repo = AgentTemplateRepository(db)
    template = await repo.get_by_id(uuid.UUID(org_id), agent_id)
    if template is None:
        raise NotFoundError(f"AgentTemplate {agent_id} not found.")
    return AgentTemplateRead.model_validate(template)


@router.patch("/{agent_id}", response_model=AgentTemplateRead)
async def update_agent_template(
    agent_id: uuid.UUID,
    payload: AgentTemplateUpdate,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> AgentTemplateRead:
    """Partially update an AgentTemplate."""
    repo = AgentTemplateRepository(db)
    template = await repo.get_by_id(uuid.UUID(org_id), agent_id)
    if template is None:
        raise NotFoundError(f"AgentTemplate {agent_id} not found.")
    updates = payload.model_dump(exclude_unset=True)
    template = await repo.update(template, **updates)
    await db.commit()
    await db.refresh(template)
    return AgentTemplateRead.model_validate(template)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_agent_template(
    agent_id: uuid.UUID,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Hard delete an AgentTemplate."""
    repo = AgentTemplateRepository(db)
    template = await repo.get_by_id(uuid.UUID(org_id), agent_id)
    if template is None:
        raise NotFoundError(f"AgentTemplate {agent_id} not found.")
    await repo.delete(template)
    await db.commit()
