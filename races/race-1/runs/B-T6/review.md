# Review — PR #13 (`feature/streaks`) for issue #12

Run `B-T6`, step 6 (agent review). The reviewer was a fresh general-purpose agent whose whole prompt was
`shapes/B/reviewer-brief.md` filled in for PR #13, with `runs/B-T6/contract.md` pasted verbatim. Sandbox:
`~/repos/lab-worktrees/B-T6` (made by `lab-up.sh B-T6 review`, then reset to `origin/feature/streaks`
at `93548fa`). Scratch: `runs/B-T6/scratch/`.

## Reviewer's report (verbatim)

## Review of PR #13 (feature/streaks) against issue #12's contract

The PR should not merge. Three contract examples fail. Two of the bugs are in one query (`active_days`), and the third is in the migration's backfill. CI is green because nothing in CI covers these cases.

### 1. The contract, line by line
I wrote the checks before reading the diff: `scratch/checks.py`, 23 checks. Run with `uv run python <scratch>/checks.py`.
- ✓ Ada asked on Mar 10, 11 and 12 → 3 (E1)
- ✓ Asked on Mar 10 and 11 → 2. Only question on Mar 9 → 0 (E2a, E2b)
- ✗ Ben, two questions on Mar 12 → returns **1**, should be 2 (E3)
- ✗ Cora, hidden question → returns **1**, should be 0 (E4)
- ✓ No questions → 0 and 0 (E5)
- ✓ `record_streak` gives 3, then still 3 (E6)
- ✗ Migration with history → **crashes** (E7, plus a run of the real script below)
- ✓ 0001 and 0002 not edited (`git diff --name-status`: only 3 files added)
- ✓ Existing rows survive: the failed migration rolled back, with all 3 question rows intact and no `streaks` table
- ✓ `ask_question` and the other existing functions are unchanged (no existing src file touched)
- ✓ Existing tests unchanged and passing: `pytest -q` gives 111 passed. Ruff check and ruff format pass. On a fresh database, migrate twice gives "applied ×3", then "nothing to apply".

### 2. Blocking findings
**B1. The migration crashes for any student who asked visible questions on two or more different days.** `migrations/0003_streaks.sql:13` groups by `student_id, date(asked_at)`, which makes one row per student per day. The `student_id` primary key then rejects the second row.
Reproduction: apply 0001 and 0002, give Ada visible questions on Mar 9, 11 and 12, then run `uv run python scripts/migrate.py`.
```
sqlite3.IntegrityError: UNIQUE constraint failed: streaks.student_id
exit=1
```
It fails the same way on every re-run. Any real database with history cannot upgrade. CI misses this because it migrates an empty database. The fix is to group by `student_id` only.

**B2. Hidden questions count.** In `src/lab/streaks.py:19` the query has no `hidden = 0` filter.
**B3. Several questions on one day break the streak.** The same query at line 19 has no `distinct`, so a repeated day stops the loop at line 34.
Reproduction for both: `LAB_DB=<scratch>/repro.db uv run python <scratch>/repro.py`
```
Ben 1 (want 2)  Cora 1 (want 0)
```
More from checks.py:
- A hidden question on Mar 11, between visible questions on Mar 10 and 12, gives 3 (should be 1).
- A day with one hidden and one visible question gives 1 (should be 2).

### 3. Departures from the contract
- The "visible only" and "several questions count as one day" decisions are not implemented (B2, B3).
- The backfill decision ("one row per student, best = 1") is not met (B1).
- Scope is fine. Nothing is wired into `ask_question`, the summary or the CLI.

### 4. Non-blocking concerns
- A question dated after `today` (for example Mar 14 when today is Mar 12) makes `current_streak` return 0 instead of 2. The contract doesn't cover this case.
- `today` must be a `date`. Passing an ISO string raises `TypeError`.
- `best_streak` raises `LookupError` for an unknown student. The contract only asks for 0 when there is no row, so this is a reasonable choice, but it isn't specified.
- The builder's tests have no hidden, same-day or migration-with-history case. That is why all three bugs got through.
- The comment on line 1 of 0003 says "at least one question". It should say "visible".

### 5. Checked and fine
- An unknown student raises `LookupError` in both `current_streak` and `record_streak`.
- Days are taken in UTC: asked_at values with +05:00 and -05:00 offsets land on the right day, because SQLite's `date()` converts to UTC.
- `today` defaults to the current UTC date.
- The first `record_streak` creates a row, even when the streak is 0.
- A lower current streak keeps the stored best. A higher one raises it and updates `updated_at`.
- Writes are committed. Streaks are per student. A 400-day streak across a year boundary counts correctly.
- A failed migration rolls back cleanly.

Scratch files are in `/Users/nathan/repos/pipeline-bench/runs/B-T6/scratch` (`checks.py`, `repro.py`, `setup.py`). All database files are deleted.

---

## Builder re-check

I re-ran the reviewer's reproductions myself, in the sandbox at `93548fa`, each on a new database in my
own scratch folder. **All three blocking findings reproduced.**

- **B1 — reproduced.** I made a database with only `0001_init.sql` and `0002_answers.sql` applied, using
  the reviewer's `scratch/setup.py`. It left Ada with three visible questions (Mar 9, 11, 12, all
  `hidden=0`) and Ben with none. Then I ran the real `uv run python scripts/migrate.py`. Output:
  `sqlite3.IntegrityError: UNIQUE constraint failed: streaks.student_id`, exit 1. A second run fails the
  same way. Afterwards `schema_migrations` still lists only 0001 and 0002, all 3 question rows are
  there, and there is no `streaks` table. So the rollback works, but the upgrade can never complete. In
  the diff, `0003_streaks.sql` ends with `group by student_id, date(asked_at);`, which gives one row
  per student per day.
- **B2 and B3 — reproduced.** On a new migrated database, the reviewer's `scratch/repro.py` printed
  `Ben 1 (want 2)  Cora 1 (want 0)`. In the diff, `active_days` (`src/lab/streaks.py`) runs
  `select date(asked_at) as day from questions where student_id = ? order by day desc`. There is no
  `hidden = 0` and no `distinct`, which explains both results.
- **Not re-checked:** the extra cases the reviewer cites from `checks.py`, its ruff result, and the
  non-blocking concerns. I did re-run `uv run pytest -q` on a new database (after migrating 0001–0003
  on an empty database, which works): 111 passed. That matches the reviewer, and it shows that the
  PR's own tests and CI do not cover any of the three failures.

Nothing was fixed, pushed, commented on or relabelled. The PR branch is untouched.
