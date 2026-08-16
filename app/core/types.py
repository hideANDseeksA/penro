"""Portable column types so one migration set runs on PostgreSQL and MySQL."""
from __future__ import annotations

import uuid

from sqlalchemy import CHAR, Numeric, TypeDecorator
from sqlalchemy.dialects.mysql import CHAR as MYSQL_CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class GUID(TypeDecorator):
    """UUID column: native uuid on PostgreSQL, CHAR(36) on MySQL/SQLite."""

    impl = CHAR
    cache_ok = True

    @property
    def python_type(self):  # drives schema generation and filter coercion
        return uuid.UUID

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        if dialect.name == "mysql":
            return dialect.type_descriptor(MYSQL_CHAR(36))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        return value if dialect.name == "postgresql" else str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


# Money / volume precision. MySQL and PostgreSQL both honour DECIMAL(18,2).
Money = Numeric(18, 2)
Volume = Numeric(18, 3)
Rate = Numeric(9, 6)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()
