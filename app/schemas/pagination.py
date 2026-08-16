"""Pagination envelope and paging/sorting query parameters.

The filter grammar itself lives in `app.utils.query_filters`; this module only
defines the shape every list endpoint returns and the parameters it accepts.
"""
from __future__ import annotations

from typing import Generic, TypeVar

from fastapi import Query, Request
from pydantic import BaseModel

from app.core.config import settings

T = TypeVar("T")

RESERVED = {"page", "size", "sort", "q", "search"}


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    size: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool


class PageParams:
    """FastAPI dependency capturing paging/sorting plus the raw query string."""

    def __init__(
        self,
        request: Request,
        page: int = Query(1, ge=1, description="1-based page number"),
        size: int = Query(
            settings.PAGE_SIZE_DEFAULT, ge=1, le=settings.PAGE_SIZE_MAX, description="Rows per page"
        ),
        sort: str | None = Query(None, description="Comma-separated columns; prefix '-' for DESC"),
        q: str | None = Query(None, description="Free-text search across the model's string columns"),
    ) -> None:
        self.page = page
        self.size = size
        self.sort = sort
        self.q = q
        self.raw: list[tuple[str, str]] = list(request.query_params.multi_items())
