"""Rate-limiting middleware and per-endpoint limiters."""
from __future__ import annotations

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.api_key import API_KEYS
from app.core.bucket import store
from app.core.config import settings

EXEMPT_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


def client_key(request: Request) -> tuple[str, int]:
    """Bucket key and budget: per API key when present, otherwise per IP."""
    api_key = request.headers.get(settings.API_KEY_HEADER)
    if api_key and api_key in API_KEYS:
        client = API_KEYS[api_key]
        return f"key:{client.label}", client.rate_per_minute
    ip = request.client.host if request.client else "unknown"
    return f"ip:{ip}", settings.RATE_LIMIT_DEFAULT_PER_MINUTE


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED or request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        key, rate = client_key(request)
        allowed, retry_after, remaining = store.hit(key, rate, settings.RATE_LIMIT_BURST)
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
                headers={
                    "Retry-After": str(max(1, int(retry_after + 0.999))),
                    "X-RateLimit-Limit": str(rate),
                    "X-RateLimit-Remaining": "0",
                },
            )
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


def login_rate_limit(request: Request) -> None:
    """Tighter per-IP limit on the login endpoint (credential stuffing)."""
    ip = request.client.host if request.client else "unknown"
    allowed, retry, _ = store.hit(f"login:{ip}", settings.RATE_LIMIT_LOGIN_PER_MINUTE, 0)
    if not allowed:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many login attempts",
            headers={"Retry-After": str(max(1, int(retry + 0.999)))},
        )
