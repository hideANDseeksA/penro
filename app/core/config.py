from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Camarines Norte Soil Depletion Tax System"
    ENV: str = "dev"

    # postgresql+psycopg://user:pw@host:5432/soiltax
    # mysql+pymysql://user:pw@host:3306/soiltax
    DATABASE_URL: str = "sqlite+pysqlite:///./soiltax.db"
    SQL_ECHO: bool = False

    # --- session cookie auth ---
    SECRET_KEY: str = "change-me-in-production"
    SESSION_COOKIE_NAME: str = "sdt_session"
    CSRF_COOKIE_NAME: str = "sdt_csrf"
    CSRF_HEADER_NAME: str = "X-CSRF-Token"
    SESSION_TTL_MINUTES: int = 60
    COOKIE_SECURE: bool = False       # True behind HTTPS
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: str | None = None

    # --- x-api-key ---
    API_KEY_HEADER: str = "X-API-Key"
    # "key:label:rate_per_minute" entries, comma separated
    API_KEYS: str = "dev-key-treasurer:treasurer-portal:120,dev-key-penro:penro-portal:60"

    # --- rate limiting ---
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 20
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5

    # --- CORS (comma separated origins for the portal front-end) ---
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # --- pagination ---
    PAGE_SIZE_DEFAULT: int = 25
    PAGE_SIZE_MAX: int = 200


    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
