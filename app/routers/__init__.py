"""API v1 router assembly.

Business endpoints (clearance, assessment, returns, remedies, enforcement) and
the generic registry endpoints for each ERD entity live side by side in the
domain modules; this module just mounts them under /api/v1.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.api_key import require_api_key
from app.routers import (
    admin,
    assessment,
    audit,
    auth,
    clearance,
    enforcement,
    mining,
    monitoring,
    reference,
    remedy,
    shipment,
    tax_return,
    taxpayer,
)

# X-API-Key is enforced on the whole tree, login included.
api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)])

for module in (
    auth,
    taxpayer,
    mining,
    shipment,
    clearance,
    assessment,
    tax_return,
    remedy,
    enforcement,
    monitoring,
    reference,
    admin,
    audit,
):
    api_router.include_router(module.router)

__all__ = ["api_router"]
