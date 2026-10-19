"""Alembic migration environment (async, asyncpg).

Reads ``DATABASE_URL`` from ``src/.env`` (or builds it from the app's
``POSTGRES_*`` settings) and exposes ``Base.metadata`` so ``--autogenerate``
can diff the models against a live database. Migrations run on an asyncio
event loop through the asyncpg driver, matching the application.

Every command runs from the repository root::

    alembic -c src/models/alembic.ini revision --autogenerate -m "message"
    alembic -c src/models/alembic.ini upgrade head
"""

from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

# The `alembic` console script is not launched from the repository root and is
# not a package inside `src`, so the repo root would otherwise be absent from
# sys.path. Without this, `from src.models...` below raises ModuleNotFoundError
# before any migration code runs.
_SRC_DIR = Path(__file__).resolve().parents[2]  # .../src
_PROJECT_ROOT = _SRC_DIR.parent  # repository root
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from src.models.dbSchemes.base import SQLAlchemyBase

# Importing the package registers all four models on Base.metadata, which is
# what autogenerate compares against. The names are referenced nowhere else.
from src.models.dbSchemes import Booking, Customer, Route, Trip  # noqa: E402,F401

# Alembic does not inject `config` into this module's namespace; the standard
# environment template aliases it from the running migration context.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# Resolve the .env beside main.py rather than wherever the command was run.
load_dotenv(_SRC_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    # Fall back to the application settings so migrations work straight from
    # the POSTGRES_* variables src/.env already holds.
    try:
        from src.helpers.config import get_settings

        s = get_settings()
        DATABASE_URL = (
            f"postgresql+asyncpg://{s.POSTGRES_USERNAME}:{s.POSTGRES_PASSWORD}"
            f"@{s.POSTGRES_HOST}:{s.POSTGRES_PORT}/{s.POSTGRES_DB}"
        )
    except Exception as exc:  # pragma: no cover - environment problem
        raise RuntimeError(
            "DATABASE_URL is not set, and no usable POSTGRES_* settings were "
            "found in src/.env. Add DATABASE_URL=... to src/.env, for example:\n"
            "    DATABASE_URL="
            "postgresql+asyncpg://postgres:postgres@localhost:5432/bus_booking"
        ) from exc

# The application is async, so the URL must name an async driver.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://", 1
    )
elif not DATABASE_URL.startswith("postgresql+asyncpg://"):
    raise RuntimeError(
        "DATABASE_URL must use the asyncpg dialect "
        "(postgresql+asyncpg://...), got: " + DATABASE_URL
    )

# compared by --autogenerate
target_metadata = SQLAlchemyBase.metadata


def _do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def _run_async_migrations() -> None:
    connectable = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations against a live database on an asyncio event loop."""
    asyncio.run(_run_async_migrations())


def run_migrations_offline() -> None:
    """Emit SQL to stdout without opening a database connection."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()