import sqlite3

import pytest
from conftest import migrate_script

from lab.db import DEFAULT_PATH, connect, db_path


def tables(conn):
    rows = conn.execute("select name from sqlite_master where type = 'table'").fetchall()
    return {row["name"] for row in rows}


def test_db_path_prefers_argument_then_env_then_default(monkeypatch):
    monkeypatch.setenv("LAB_DB", "/tmp/from-env.db")
    assert db_path("given.db") == "given.db"
    assert db_path() == "/tmp/from-env.db"
    monkeypatch.delenv("LAB_DB")
    assert db_path() == DEFAULT_PATH == "./lab.db"


def test_connect_uses_lab_db_env(db_path):
    conn = connect()
    assert "classes" in tables(conn)
    conn.close()


def test_rows_are_readable_by_name(conn):
    row = conn.execute("select 1 as one").fetchone()
    assert row["one"] == 1


def test_foreign_keys_are_enforced(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("insert into students (class_id, name, created_at) values (999, 'x', 'now')")


def test_migrations_create_every_table(conn):
    assert {"schema_migrations", "classes", "students", "questions", "answers", "jobs"} <= tables(
        conn
    )


def test_students_table_columns(conn):
    columns = {row["name"] for row in conn.execute("pragma table_info(students)")}
    assert {"id", "class_id", "name", "created_at"} <= columns


def test_applied_migrations_are_recorded_in_order(conn):
    names = [r["name"] for r in conn.execute("select name from schema_migrations order by name")]
    files = sorted(f.name for f in migrate_script.MIGRATIONS_DIR.glob("*.sql"))
    assert names == files
    assert names[:2] == ["0001_init.sql", "0002_answers.sql"]


def test_migrate_twice_applies_nothing_and_keeps_data(db_path, conn):
    conn.execute("insert into classes (name, created_at) values ('Kept', 'now')")
    conn.commit()
    assert migrate_script.migrate() == []
    assert conn.execute("select name from classes").fetchone()["name"] == "Kept"


def test_migrate_applies_only_new_files(tmp_path, db_path):
    extra = tmp_path / "migrations"
    extra.mkdir()
    for file in sorted(migrate_script.MIGRATIONS_DIR.glob("*.sql")):
        (extra / file.name).write_text(file.read_text())
    (extra / "0003_notes.sql").write_text("create table notes (id integer primary key);")
    assert migrate_script.migrate(migrations_dir=extra) == ["0003_notes.sql"]
    assert migrate_script.migrate(migrations_dir=extra) == []


def test_failed_migration_is_rolled_back_and_not_recorded(tmp_path, db_path):
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "0003_bad.sql").write_text("create table half (id integer); select * from nowhere;")
    with pytest.raises(sqlite3.OperationalError):
        migrate_script.migrate(migrations_dir=bad)
    conn = connect()
    assert "half" not in tables(conn)
    recorded = {r["name"] for r in conn.execute("select name from schema_migrations")}
    assert "0003_bad.sql" not in recorded
    conn.close()


def test_migrate_main_reports(db_path, capsys):
    assert migrate_script.main() == 0
    assert capsys.readouterr().out.strip() == "nothing to apply"
