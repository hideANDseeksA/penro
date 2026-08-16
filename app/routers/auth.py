from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    CurrentUser,
    authenticate_user,
    clear_session,
    db_session,
    get_current_user,
    issue_session,
)
from app.service.audit_service import record_audit
from app.utils.rate_limiter import login_rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    username: str
    role: str
    csrf_token: str
    expires_in: int


@router.post("/login", response_model=LoginResponse, dependencies=[Depends(login_rate_limit)])
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(db_session),
) -> LoginResponse:
    """Sets an HttpOnly session cookie plus a readable CSRF cookie.

    The CSRF value must be echoed in the `X-CSRF-Token` header on every
    POST/PATCH/DELETE; the session cookie alone is not sufficient.
    """
    result = authenticate_user(db, payload.username, payload.password)
    if result is None:
        record_audit(db, request=request, user_id=None, action="login_failed",
                     entity_name="system_user", details={"username": payload.username})
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")

    user, role_name = result
    csrf = issue_session(response, user, role_name)
    user.last_login = dt.date.today()
    record_audit(db, request=request, user_id=str(user.user_id), action="login",
                 entity_name="system_user", entity_id=user.user_id)
    return LoginResponse(
        username=user.username,
        role=role_name,
        csrf_token=csrf,
        expires_in=settings.SESSION_TTL_MINUTES * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
) -> None:
    record_audit(db, request=request, user_id=user.user_id, action="logout", entity_name="system_user")
    clear_session(response)


@router.get("/me", response_model=CurrentUser | None)
def me(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return user
