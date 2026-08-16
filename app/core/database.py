from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs(url: str) -> dict:
    kw: dict = {"echo": settings.SQL_ECHO, "future": True, "pool_pre_ping": True}
    if url.startswith("sqlite"):
        kw["connect_args"] = {"check_same_thread": False}
        kw.pop("pool_pre_ping")
    return kw


engine = create_engine(settings.DATABASE_URL, **_engine_kwargs(settings.DATABASE_URL))
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
