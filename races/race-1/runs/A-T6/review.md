# Review of PR #13 (`feature/streaks` @ 93548fa) for issue #11, run A-T6

Step 6 of shape A. A fresh reviewer agent ran with `shapes/A/reviewer-brief.md` filled in as its whole prompt. It had its own sandbox (`~/repos/lab-worktrees/A-T6`, a local branch reset to `origin/feature/streaks`) and its own database in `runs/A-T6/scratch/`.

## Reviewer's report (verbatim)

**Verdict: do not merge.** PR #13 (`feature/streaks` @ 93548fa) has 3 blocking bugs. Two break "Done when" items, and the third stops the migration running on any real database.

**1. Acceptance checks** (written to `/Users/nathan/repos/pipeline-bench/runs/A-T6/scratch/checks.txt` before I read the diff; scripts `behaviour.py` and `c6_migrate_existing.py` are in the same folder)
- C1, three days ending today give 3, and a gap yesterday gives 1: **PASS**
- C2, a streak ending yesterday gives 2, one ending earlier gives 0: **PASS**
- C3, several questions on one day count once, and hidden questions don't count: **FAIL** (B1, B2)
- C4, `best_streak` is 0 with no row, and `record_streak` keeps the highest: **PASS**
- C5, an unknown student raises `LookupError` (all three functions): **PASS**
- C6, migrating an existing database with data, correct backfill, second run clean: **FAIL** (B3)
- C7, the day is the UTC date of a timestamp stored with a `-05:00` offset: **PASS**
- C8, pytest (111 passed), ruff, ruff format, migrating a fresh database twice: **PASS**. CI's `ruff + pytest` is green. `risk-gate` is red only because the PR is `risk:high` and needs the `owner-ok` label; that is not a code defect.

**2. Blocking findings**

**B3 (most severe): migration 0003 fails on any database where a student asked visible questions on 2 or more days.** At `migrations/0003_streaks.sql:14`, `group by student_id, date(asked_at)` inserts one row per student per day into a table keyed on `student_id`. The transaction rolls back, so the database is left at 0002 and cannot move forward. Reproduction: `LAB_DB=…/scratch/review.db uv run python …/scratch/c6_migrate_existing.py` (builds a 0001+0002 database with data, then runs `scripts/migrate.py` twice):
```
run 1: rc=1 sqlite3.IntegrityError: UNIQUE constraint failed: streaks.student_id
run 2: rc=1 sqlite3.IntegrityError: UNIQUE constraint failed: streaks.student_id
streaks: NO TABLE
```
CI and the tests never catch this because they only migrate empty databases. The fix is `group by student_id`.

**B1: several questions on one day break the streak.** `active_days` (`src/lab/streaks.py:19`) returns one entry per question, with no `distinct`. A repeated day no longer matches the expected date, so the loop stops early. From `uv run python …/scratch/behaviour.py`:
```
C3 two questions/day on 3 days (expect 3): 1
C3 yesterday + 2 today (expect 2): 1
```

**B2: hidden questions count.** The same query (`src/lab/streaks.py:19`) has no `hidden = 0` filter:
```
C3 hidden-only today (expect 0): 1
C3 hidden-only yesterday breaks it (expect 1): 3
```

**3. Departures from the ticket**
- Decision "Several questions on one day count as one day. Hidden questions do not count" is not implemented (B1, B2).
- Decision "Backfill: one row for every student…" is implemented wrongly (B3).
- Done when "Tests cover the above" is not met. There are no tests for multiple questions on one day, hidden questions, or migrating a database that already has data.
- No scope-out violations: `ask_question`, the summary and the CLI are untouched.

**4. Non-blocking concerns**
- `active_days` reads the student's whole question history on every call; it could stop at the first gap or limit the date range.
- If an `asked_at` value is not a valid ISO timestamp (e.g. an unpadded hour), `date()` returns NULL and `date.fromisoformat` raises `TypeError`. Data written by the app is always valid, so this is low risk.
- The migration comment says "asked at least one question" but means a *visible* question.
- `record_streak` updates `updated_at` even when the best is unchanged. Possibly intended, but the ticket doesn't say.

**5. Checked and fine**
- The yesterday-alive logic, the default today in UTC, and per-student isolation.
- The upsert keeps `max(best, …)`, and `record_streak` creates a row with best 0 for a student who has none.
- Students with only hidden questions, or no questions, get no backfill row.
- The migration runner rolls back cleanly when a migration fails.
- The table schema matches the decision (`student_id` primary key, `best`, `updated_at`).
- The scratch database was deleted, and the working tree is still clean.

## Builder re-check

I read both of the reviewer's scripts before running them (they only use the app's own API and `scripts/migrate.py`). Then I re-ran them in the same sandbox at 93548fa on a new database (`scratch/recheck.db`, deleted afterwards). I also checked the cited lines and the ticket text.

- **B3, reproduced.** `c6_migrate_existing.py` gave `rc=1 sqlite3.IntegrityError: UNIQUE constraint failed: streaks.student_id` on both runs. Afterwards there was no `streaks` table and `schema_migrations` held only 0001 and 0002. I confirmed it a second way, independent of the reviewer's script: running `migrations/0003_streaks.sql` alone in `sqlite3 :memory:` on one student with visible questions on two days failed with `UNIQUE constraint failed: streaks.student_id`. The cause is `group by student_id, date(asked_at)` at line 14.
- **B1, reproduced.** Two questions a day on 3 days gave 1 (expected 3). Yesterday plus two today gave 1 (expected 2). The query at `src/lab/streaks.py:19` has no `distinct`.
- **B2, reproduced.** A hidden question only today gave 1 (expected 0). A hidden question only yesterday gave 3 (expected 1). The same query has no `hidden = 0` filter.
- **Passing checks confirmed:** C1, C2, C4, C5 and C7 matched the reviewer's output, and `uv run pytest -q` gave 111 passed.
- **Ticket wording confirmed.** Issue #11 says that several questions on one day count as one day and that hidden questions do not count. It also requires that the migration applies cleanly on an existing database with data, and that tests cover all of the above.
- **Not re-checked:** ruff and ruff format, and the reviewer's CI and `risk-gate` status claims. The non-blocking concerns can't be proven, by definition.

Nothing was fixed, pushed, commented on or labelled. I tore down the sandbox afterwards.
