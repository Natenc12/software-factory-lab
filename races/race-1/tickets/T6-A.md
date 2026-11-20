# Show each student's question streak

## Problem

Teachers want to encourage regular practice: a student who asks something every day is
building a habit. Study Buddy has no idea of a streak: how many days in a row a student has asked a
question, or the best run they have had.

## Why it matters

A visible streak is a cheap nudge that keeps students coming back daily, and it lets a teacher
spot the students whose habit just broke.

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

## Done when

- [ ] Three consecutive days ending today give a streak of 3; a missed day ends the streak.
- [ ] A streak ending yesterday still counts; one ending earlier is 0.
- [ ] Several questions on one day count as one day; hidden questions do not count.
- [ ] `best_streak` is 0 with no row; `record_streak` keeps the highest value.
- [ ] The migration applies cleanly on an existing database with data, the backfill is as decided,
      and migrating twice is clean.
- [ ] Tests cover the above; every existing test passes; ruff clean; CI green.

## Notes for the implementer

- The implementation is up for review on branch `feature/streaks` (see the linked pull request).
- SQLite's `date(asked_at)` gives the UTC date of a stored timestamp.
