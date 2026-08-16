"""SYSTEM_USER management, kept out of the generic CRUD factory so that
password_hash is never serialized and passwords are always hashed on write."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.models import SystemUser
from app.auth.schemas import PasswordReset, SystemUserCreate, SystemUserRead
from app.core.crypto import hash_password
from app.core.permission import ADMIN, require_roles
from app.core.security import CurrentUser, db_session
from app.schemas.pagination import Page, PageParams
from app.service.audit_service import record_audit
from app.utils.query_filters import paginate

router = APIRouter(prefix="/system-users", tags=["administration"])


@router.get("", response_model=Page[SystemUserRead])
def list_users(
    params: PageParams = Depends(),
    db: Session = Depends(db_session),
    user: CurrentUser = Depends(require_roles(ADMIN)),
):
    page = paginate(db, SystemUser, params)
    page["items"] = [SystemUserRead.from_model(u) for u in page["items"]]
    return page


@router.post("", response_model=SystemUserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: SystemUserCreate,
    request: Request,
    db: Session = Depends(db_session),
    user: CurrentUser = Depends(require_roles(ADMIN)),
):
    """A user is either internal staff (provincial_office_id) or a taxpayer
    portal account (taxpayer_id) — exactly one, per the ERD's note in Sec. 14."""
    if bool(payload.provincial_office_id) == bool(payload.taxpayer_id):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Set exactly one of provincial_office_id or taxpayer_id",
        )
    obj = SystemUser(
        role_id=payload.role_id,
        username=payload.username,
        email=payload.email,
        provincial_office_id=payload.provincial_office_id,
        taxpayer_id=payload.taxpayer_id,
        password_hash=hash_password(payload.password),
        active=True,
    )
    db.add(obj)
    db.flush()
    record_audit(db, request=request, user_id=user.user_id, action="create",
                 entity_name="system_user", entity_id=obj.user_id)
    return SystemUserRead.from_model(obj)


@router.post("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    user_id: str,
    payload: PasswordReset,
    request: Request,
    db: Session = Depends(db_session),
    user: CurrentUser = Depends(require_roles(ADMIN)),
) -> None:
    obj = db.get(SystemUser, user_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "system_user not found")
    obj.password_hash = hash_password(payload.password)
    record_audit(db, request=request, user_id=user.user_id, action="password_reset",
                 entity_name="system_user", entity_id=user_id)
