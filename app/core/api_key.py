"""X-API-Key enforcement.

Keys are configured as `key:label:requests_per_minute`, so the treasurer
portal, a PENRO client and a batch integration can each carry their own rate
budget. Rotate by editing API_KEYS and restarting; move to a keys table if the
Province needs self-service rotation.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings


@dataclass(frozen=True)
class ApiClient:
    key: str
    label: str
    rate_per_minute: int


def load_api_keys() -> dict[str, ApiClient]:
    clients: dict[str, ApiClient] = {}
    for raw in settings.API_KEYS.split(","):
        raw = raw.strip()
        if not raw:
            continue
        parts = raw.split(":")
        key = parts[0]
        label = parts[1] if len(parts) > 1 else "unnamed"
        rate = int(parts[2]) if len(parts) > 2 else settings.RATE_LIMIT_DEFAULT_PER_MINUTE
        clients[key] = ApiClient(key=key, label=label, rate_per_minute=rate)
    return clients


API_KEYS: dict[str, ApiClient] = load_api_keys()

# A plain `request.headers.get(...)` dependency is invisible to FastAPI's
# OpenAPI generation, so Swagger UI has no "Authorize" button and no field to
# enter the key into. APIKeyHeader is a proper SecurityBase scheme, so it gets
# registered in components.securitySchemes and shows up as an Authorize
# option. auto_error=False keeps the existing 401 (not FastAPI's default 403)
# and message on a missing header.
_api_key_scheme = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


def require_api_key(request: Request, provided: str | None = Security(_api_key_scheme)) -> ApiClient:
    if not provided:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Missing {settings.API_KEY_HEADER} header")
    client = API_KEYS.get(provided)
    if client is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
    request.state.api_client = client
    return client
