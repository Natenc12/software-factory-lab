"""Every test gets its own empty SQLite file with the real migrations applied.

The migrations are applied by scripts/migrate.py's own `migrate()` function, the same code CI
and developers run, so the tests always see the schema the migrations actually produce.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from lab import classes
from lab.db import connect

ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location("migrate", ROOT / "scripts" / "migrate.py")
migrate_script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migrate_script)


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "lab.db"
    monkeypatch.setenv("LAB_DB", str(path))
    migrate_script.migrate()
    return path


@pytest.fixture
def conn(db_path):
    connection = connect()
    yield connection
    connection.close()


@pytest.fixture
def biology(conn):
    """A class with material and two enrolled students."""
    klass = classes.create_class(
        conn,
        "Biology",
        "Mitochondria produce energy for the cell. "
        "Photosynthesis turns sunlight into sugar in plants. "
        "DNA carries genetic information.",
    )
    ada = classes.enrol_student(conn, klass.id, "Ada")
    ben = classes.enrol_student(conn, klass.id, "Ben")
    return klass, ada, ben
