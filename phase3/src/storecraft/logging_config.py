"""Structured logging configuration.

Emits one `key=value` line per log record; easy to parse with grep / jq-less
tools during local development while still being machine-readable.

Redacts any known secret-bearing keys (auth headers, passwords) defensively.
"""
from __future__ import annotations

import logging
import sys
from typing import Any

_REDACT_KEYS: frozenset[str] = frozenset(
    {"authorization", "cookie", "set-cookie", "password", "password_hash", "secret", "api_key", "token"}
)


def _redact(value: Any) -> Any:
    if isinstance(value, str) and len(value) > 4:
        return value[:2] + "…" + value[-2:]
    return "…"


class KeyValueFormatter(logging.Formatter):
    """Formatter that serializes log records as `key=value key2=value2 …`.

    Any `extra=` attributes attached to the record are surfaced at the top
    level; known secret keys are redacted.
    """

    _standard_fields: frozenset[str] = frozenset(
        {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message", "asctime", "taskName",
        }
    )

    def format(self, record: logging.LogRecord) -> str:
        pieces: list[str] = [
            f"ts={self.formatTime(record, '%Y-%m-%dT%H:%M:%S')}",
            f"level={record.levelname}",
            f"logger={record.name}",
        ]
        message = record.getMessage()
        # Quote the message so embedded spaces don't split it.
        pieces.append(f'msg="{message}"')

        # Surface extras
        for key, value in record.__dict__.items():
            if key in self._standard_fields or key.startswith("_"):
                continue
            if key.lower() in _REDACT_KEYS:
                value = _redact(value)
            pieces.append(f"{key}={value}")

        if record.exc_info:
            pieces.append(f'exc="{self.formatException(record.exc_info)}"')
        return " ".join(pieces)


def configure_logging(level: str = "INFO") -> None:
    """Idempotent — replace any existing handlers with our structured one."""
    root = logging.getLogger()
    root.setLevel(level.upper())
    # Remove prior handlers (pytest, uvicorn defaults) to avoid double emission.
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(KeyValueFormatter())
    root.addHandler(handler)
    # Silence the chatty sqlalchemy engine logger unless DEBUG.
    logging.getLogger("sqlalchemy.engine").setLevel("WARNING")
