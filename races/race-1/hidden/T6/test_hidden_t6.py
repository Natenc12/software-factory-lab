"""Hidden checks for T6: one test per planted bug in feature/streaks (see answers/T6-bugs.md).

Not used to grade a reviewer directly; they prove the bugs exist on the branch (all three fail
there) and pass once the bugs are fixed. Copied into the lab's tests/ folder; uses its conftest.
"""

import shutil
from datetime import date

from conftest import migrate_script
from lab.streaks import current_streak

from lab import classes, questions
from lab.db import connect

TODAY = date(2026, 3, 12)


def test_t6_bug1_hidden_questions_do_not_count(conn, biology):
    klass, ada, _ = biology
    q = questions.ask_question(conn, klass.id, ada.id, "x?", "2026-03-12T10:00:00")
    questions.hide_question(conn, q.id)
    assert current_streak(conn, ada.id, TODAY) == 0


def test_t6_bug2_several_questions_one_day_count_once(conn, biology):
    klass, _, ben = biology
    for t in ("2026-03-11T09:00:00", "2026-03-12T09:00:00", "2026-03-12T15:00:00"):
        questions.ask_question(conn, klass.id, ben.id, "y?", t)
    assert current_streak(conn, ben.id, TODAY) == 2


def test_t6_bug3_migration_applies_on_existing_data(tmp_path, db_path):
    old = tmp_path / "old"
    old.mkdir()
    for name in ("0001_init.sql", "0002_answers.sql"):
        shutil.copy(migrate_script.MIGRATIONS_DIR / name, old / name)
    path = tmp_path / "old.db"
    migrate_script.migrate(str(path), migrations_dir=old)
    c = connect(path)
    k = classes.create_class(c, "Bio")
    ada = classes.enrol_student(c, k.id, "Ada")
    classes.enrol_student(c, k.id, "Ben")
    for t in ("2026-03-09T10:00:00", "2026-03-11T10:00:00", "2026-03-12T10:00:00"):
        questions.ask_question(c, k.id, ada.id, "z?", t)
    c.close()
    assert migrate_script.migrate(str(path))
    assert migrate_script.migrate(str(path)) == []
    c = connect(path)
    rows = [tuple(r) for r in c.execute("select student_id, best from streaks")]
    c.close()
    assert rows == [(ada.id, 1)]
