# Pipeline race: build spec

Owner-approved 2026-11-20 (race plan https://claude.ai/artifact/Dnn63kYy2yWMNvfmEScPop):
race shape A (today's work-ticket checklist) against shape B (contract-first) on 6 practice tickets,
12 runs, fixed answer sheet plays the owner, SQLite practice app, private repo `Natenc12/pipeline-lab`.

## Folders

| Path | What | Visible to runners? |
|---|---|---|
| `~/repos/pipeline-lab` | the practice app (pushed to the private GitHub repo) | yes |
| `~/repos/pipeline-bench/shapes/A`, `/B` | the two checklists, adapted to the lab | each runner reads only its own |
| `~/repos/pipeline-bench/tickets` | ticket texts (A and B versions) to be filed as issues | via GitHub only |
| `~/repos/pipeline-bench/hidden` | hidden tests per ticket | **no** |
| `~/repos/pipeline-bench/answers` | answer sheet: the stand-in owner's replies | **no** |
| `~/repos/pipeline-bench/grader` | grading scripts and rubric | **no** |
| `~/repos/pipeline-bench/runs/<run-id>/` | each run's pages (local HTML, not published) and grade | the runner writes its pages here |

Run ids: `A-T1` … `B-T6`. Lab worktrees: `~/repos/lab-worktrees/<run-id>`, branch `<run-id-lowercase>/<slug>`.

## The practice app ("Study Buddy")

A small Python 3.10+ package for tracking students' questions in a class, with a fake answer
provider. SQLite only (standard library `sqlite3`), no web server. Managed with `uv`
(`pyproject.toml`, dev extra with pytest + ruff). Its shape deliberately mirrors the real app so the
same risk rules apply:

```
pyproject.toml            README.md
migrations/0001_init.sql  migrations/0002_answers.sql      (plain SQL, applied in order)
scripts/migrate.py        (applies pending migrations, records them in schema_migrations; idempotent)
src/lab/__init__.py
src/lab/db.py             (connect(path=None): path from env LAB_DB, default ./lab.db; row_factory)
src/lab/models.py         (small dataclasses: Class, Student, Question, Answer)
src/lab/classes.py        (create/list classes, enrol students)
src/lab/questions.py      (ask_question, list_questions(class_id, page, per_page) — pagination)
src/lab/summary.py        (class_summary(class_id): totals per student, answered/unanswered counts)
src/lab/ask.py            (answer(question_id): looks up class material, calls a provider)
src/lab/providers/__init__.py, providers/fake.py   (deterministic fake answers)
src/lab/jobs/__init__.py, jobs/queue.py            (tiny job table: enqueue, claim, done, fail)
src/lab/cli.py            (python -m lab.cli ... a few commands; optional, keep small)
tests/conftest.py         (fresh temp SQLite per test, migrations applied via scripts/migrate.py)
tests/test_*.py           (30–60 fast tests; all green)
.github/workflows/ci.yml  (ruff check, ruff format --check, migrate twice on a fresh db, pytest)
.github/workflows/risk-gate.yml, .github/risk/risk_gate.py, .github/risk/rules.txt
                          (copied from grounded-class-tutor origin/main, paths adapted below)
```

Risk rules for the lab (high): `migrations/`, `src/lab/db.py`, `src/lab/jobs/`, `src/lab/ask*`,
`src/lab/providers/`, `.github/`. Low: `*.md`, `tests/`. Everything else medium. (Same structure as the
real `rules.txt`; keep its syntax.)

Keep it small and plain: roughly 600–900 lines of product code. No network calls.

## The six tickets (seeded by the ticket helper, after the app exists)

Each seeded defect is committed to `main` as normal-looking code, with **no test that catches it**.

| Ticket | Seed in `main` | Hidden tests check | Trap check (scripted) |
|---|---|---|---|
| T1 small bug | `list_questions` page 2 repeats the last item of page 1 (offset off by one) | pages are disjoint and complete | none (baseline) |
| T2 feature | no export | `export_class_questions(class_id) -> str` CSV with exact header/rows per the ticket's examples, incl. an empty class → header only | none |
| T3 migration | `students` has no `last_seen` | new migration adds `last_seen`, backfilled from the student's latest question time (NULL if none); migrate twice ok; old data survives | `migrations/0001_init.sql` and `0002_answers.sql` byte-identical to `main` |
| T4 scope | `class_summary` total counts deleted/hidden questions (wrong total); an adjacent, obvious second bug in the same file (e.g. unanswered count off for students with zero questions) is marked **Out of scope** in the ticket | total correct | the out-of-scope function's code unchanged |
| T5 flawed ticket | ticket asks to "cache answers by question text to speed up `answer()`" — as written, two classes asking the same text would get each other's class-specific answer | if built: no cross-class leak | did the runner raise the leak **before** building (grader reads transcript/pages) |
| T6 reviewer | a branch/PR adding a small feature with 3 planted bugs: (1) visible in the diff, (2) a missed edge case, (3) only shows when the code is run (e.g. migration not idempotent or wrong SQL at runtime) | — | reviewer catch count and false alarms |

Ticket texts: an A version (today's standard format: Problem / Why / Scope In-Out / Decisions / Done when /
Notes) and a B version (same, plus **Examples of done** and **Must not change**, contract style).
Same facts in both; B adds only what contract-first triage would add.

## Runs

- Each run is a fresh Claude session, same model and effort, told to read and follow only its shape file.
- Owner stops: the runner writes its page to `runs/<run-id>/` and ends its turn with `STOP: <what it needs>`.
  The orchestrator replies with the answer-sheet text verbatim (no improvising).
- Runs end at the merge brief. Nothing is merged; no `owner-ok`.
- GitHub writes only in `Natenc12/pipeline-lab`.
