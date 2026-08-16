from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.database import Base
import app.models  # noqa: F401  (registers all tables on Base.metadata)

config = context.config
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL.replace("%", "%%"),
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def render_item(type_, obj, autogen_context):
    """Emit the portable GUID type in generated migrations instead of the
    dialect-specific type it resolved to at autogenerate time."""
    if type_ == "type" and obj.__class__.__name__ == "GUID":
        autogen_context.imports.add("import app.core.types")
        return "app.core.types.GUID()"
    return False


def _common_kwargs() -> dict:
    return {
        "target_metadata": target_metadata,
        "compare_type": True,
        "compare_server_default": True,
        "render_item": render_item,
        # SQLite (used for local tests) cannot ALTER; batch mode makes the same
        # migration script work there as well as on MySQL/PostgreSQL.
        "render_as_batch": settings.DATABASE_URL.startswith("sqlite") and not os.getenv("ALEMBIC_NO_BATCH"),
    }


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **_common_kwargs(),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        kwargs = _common_kwargs()
        if connection.dialect.name == "mysql":
            # InnoDB + utf8mb4 so FKs and Filipino/Unicode names behave.
            kwargs["dialect_opts"] = {"paramstyle": "named"}
        context.configure(connection=connection, **kwargs)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
