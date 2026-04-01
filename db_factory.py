"""
Database handler factory.

Resolution strategy:
1) Default/unset backend is PostgreSQL (strict).
2) If DB_BACKEND is postgres/postgresql -> use PostgreSQL only.
3) If DB_BACKEND is sqlite -> use SQLite only (local fallback/dev only).
"""

import os

from database_sqlite import DatabaseHandler as SQLiteHandler

try:
    from database import DatabaseHandler as PostgresHandler
except Exception:
    PostgresHandler = None


def get_handler(*args, **kwargs):
    """Return a database handler instance based on environment/backend availability."""
    backend = os.getenv("DB_BACKEND", "postgres").strip().lower()

    if backend == "sqlite":
        db_path = kwargs.pop("db_path", os.getenv("SQLITE_DB_PATH", "travel_advisories.db"))
        return SQLiteHandler(db_path=db_path)

    if backend not in {"postgres", "postgresql"}:
        raise RuntimeError(f"Unsupported DB_BACKEND='{backend}'. Use 'postgres' or 'sqlite'.")

    if PostgresHandler is None:
        raise RuntimeError(
            "PostgreSQL backend requested but driver/handler is unavailable. "
            "Install dependencies (e.g. psycopg2-binary) and verify DB settings."
        )

    return PostgresHandler(*args, **kwargs)
