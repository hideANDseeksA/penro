"""Request-level security helpers shared by routers."""
from __future__ import annotations

from fastapi import HTTPException, status

from app.core.permission import owns_taxpayer_record
from app.core.security import CurrentUser


def assert_owns(user: CurrentUser, taxpayer_id, message: str = "Not your record") -> None:
    """403 unless the caller may act on this taxpayer's records."""
    if not owns_taxpayer_record(user, taxpayer_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, message)


def client_ip(request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
