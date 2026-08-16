"""Authentication request/response schemas."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.auth.models import SystemUser


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    username: str
    role: str
    csrf_token: str
    expires_in: int


class SystemUserRead(BaseModel):
    user_id: str
    role_id: str
    provincial_office_id: str | None = None
    taxpayer_id: str | None = None
    username: str
    email: str | None = None
    active: bool

    @classmethod
    def from_model(cls, u: SystemUser) -> "SystemUserRead":
        return cls(
            user_id=str(u.user_id),
            role_id=str(u.role_id),
            provincial_office_id=str(u.provincial_office_id) if u.provincial_office_id else None,
            taxpayer_id=str(u.taxpayer_id) if u.taxpayer_id else None,
            username=u.username,
            email=u.email,
            active=u.active,
        )


class SystemUserCreate(BaseModel):
    role_id: str
    username: str
    password: str = Field(min_length=12)
    email: EmailStr | None = None
    provincial_office_id: str | None = None
    taxpayer_id: str | None = None


class PasswordReset(BaseModel):
    password: str = Field(min_length=12)
