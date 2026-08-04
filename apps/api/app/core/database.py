from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    url = get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, future=True, pool_pre_ping=True, connect_args=connect_args)

    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _fk(dbapi_connection, _):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_columns() -> None:
    """Ajustes leves de schema sem Alembic (MVP). create_all não altera tabelas existentes."""
    insp = inspect(engine)
    dialect = engine.dialect.name
    with engine.begin() as conn:
        if "app_settings" in insp.get_table_names():
            cols = {c["name"] for c in insp.get_columns("app_settings")}
            if "crypto_key_fp" not in cols:
                conn.execute(text("ALTER TABLE app_settings ADD COLUMN crypto_key_fp VARCHAR(16)"))
        if "acs_servers" in insp.get_table_names() and dialect == "postgresql":
            # Bearer NBI opcional
            conn.execute(text("ALTER TABLE acs_servers ALTER COLUMN bearer_token_encrypted DROP NOT NULL"))


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_columns()
