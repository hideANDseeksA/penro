"""Password hashing and session-token signing.

pbkdf2-sha256 from the standard library, so there is no bcrypt/argon2 build
dependency to manage on the provincial server.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import secrets

import jwt

from app.core.config import settings

PBKDF2_ROUNDS = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ROUNDS).hex()
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, salt, digest = stored.split("$")
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    calc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(rounds)).hex()
    return hmac.compare_digest(calc, digest)


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def encode_session(claims: dict, ttl_minutes: int | None = None) -> str:
    ttl = ttl_minutes or settings.SESSION_TTL_MINUTES
    now = dt.datetime.now(dt.UTC)
    payload = {
        **claims,
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(minutes=ttl)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_session(token: str) -> dict:
    """Raises jwt.ExpiredSignatureError / jwt.InvalidTokenError."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a or "", b or "")
