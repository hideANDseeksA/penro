"""Cookie-based session security.

Login sets two cookies:
  * `sdt_session` — HttpOnly signed JWT, never readable by JavaScript.
  * `sdt_csrf`    — readable, echoed back in `X-CSRF-Token` on every write.

Both must line up for a POST/PATCH/DELETE to be accepted (double-submit CSRF).
"""
from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import Role, SystemUser
from app.core.config import settings
from app.core.crypto import (
    constant_time_equals,
    decode_session,
    encode_session,
    new_csrf_token,
    verify_password,
)
from app.core.database import get_db

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


@dataclass
class CurrentUser:
    user_id: str
    username: str
    role: str
    taxpayer_id: str | None
    office_id: str | None


def issue_session(response: Response, user: SystemUser, role_name: str) -> str:
    csrf = new_csrf_token()
    token = encode_session({
        "sub": str(user.user_id),
        "username": user.username,
        "role": role_name,
        "taxpayer_id": str(user.taxpayer_id) if user.taxpayer_id else None,
        "office_id": str(user.provincial_office_id) if user.provincial_office_id else None,
        "csrf": csrf,
    })
    common = dict(
        max_age=settings.SESSION_TTL_MINUTES * 60,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )
    response.set_cookie(settings.SESSION_COOKIE_NAME, token, httponly=True, **common)
    response.set_cookie(settings.CSRF_COOKIE_NAME, csrf, httponly=False, **common)
    return csrf


def clear_session(response: Response) -> None:
    for name in (settings.SESSION_COOKIE_NAME, settings.CSRF_COOKIE_NAME):
        response.delete_cookie(name, path="/", domain=settings.COOKIE_DOMAIN)


def get_current_user(
    request: Request,
    # A plain request.headers.get(...) read is invisible to FastAPI's OpenAPI
    # generation, so Swagger UI rendered no input for it at all on write
    # endpoints -- there was no way to supply the token through /docs.
    # Declaring it as a Header() parameter makes it a documented, fillable
    # field. It's optional here because it's only required for unsafe
    # methods, checked below.
    x_csrf_token: str | None = Header(default=None, alias=settings.CSRF_HEADER_NAME),
) -> CurrentUser:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing session cookie")
    try:
        claims = decode_session(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired") from None
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session") from None

    if request.method not in SAFE_METHODS:
        if not constant_time_equals(x_csrf_token, claims.get("csrf", "")):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF token missing or invalid")

    user = CurrentUser(
        user_id=claims["sub"],
        username=claims["username"],
        role=claims["role"],
        taxpayer_id=claims.get("taxpayer_id"),
        office_id=claims.get("office_id"),
    )
    request.state.current_user = user
    return user


def authenticate_user(db: Session, username: str, password: str) -> tuple[SystemUser, str] | None:
    user = db.scalar(
        select(SystemUser).where(SystemUser.username == username, SystemUser.active.is_(True))
    )
    if user is None or not verify_password(password, user.password_hash):
        return None
    role_name = db.scalar(select(Role.role_name).where(Role.role_id == user.role_id)) or "Unknown"
    return user, role_name


def db_session(db: Session = Depends(get_db)) -> Session:
    return db
