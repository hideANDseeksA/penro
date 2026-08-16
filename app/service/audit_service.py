from __future__ import annotations

import json
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.auth.models import AuditLog


def record_audit(
    db: Session,
    *,
    request: Request | None,
    user_id: str | None,
    action: str,
    entity_name: str,
    entity_id: Any | None = None,
    details: dict | str | None = None,
) -> AuditLog:
    """Write one AUDIT_LOG row: who did what, to which record, from where."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_name=entity_name,
        entity_id=entity_id,
        details=details if isinstance(details, str) else json.dumps(details, default=str) if details else None,
        ip_address=(request.client.host if request and request.client else None),
    )
    db.add(log)
    db.flush()
    return log
