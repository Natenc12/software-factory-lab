"""Hidden tests for T3 (students.last_seen). Copied into the lab's tests/ folder."""

import shutil

from conftest import migrate_script

from lab import classes, questions
from lab.db import connect

OLD = ["0001_init.sql", "0002_answers.sql"]


def columns(conn, table):
    return {row["name"] for row in conn.execute(f"pragma table_info({table})")}


def last_seen(conn, student_id):
    return conn.execute("select last_seen from students where id = ?", (student_id,)).fetchone()[0]


def build_old_database(tmp_path):
    """A database with only 0001 and 0002 applied and some data in every table."""
    old_dir = tmp_path / "old_migrations"
    old_dir.mkdir()
    for name in OLD:
        shutil.copy(migrate_script.MIGRATIONS_DIR / name, old_dir / name)
    path = tmp_path / "old.db"
    assert migrate_script.migrate(str(path), migrations_dir=old_dir) == OLD
    # Raw SQL: the app's own functions expect the new schema, the database has the old one.
    conn = connect(path)
    sql = conn.execute
    sql("insert into classes (id, name, material, created_at) values (1, 'Biology', 'DNA.', 't')")
    sql("insert into classes (id, name, material, created_at) values (2, 'Art', 'Blue.', 't')")
    for sid, cid, name in ((1, 1, "Ada"), (2, 1, "Ben"), (3, 2, "Cara")):
        sql(
            "insert into students (id, class_id, name, created_at) values (?, ?, ?, 't')",
            (sid, cid, name),
        )
    for qid, cid, sid, text, hidden, at in (
        (1, 1, 1, "What is DNA?", 0, "2026-03-01T09:00:00"),
        (2, 1, 1, "What is RNA?", 1, "2026-03-04T10:00:00"),
        (3, 1, 1, "Older?", 0, "2026-02-01T10:00:00"),
        (4, 2, 3, "What is blue?", 0, "2026-03-02T11:30:00"),
    ):
        sql(
            "insert into questions (id, class_id, student_id, text, hidden, asked_at)"
            " values (?, ?, ?, ?, ?, ?)",
            (qid, cid, sid, text, hidden, at),
        )
    sql("insert into answers (question_id, body, provider, created_at) values (1, 'x', 'f', 't')")
    sql("insert into jobs (kind, payload, created_at, updated_at) values ('a', '{}', 't', 't')")
    conn.commit()
    snapshot = {}
    for t in ("classes", "students", "questions", "answers", "jobs"):
        rows = conn.execute(f"select * from {t} order by id").fetchall()
        snapshot[t] = (list(rows[0].keys()), [tuple(r) for r in rows])
    conn.close()
    return path, snapshot, {"ada": 1, "ben": 2, "cara": 3}


def test_t3_fresh_database_has_last_seen(conn):
    assert "last_seen" in columns(conn, "students")


def test_t3_migrate_twice_on_fresh_database(db_path):
    assert migrate_script.migrate() == []


def test_t3_existing_database_backfill_and_data_survive(tmp_path, db_path):
    path, before, ids = build_old_database(tmp_path)
    applied = migrate_script.migrate(str(path))
    assert applied, "the new migration should apply to an existing database"
    assert not set(applied) & set(OLD)
    assert migrate_script.migrate(str(path)) == []

    conn = connect(path)
    assert last_seen(conn, ids["ada"]) == "2026-03-04T10:00:00"  # hidden question counts
    assert last_seen(conn, ids["ben"]) is None
    assert last_seen(conn, ids["cara"]) == "2026-03-02T11:30:00"
    for table, (cols, rows) in before.items():
        after = conn.execute(f"select * from {table} order by id").fetchall()
        assert [tuple(r[k] for k in cols) for r in after] == rows, table
    conn.close()


def test_t3_new_student_starts_null(conn, biology):
    _, ada, _ = biology
    assert classes.get_student(conn, ada.id).last_seen is None
    assert last_seen(conn, ada.id) is None


def test_t3_ask_question_moves_last_seen_forward_never_back(conn, biology):
    klass, ada, ben = biology
    questions.ask_question(conn, klass.id, ada.id, "One?", "2026-03-04T10:00:00")
    assert classes.get_student(conn, ada.id).last_seen == "2026-03-04T10:00:00"
    questions.ask_question(conn, klass.id, ada.id, "Two?", "2026-03-05T08:00:00")
    assert classes.get_student(conn, ada.id).last_seen == "2026-03-05T08:00:00"
    questions.ask_question(conn, klass.id, ada.id, "Three?", "2026-02-01T08:00:00")
    assert classes.get_student(conn, ada.id).last_seen == "2026-03-05T08:00:00"
    assert classes.get_student(conn, ben.id).last_seen is None


def test_t3_default_asked_at_sets_last_seen(conn, biology):
    klass, ada, _ = biology
    q = questions.ask_question(conn, klass.id, ada.id, "Now?")
    assert classes.get_student(conn, ada.id).last_seen == q.asked_at


def test_t3_student_model_keeps_existing_fields_first(conn, biology):
    _, ada, _ = biology
    s = classes.get_student(conn, ada.id)
    assert (s.id, s.class_id, s.name) == (ada.id, ada.class_id, "Ada")
    assert list(s.__dataclass_fields__)[:4] == ["id", "class_id", "name", "created_at"]
    assert list(s.__dataclass_fields__)[-1] == "last_seen"


def test_t3_old_migrations_untouched_in_schema_record(conn):
    names = [r["name"] for r in conn.execute("select name from schema_migrations order by name")]
    assert names[:2] == OLD
    assert len(names) >= 3


def test_t3_last_seen_is_nullable_text(conn):
    info = {row["name"]: row for row in conn.execute("pragma table_info(students)")}
    assert info["last_seen"]["notnull"] == 0
