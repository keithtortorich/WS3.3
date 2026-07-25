"""Shared Pydantic schema building blocks (pagination envelope, etc.)."""
from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)


class Page(BaseModel, Generic[T]):
    """Generic paginated response envelope used by every list endpoint."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
