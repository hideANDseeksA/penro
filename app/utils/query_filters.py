"""Server-side filtering, sorting and pagination against the mapped models.

Query grammar (identical on every list endpoint):

    ?page=2&size=50
    &sort=-shipment_date,buyer
    &shipment_status=cleared              # implicit eq
    &shipment_date__gte=2026-01-01
    &gross_receipts__lt=1000000
    &buyer__ilike=sinosteel               # auto-wrapped in %...%
    &shipment_status__in=declared,cleared
    &final_volume__isnull=true

Only columns that exist on the model are accepted; a typo returns 422 rather
than quietly returning the unfiltered table.
"""
from __future__ import annotations

import datetime as dt
import decimal
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import Select, and_, func, inspect, or_, select
from sqlalchemy.orm import Session

from app.schemas.pagination import RESERVED, PageParams

OPERATORS = {"eq", "ne", "gt", "gte", "lt", "lte", "like", "ilike", "in", "isnull"}


def _coerce(column, value: str) -> Any:
    if value == "":
        return None
    try:
        py = column.type.python_type
    except NotImplementedError:
        return value
    if py is bool:
        return value.lower() in {"1", "true", "t", "yes", "y"}
    if py is int:
        return int(value)
    if py in (float, decimal.Decimal):
        return decimal.Decimal(value)
    if py is dt.date:
        return dt.date.fromisoformat(value)
    if py is dt.datetime:
        return dt.datetime.fromisoformat(value)
    if py is uuid.UUID:
        return uuid.UUID(value)
    return value


def build_filters(model, params: PageParams) -> list:
    mapper = inspect(model)
    columns = {c.key: c for c in mapper.columns}
    conditions = []

    for raw_key, raw_value in params.raw:
        if raw_key in RESERVED:
            continue
        field, _, op = raw_key.partition("__")
        op = op or "eq"
        if field not in columns:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Unknown filter field '{field}'. Allowed: {', '.join(sorted(columns))}",
            )
        if op not in OPERATORS:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Unknown operator '{op}'. Allowed: {', '.join(sorted(OPERATORS))}",
            )
        col = columns[field]
        try:
            if op == "eq":
                conditions.append(col == _coerce(col, raw_value))
            elif op == "ne":
                conditions.append(col != _coerce(col, raw_value))
            elif op == "gt":
                conditions.append(col > _coerce(col, raw_value))
            elif op == "gte":
                conditions.append(col >= _coerce(col, raw_value))
            elif op == "lt":
                conditions.append(col < _coerce(col, raw_value))
            elif op == "lte":
                conditions.append(col <= _coerce(col, raw_value))
            elif op == "like":
                conditions.append(col.like(f"%{raw_value}%"))
            elif op == "ilike":
                # func.lower keeps behaviour identical on MySQL and PostgreSQL
                conditions.append(func.lower(col).like(f"%{raw_value.lower()}%"))
            elif op == "in":
                values = [_coerce(col, v) for v in raw_value.split(",") if v != ""]
                conditions.append(col.in_(values))
            elif op == "isnull":
                truthy = raw_value.lower() in {"1", "true", "t", "yes", "y"}
                conditions.append(col.is_(None) if truthy else col.is_not(None))
        except (ValueError, decimal.InvalidOperation) as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, f"Bad value for '{raw_key}': {exc}"
            ) from exc

    if params.q:
        text_cols = [c for c in mapper.columns if str(c.type).upper().startswith(("VARCHAR", "STRING", "CHAR", "TEXT"))]
        if text_cols:
            needle = f"%{params.q.lower()}%"
            conditions.append(or_(*[func.lower(c).like(needle) for c in text_cols]))

    return conditions


def apply_sort(stmt: Select, model, sort: str | None) -> Select:
    mapper = inspect(model)
    columns = {c.key: c for c in mapper.columns}
    if not sort:
        pk_col = list(mapper.primary_key)[0]
        return stmt.order_by(pk_col)
    order = []
    for token in sort.split(","):
        token = token.strip()
        if not token:
            continue
        desc = token.startswith("-")
        name = token[1:] if desc else token
        if name not in columns:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, f"Cannot sort by unknown column '{name}'"
            )
        order.append(columns[name].desc() if desc else columns[name].asc())
    return stmt.order_by(*order) if order else stmt


def paginate(db: Session, model, params: PageParams, *, base_conditions: list | None = None) -> dict:
    conditions = list(base_conditions or []) + build_filters(model, params)
    where = and_(*conditions) if conditions else None

    count_stmt = select(func.count()).select_from(model)
    stmt = select(model)
    if where is not None:
        count_stmt = count_stmt.where(where)
        stmt = stmt.where(where)

    total = db.scalar(count_stmt) or 0
    stmt = apply_sort(stmt, model, params.sort).limit(params.size).offset((params.page - 1) * params.size)
    items = list(db.scalars(stmt))

    pages = (total + params.size - 1) // params.size if params.size else 0
    return {
        "items": items,
        "page": params.page,
        "size": params.size,
        "total": total,
        "pages": pages,
        "has_next": params.page < pages,
        "has_prev": params.page > 1,
    }
