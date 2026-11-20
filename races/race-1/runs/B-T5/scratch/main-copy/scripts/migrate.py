"""Apply pending migrations/*.sql to the database at $LAB_DB (default ./lab.db).

Each file runs once, in name order, inside its own transaction, and its name is recorded in
`schema_migrations`. Running the script again applies nothing new, so it is safe to re-run.

    uv run python scripts/migrate.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from lab.db import connect, now

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"

CREATE_TABLE = """
create table if not exists schema_migrations (
    name text primary key,
    applied_at text not null
)
"""


def applied_names(conn: sqlite3.Connection) -> set[str]:
    return {row["name"] for row in conn.execute("select name from schema_migrations")}


def migrate(path: str | None = None, migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply every migration not yet recorded. Returns the names applied this run."""
    conn = connect(path)
    try:
        conn.execute(CREATE_TABLE)
        conn.commit()
        done = applied_names(conn)
        applied = []
        for file in sorted(migrations_dir.glob("*.sql")):
            if file.name in done:
                continue
            record = (
                "insert into schema_migrations (name, applied_at) values ("
                + quote(file.name)
                + ", "
                + quote(now())
                + ");"
            )
            script = "begin;\n" + file.read_text(encoding="utf-8") + "\n" + record + "\ncommit;"
            try:
                conn.executescript(script)
            except sqlite3.Error:
                conn.rollback()
                raise
            applied.append(file.name)
        return applied
    finally:
        conn.close()


def quote(value: str) -> str:
    """A SQL string literal. Only used for file names and timestamps we produce ourselves."""
    return "'" + value.replace("'", "''") + "'"


def main() -> int:
    applied = migrate()
    if applied:
        for name in applied:
            print(f"applied {name}")
    else:
        print("nothing to apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
