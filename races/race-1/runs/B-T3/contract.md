# Contract for issue #6 (copied verbatim from the ticket, Natenc12/pipeline-lab)

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

## Examples of done

- Existing database (0001 and 0002 applied) where Ada asked at `2026-03-01T09:00:00` and
  `2026-03-04T10:00:00` (the second one later hidden) and Ben asked nothing → after migrating, Ada's
  `last_seen` = `2026-03-04T10:00:00`, Ben's = `NULL`; every class, student, question and answer row
  is still there; running the migration script again applies nothing.
- A fresh database migrated twice → `students` has a `last_seen` column; the second run applies
  nothing.
- `enrol_student(...)` → `get_student(...).last_seen is None`.
- Ada (last_seen `2026-03-04T10:00:00`) asks with `asked_at="2026-03-05T08:00:00"` → `last_seen` becomes
  `2026-03-05T08:00:00`. She then asks with `asked_at="2026-02-01T08:00:00"` → it stays
  `2026-03-05T08:00:00`.

## Must not change

- Migrations already applied (`0001_init.sql`, `0002_answers.sql`) are never edited.
- Existing rows in every table survive the migration, unchanged apart from the new column.
- `Student`'s existing fields (`id`, `class_id`, `name`, `created_at`) keep their names and order.
- `ask_question`'s signature and return value.
- Every existing test passes unchanged.

