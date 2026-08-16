"""Shared column helpers for the model layer (kept in core so app.auth can use them)."""
from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.types import GUID, new_uuid


def pk() -> Mapped:
    """UUID primary key."""
    return mapped_column(GUID(), primary_key=True, default=new_uuid)


def fk(target: str, *, nullable: bool = False, index: bool = True) -> Mapped:
    """Indexed foreign key that refuses to orphan rows."""
    return mapped_column(
        GUID(), ForeignKey(target, ondelete="RESTRICT"), nullable=nullable, index=index
    )
