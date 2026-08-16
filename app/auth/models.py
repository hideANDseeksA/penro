"""Authentication and audit entities.

System-level additions: the ordinance describes who must do what but
prescribes no login or access-control model, so ROLE, SYSTEM_USER and
AUDIT_LOG are implementation infrastructure, not legal requirements.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.types import GUID
from app.core.columns import fk, pk


class Role(Base):
    __tablename__ = "role"

    role_id: Mapped[str] = pk()
    role_name: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str | None] = mapped_column(String(255))


class SystemUser(Base):
    # Table is named app_user, not system_user: PostgreSQL 16+ reserves
    # SYSTEM_USER as a SQL:2023 keyword, which makes an unquoted reference to
    # a system_user table/column a syntax error (see alembic/versions/0001_initial_schema.py).
    __tablename__ = "app_user"

    user_id: Mapped[str] = pk()
    role_id: Mapped[str] = fk("role.role_id")
    provincial_office_id: Mapped[str | None] = fk("provincial_office.provincial_office_id", nullable=True)
    taxpayer_id: Mapped[str | None] = fk("taxpayer.taxpayer_id", nullable=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str | None] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[dt.date | None] = mapped_column(Date)

    role = relationship("Role")


class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id: Mapped[str] = pk()
    user_id: Mapped[str | None] = fk("app_user.user_id", nullable=True)
    action: Mapped[str] = mapped_column(String(50), index=True)
    entity_name: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[str | None] = mapped_column(GUID(), nullable=True, index=True)
    details: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    logged_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=lambda: dt.datetime.now(dt.UTC).replace(tzinfo=None), index=True
    )
