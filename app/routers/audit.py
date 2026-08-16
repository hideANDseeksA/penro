"""AUDIT_LOG access.

Written by the application only — who did what, to which record, from where.
Read-only to every client so the trail cannot be edited from the API, which is
what makes it useful for Sec. 11 confidentiality review and later disputes
("who issued this clearance", "who approved this refund").
"""
from __future__ import annotations

from fastapi import APIRouter

from app.auth.models import AuditLog
from app.core.crud import build_crud_router
from app.core.permission import ADMIN

router = APIRouter()

router.include_router(
    build_crud_router(AuditLog, prefix="/audit-logs", tag="administration",
                      read_roles=(ADMIN,), read_only=True)
)
