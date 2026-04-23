"""SQLAlchemy engine + session factory.

Exposes:
  - `engine`: the SQLAlchemy Engine (reused across the process)
  - `SessionLocal`: sessionmaker (call to get a Session)
  - `get_db()`: FastAPI dependency yielding a Session with explicit close
  - `Base`: declarative base for ORM models (shared across models/ modules)

The connection URL is read from Settings.database_url; pool sizing follows
defaults suitable for a small demo app but scales up via .env overrides.
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    """Single declarative base shared by every ORM model module."""


_settings = get_settings()

# SQLite (used in unit tests) doesn't accept pool_size/max_overflow; omit for it.
_engine_kwargs: dict = {
    "echo": _settings.db_echo,
    "pool_pre_ping": True,
    "future": True,
}
if not _settings.database_url.startswith("sqlite"):
    _engine_kwargs["pool_size"] = _settings.db_pool_size
    _engine_kwargs["max_overflow"] = _settings.db_max_overflow

engine = create_engine(_settings.database_url, **_engine_kwargs)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a session, closes it after the request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
