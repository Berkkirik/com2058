"""Runtime configuration sourced from environment variables.

Settings are loaded via pydantic-settings; any field can be overridden by an
environment variable of the same name. docker-compose.yml injects the important
ones at container startup.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven application settings.

    Values are read in priority order:
      1. Environment variables (docker compose injects these)
      2. `.env` file at the project root (development)
      3. Built-in defaults below (safe for local dev)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Database ──────────────────────────────────────────────────────────
    database_url: str = Field(
        default="mysql+pymysql://storecraft:storecraft@localhost:3307/storecraft?charset=utf8mb4",
        description="SQLAlchemy-style database URL.",
    )
    db_echo: bool = Field(default=False, description="Echo emitted SQL to stdout.")
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=10, ge=0, le=50)

    # ─── Application ───────────────────────────────────────────────────────
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000, ge=1, le=65535)
    app_secret_key: str = Field(
        default="dev-not-secret-change-me",
        description="Never use the default in production.",
    )
    app_debug: bool = Field(default=True)

    # ─── CORS ──────────────────────────────────────────────────────────────
    # Comma-separated list; keeps compose/.env ergonomics simple.
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Allowed origins for CORS. Use comma-separated list.",
    )

    # ─── Logging ───────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO")

    # ─── Seed / data fixtures ──────────────────────────────────────────────
    faker_seed: int = Field(default=42)
    seed_locale: str = Field(default="en_US")

    # ─── Helpers ───────────────────────────────────────────────────────────
    @field_validator("log_level")
    @classmethod
    def _upper_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(f"invalid log_level '{value}'")
        return normalized

    def cors_origins_list(self) -> list[str]:
        """Parse the comma-separated list into a real list. `*` means dev-open."""
        parts = [p.strip() for p in self.cors_origins.split(",") if p.strip()]
        return parts or ["*"]


@lru_cache
def get_settings() -> Settings:
    """Cached accessor — one Settings instance per process."""
    return Settings()


# Convenient module-level references
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SQL_DIR = PROJECT_ROOT / "sql"
