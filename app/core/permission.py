"""Role-based authorization.

Role names come from ROLE.role_name: Admin, Treasurer Staff, PENRO Staff,
PMRB Staff, Legal Office, Taxpayer. The office split follows the ordinance —
assessment and collection sit with the Treasurer (Sec. 8, 11), monitoring with
PENRO (Sec. 10), remedies and enforcement with the Legal Office (Sec. 13, 15).
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.core.security import CurrentUser, get_current_user

ADMIN = "Admin"
TREASURER_STAFF = "Treasurer Staff"
PENRO_STAFF = "PENRO Staff"
PMRB_STAFF = "PMRB Staff"
LEGAL_OFFICE = "Legal Office"
TAXPAYER = "Taxpayer"

TREASURY = (ADMIN, TREASURER_STAFF)
MONITORING = (ADMIN, TREASURER_STAFF, PENRO_STAFF)
ENFORCEMENT = (ADMIN, TREASURER_STAFF, LEGAL_OFFICE)


def require_roles(*roles: str):
    """Dependency factory restricting an endpoint to the given roles."""

    def _dep(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requires role: {', '.join(roles)}")
        return user

    return _dep


def owns_taxpayer_record(user: CurrentUser, taxpayer_id) -> bool:
    """Portal users only ever act on their own taxpayer's records."""
    if user.role != TAXPAYER:
        return True
    return user.taxpayer_id is not None and str(taxpayer_id) == user.taxpayer_id
