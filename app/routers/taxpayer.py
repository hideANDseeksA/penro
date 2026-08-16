"""Taxpayer registry (Sec. 4-5)."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.crud import build_crud_router
from app.core.permission import TREASURY
from app.models.taxpayer import Taxpayer

router = APIRouter()

router.include_router(
    build_crud_router(Taxpayer, prefix="/taxpayers", tag="taxpayers",
                      write_roles=TREASURY, taxpayer_scoped=True)
)
