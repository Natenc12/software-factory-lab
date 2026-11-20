# Contract — issue #12 (copied verbatim from the issue body)

## Scope

**In:**

- `src/lab/streaks.py` with `current_streak`, `best_streak` and `record_streak`.
- A new migration adding a `streaks` table (best streak per student), with a backfill.
- Tests.

**Out:** Calling `record_streak` automatically from `ask_question`, showing streaks in the summary or
CLI, time zones other than UTC, and reminders or notifications.

## Decisions

- A day is the UTC calendar date of a question's `asked_at`.
- A day counts if the student asked at least one **visible** question on it. Several questions on one
  day count as one day. Hidden questions do not count.
- `current_streak(conn, student_id, today=None) -> int`: the number of consecutive counting days
  ending today. If the student has not asked anything today, a streak ending yesterday is still alive
  (count back from yesterday); otherwise it is 0. `today` defaults to the current UTC date. An unknown
  student raises `LookupError`.
- `best_streak(conn, student_id) -> int`: the stored best, or 0 if the student has no row yet.
- `record_streak(conn, student_id, today=None) -> int`: stores the current streak as the student's
  best if it is higher, and returns the best.
- Migration `0003`: a `streaks` table (`student_id` primary key, `best`, `updated_at`). Backfill: one
  row for every student who has asked at least one visible question, with `best` = 1; other students
  get their row on their first `record_streak`.

## Examples of done

(Today is 2026-03-12 unless stated.)
- Ada asked on Mar 10, 11 and 12 → `current_streak` = 3.
- Ada asked on Mar 10 and 11, nothing today → 2. Ada's only question was on Mar 9 → 0.
- Ben asked at Mar 11 09:00, Mar 12 09:00 and Mar 12 15:00 → 2.
- Cora's only question, on Mar 12, was hidden → 0.
- A student with no questions → `current_streak` 0 and `best_streak` 0.
- After the first example, `record_streak(..., today=Mar 12)` → 3; then
  `record_streak(..., today=Mar 20)` → still 3.
- A database with 0001 and 0002 applied and some history (Ada asked visible questions on Mar 9,
  Mar 11 and Mar 12; Ben asked nothing) → the migration script applies 0003; `streaks` has exactly
  one row (Ada, `best` 1); every existing row is still there; running the script again applies
  nothing.

## Must not change

- Migrations already applied (`0001_init.sql`, `0002_answers.sql`) are never edited.
- Existing rows in every table survive the migration unchanged.
- `ask_question` and every other existing function behave exactly as before.
- Every existing test passes unchanged.
