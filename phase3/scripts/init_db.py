"""Apply DDL files in order to a fresh database.

Used by:
  * docker-compose (mysql volume mount makes this optional — but useful for re-init)
  * tests (apply schema to a dedicated test database)
  * local development

Usage:
    python -m storecraft.scripts.init_db [--drop] [--sql-dir PATH]
"""
from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

from sqlalchemy import text

from storecraft.config import SQL_DIR
from storecraft.db import engine

log = logging.getLogger("storecraft.init_db")


def split_statements(sql_text: str) -> list[str]:
    """Split a SQL file into individual statements, honoring DELIMITER changes
    (used by trigger definitions).
    """
    stmts: list[str] = []
    buf: list[str] = []
    delimiter = ";"
    for raw_line in sql_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("--"):
            continue
        m = re.match(r"^DELIMITER\s+(\S+)", line, re.IGNORECASE)
        if m:
            if buf:
                stmts.append("\n".join(buf).strip())
                buf = []
            delimiter = m.group(1)
            continue
        if line.endswith(delimiter):
            buf.append(line[: -len(delimiter)])
            stmt = "\n".join(buf).strip()
            if stmt:
                stmts.append(stmt)
            buf = []
        else:
            buf.append(raw_line)
    if buf:
        stmt = "\n".join(buf).strip()
        if stmt:
            stmts.append(stmt)
    return stmts


def apply_sql_file(path: Path) -> int:
    sql = path.read_text(encoding="utf-8")
    statements = split_statements(sql)
    with engine.begin() as conn:
        for stmt in statements:
            if stmt:
                conn.execute(text(stmt))
    log.info("applied %s (%d statements)", path.name, len(statements))
    return len(statements)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--sql-dir", type=Path, default=SQL_DIR, help="Directory holding ordered SQL files")
    parser.add_argument("--drop", action="store_true", help="Drop all tables first")
    parser.add_argument("--pattern", default="0??_*.sql", help="Glob applied within sql-dir (default: 0??_*.sql)")
    args = parser.parse_args()

    if args.drop:
        log.warning("dropping all tables via foreign_key_checks=0 + DROP pattern")
        with engine.begin() as conn:
            conn.execute(text("SET foreign_key_checks = 0"))
            rows = conn.execute(text("SHOW TABLES")).fetchall()
            for (tbl,) in rows:
                conn.execute(text(f"DROP TABLE IF EXISTS `{tbl}`"))
            conn.execute(text("SET foreign_key_checks = 1"))

    files = sorted(args.sql_dir.glob(args.pattern))
    if not files:
        log.error("no SQL files matched %s/%s", args.sql_dir, args.pattern)
        raise SystemExit(1)
    total = 0
    for f in files:
        total += apply_sql_file(f)
    log.info("done — %d total statements applied across %d files", total, len(files))


if __name__ == "__main__":
    main()
