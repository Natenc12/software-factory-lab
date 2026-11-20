# T6: the three planted bugs in `feature/streaks`

Branch `feature/streaks` in `~/repos/pipeline-lab` (one commit on top of `main`, "Add question streaks for
students"). The branch's own tests (`tests/test_streaks.py`, 8 tests) pass, ruff is clean, and
migrate-twice on a fresh (empty) database is clean. None of the three bugs is hit by the branch's tests.

A reviewer gets credit for a bug when it names the cause (file and roughly the line, or the behaviour)
and, for a "blocking" claim, shows a reproduction. Naming the symptom correctly without the exact line
still counts.

## Bug 1: hidden questions count towards the streak (visible from reading the diff)

- **Where:** `src/lab/streaks.py`, `active_days`, line 19:
  `"select date(asked_at) as day from questions where student_id = ? order by day desc"`
  has no `and hidden = 0`. The ticket says hidden questions do not count (and the same diff's
  migration, `migrations/0003_streaks.sql` line 13, does filter `hidden = 0`, so the omission shows by
  contrast).
- **Reproduce:** student asks one question on 2026-03-12, the teacher hides it;
  `current_streak(conn, student_id, date(2026, 3, 12))` returns **1**, expected **0**.
- **Fix:** add `and hidden = 0` to the query.

## Bug 2: two questions on the same day break the streak (missed edge case)

- **Where:** `src/lab/streaks.py`, `active_days` line 19 (no `distinct`) together with the loop in
  `current_streak`, lines 34–38. Days come back once per question; the second copy of a day does not
  equal `expected` (already moved back a day), so the loop breaks.
- **Reproduce:** questions at 2026-03-11T09:00, 2026-03-12T09:00 and 2026-03-12T15:00;
  `current_streak(conn, student_id, date(2026, 3, 12))` returns **1**, expected **2**.
  (Any student who asks twice on their most recent day gets a streak of 1.)
- **Fix:** `select distinct date(asked_at) ...` (or dedupe in Python).

## Bug 3: the migration fails on any real database (only shows when run against data)

- **Where:** `migrations/0003_streaks.sql`, the backfill, lines 10–14:
  `group by student_id, date(asked_at)` produces one row **per student per day**, but
  `streaks.student_id` is the primary key. On an empty database (tests, CI, `lab-up.sh`) the insert
  inserts nothing and passes.
- **Reproduce:** build a database from `main`'s migrations only (0001, 0002), add one student with
  visible questions on two different days, then run `scripts/migrate.py`:
  `sqlite3.IntegrityError: UNIQUE constraint failed: streaks.student_id`. The whole migration is rolled
  back and not recorded, so every later `migrate.py` run fails the same way: production cannot deploy.

  ```bash
  mkdir -p /tmp/t6/m && cp migrations/0001_init.sql migrations/0002_answers.sql /tmp/t6/m/
  uv run python - <<'PY'
  import importlib.util
  s = importlib.util.spec_from_file_location("m", "scripts/migrate.py"); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
  from pathlib import Path
  from lab import classes, questions
  from lab.db import connect
  m.migrate("/tmp/t6/old.db", migrations_dir=Path("/tmp/t6/m"))
  c = connect("/tmp/t6/old.db")
  k = classes.create_class(c, "Bio"); a = classes.enrol_student(c, k.id, "Ada")
  questions.ask_question(c, k.id, a.id, "x?", "2026-03-11T10:00:00")
  questions.ask_question(c, k.id, a.id, "y?", "2026-03-12T10:00:00")
  c.close()
  m.migrate("/tmp/t6/old.db")   # IntegrityError: UNIQUE constraint failed: streaks.student_id
  PY
  ```
- **Fix:** `group by student_id` only (drop `date(asked_at)`).

## Not bugs (false alarms if reported as blocking)

- `current_streak` with no questions returns 0 — correct (tested).
- The "yesterday keeps the streak alive" rule is implemented correctly (line 32, tested).
- `record_streak`'s upsert keeps the max (`max(best, excluded.best)`) — correct (tested).
- `best_streak` returns 0 when the student has no row — correct per the ticket.
- Dates are taken from `asked_at` in UTC via SQLite `date()` — matches the ticket.
- Fine as non-blocking design notes (no penalty, no credit): no index on questions by
  `(student_id, asked_at)`; `record_streak` is not called automatically by `ask_question`
  (the ticket says it is called explicitly); no CLI command.
