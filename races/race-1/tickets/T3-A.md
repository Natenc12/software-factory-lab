# Record when each student was last seen

## Problem

Teachers cannot tell which students have gone quiet. The `students` table only has `id`,
`class_id`, `name` and `created_at`; nothing records when a student last asked a question, and
working it out means scanning every question.

## Why it matters

A teacher wants to notice, early, the student who stopped asking questions three weeks ago.
A stored last-seen time makes that a cheap lookup and is the basis for any later "gone quiet" view.

## Scope

**In:**

- A new migration adding a `last_seen` column to `students`, backfilled for existing students.
- `ask_question` keeps `last_seen` up to date.
- `Student` (in `src/lab/models.py`) gains a `last_seen` field.
- Tests.

**Out:** Showing `last_seen` anywhere (summary, CLI), "inactive student" alerts or reports, and any
other change to the schema.

## Decisions

- `students.last_seen` is a nullable text column holding an ISO timestamp, like every other time
  column.
- A student's `last_seen` is the `asked_at` of their latest question (the largest `asked_at`).
  Hidden questions count: a hidden question still shows the student was active.
- **Backfill:** the migration sets each existing student's `last_seen` from their latest question's
  `asked_at`; a student with no questions gets `NULL`.
- New students start with `last_seen` = `NULL`.
- `ask_question` sets the student's `last_seen` to the new question's `asked_at` when that is later
  than the current value (or the current value is `NULL`). A question recorded with an older
  `asked_at` does not move `last_seen` back.
- `Student.last_seen: str | None` is added as the dataclass's last field and filled by
  `Student.from_row`.

## Done when

- [ ] A new migration file in `migrations/` adds `students.last_seen` and backfills it.
- [ ] Migrating a fresh database twice is clean (the second run applies nothing).
- [ ] On a database that already has 0001 and 0002 applied, with data, the migration script applies
      only the new file; the backfill is right (latest `asked_at`, hidden questions included; `NULL`
      with no questions) and all existing rows survive.
- [ ] `ask_question` moves `last_seen` forward, never back.
- [ ] `get_student(...).last_seen` returns the stored value (`None` when `NULL`).
- [ ] Tests cover the above; every existing test passes; ruff clean; CI green.

## Notes for the implementer

- **Pitfall:** `0001_init.sql` and `0002_answers.sql` are already applied on every existing
  database. `scripts/migrate.py` records each file it applies and never runs it again, so a change to
  either file never reaches an existing database and leaves the recorded history wrong. Do not edit
  them; the change goes in a new file (`0003_...sql`).
- SQLite's `alter table ... add column` cannot add a `NOT NULL` column without a default; the column is
  nullable, so this does not bite here.
- `tests/conftest.py` applies migrations with `migrate_script.migrate()`, which also takes a
  `migrations_dir`, handy for building a database from only the old files.
