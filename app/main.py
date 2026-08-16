"""Camarines Norte Soil Depletion Tax System — application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import api_router
from app.utils.rate_limiter import RateLimitMiddleware

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "Administers the Camarines Norte Soil Depletion Tax Ordinance of 2026: taxpayer "
        "registration, shipments, assessment and payment, clearances, quarterly returns, "
        "remedies, violations, monitoring and audit.\n\n"
        "**Auth:** every request needs an `X-API-Key` header; every request except "
        "`/api/v1/auth/login` and `/health` also needs the session cookie set by login, "
        "and writes must echo the CSRF cookie in `X-CSRF-Token`.\n\n"
        "This is a fiscal and provincial revenue measure only — it does not regulate "
        "mining and does not affect national permits (Sec. 3e, Sec. 9c)."
    ),
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,  # required for the session cookie
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"],
)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}


app.include_router(api_router)
