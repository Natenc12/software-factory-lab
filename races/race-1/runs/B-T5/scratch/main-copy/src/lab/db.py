"""Opening the SQLite database. Standard library only."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PATH = "./lab.db"


def db_path(path: str | os.PathLike | None = None) -> str:
    """The path to use: the argument if given, else $LAB_DB, else ./lab.db."""
    if path is not None:
        return str(path)
    return os.environ.get("LAB_DB") or DEFAULT_PATH


def connect(path: str | os.PathLike | None = None) -> sqlite3.Connection:
    """Open the database with rows readable by column name and foreign keys enforced."""
    target = db_path(path)
    if target != ":memory:":
        Path(target).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma foreign_keys = on")
    return conn


def now() -> str:
    """The current UTC time as an ISO 8601 string, the format every timestamp column uses."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
