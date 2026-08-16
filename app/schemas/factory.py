"""Build pydantic schemas from the mapped models.

The ERD is the schema of record, so the API contract is derived from it rather
than hand-copied — a field renamed in app/models cannot drift out of sync with
the request/response models.
"""
from __future__ import annotations

import datetime as dt
import decimal
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, create_model
from sqlalchemy import inspect

_TYPE_MAP = {
    str: str,
    int: int,
    bool: bool,
    float: float,
    decimal.Decimal: decimal.Decimal,
    dt.date: dt.date,
    dt.datetime: dt.datetime,
    uuid.UUID: uuid.UUID,
}


def _py_type(column) -> Any:
    try:
        return _TYPE_MAP.get(column.type.python_type, str)
    except NotImplementedError:
        return str


def make_schemas(model) -> tuple[type[BaseModel], type[BaseModel], type[BaseModel]]:
    """Return (ReadSchema, CreateSchema, UpdateSchema) for a mapped model."""
    mapper = inspect(model)
    pk_names = {c.key for c in mapper.primary_key}
    name = model.__name__

    read_fields: dict[str, Any] = {}
    create_fields: dict[str, Any] = {}
    update_fields: dict[str, Any] = {}

    for column in mapper.columns:
        py = _py_type(column)
        read_fields[column.key] = (py | None, None) if column.nullable else (py, ...)
        update_fields[column.key] = (py | None, None)
        if column.key in pk_names:
            continue
        if column.nullable or column.default is not None or column.server_default is not None:
            create_fields[column.key] = (py | None, None)
        else:
            create_fields[column.key] = (py, ...)

    config = ConfigDict(from_attributes=True)
    read = create_model(f"{name}Read", __config__=config, **read_fields)
    create = create_model(f"{name}Create", __config__=config, **create_fields)
    update = create_model(f"{name}Update", __config__=config, **update_fields)
    return read, create, update
