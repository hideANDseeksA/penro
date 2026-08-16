"""Test bootstrap.

Points the app at a throwaway SQLite file and seeds it before anything imports
settings, so tests never touch a real PostgreSQL/MySQL database and never
inherit state between runs.
"""
from __future__ import annotations

import os
import tempfile

TEST_DB = os.path.join(tempfile.mkdtemp(prefix="soiltax-test-"), "test.db")
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{TEST_DB}"
os.environ["SEED_DEMO"] = "1"
os.environ["SEED_ADMIN_PASSWORD"] = "ChangeMeNow!2026"
os.environ.setdefault("RATE_LIMIT_DEFAULT_PER_MINUTE", "600")
# .env sets COOKIE_SECURE=true for the real HTTPS deployment. TestClient only
# ever talks plain http://, and httpx's cookie jar (correctly) refuses to
# resend a Secure cookie over http, so every authenticated request after
# login would silently lose its session cookie unless this is forced off.
os.environ["COOKIE_SECURE"] = "false"
# Tests hardcode the dev key below; don't depend on whatever key(s) happen to
# be configured in the developer's real .env.
os.environ["API_KEYS"] = "dev-key-treasurer:treasurer-portal:120,dev-key-penro:penro-portal:60"

import pytest  # noqa: E402

from app.core.database import Base, engine  # noqa: E402
from app.seed import main as seed_main  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def database() -> None:
    """Schema here comes from the models; `alembic upgrade head` is exercised
    separately in CI against PostgreSQL and MySQL."""
    Base.metadata.create_all(engine)
    seed_main()
