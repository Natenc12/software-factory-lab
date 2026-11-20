"""Write tickets/T<n>-A.md and T<n>-B.md. B = A's sections verbatim + Examples of done + Must not change
(inserted after Decisions). Only exception: T2's worked example sits in Notes (A) / Examples (B)."""
from pathlib import Path

OUT = Path.home() / "repos/pipeline-bench/tickets"
T = {}

# ---------------------------------------------------------------- T1
T[1] = dict(
title="Question list: page 2 repeats the last question of page 1",
problem="""`list_questions(conn, class_id, page, per_page)` in `src/lab/questions.py` returns overlapping
pages. Page 2 starts with the last question already shown on page 1, and each later page starts with
the last question of the page before. With 7 questions and 3 per page, a teacher paging through sees
one question twice and the pages do not line up with the question count.

Seen with the CLI: `python -m lab.cli list 1 --per-page 3 --page 2` shows question 3 again (it was
the last line of page 1).""",
why="""Teachers page through a class's questions to answer them. Repeated rows make them think a
question was asked twice and make "how many are left" impossible to judge from the pages.""",
scope_in="""Pagination in `list_questions` (`src/lab/questions.py`), and a test that would have caught it.""",
scope_out="""The function's signature and defaults (`page=1`, `per_page=20`), its ordering (oldest first, by
question id), `count_questions`, the CLI, and any other module.""",
decisions="""- Pages start at 1. A page past the end returns an empty list.
- Order stays oldest first by question id; hidden questions are never listed and do not take up a slot.
- Bad arguments (`page < 1`, `per_page < 1`) still raise `ValueError`, as today.""",
examples="""- 7 visible questions q1…q7 in a class, `per_page=3`: page 1 → `[q1, q2, q3]`; page 2 → `[q4, q5, q6]`;
  page 3 → `[q7]`; page 4 → `[]`.
- 6 questions q1…q6 where q2 is hidden, `per_page=2`: page 1 → `[q1, q3]`; page 2 → `[q4, q5]`;
  page 3 → `[q6]`.
- 4 questions, `per_page=1`: pages 1–4 return q1, q2, q3, q4 one each; page 5 → `[]`.
- `page=0` or `per_page=0` → `ValueError`.""",
mustnot="""- `list_questions`' signature and defaults (`page=1`, `per_page=20`).
- Page 1's results (already correct today).
- Oldest-first order by question id; hidden questions are never listed.
- The CLI `list` command's output format.
- Every existing test passes unchanged.""",
done="""- [ ] With 7 visible questions and `per_page=3`, pages 1, 2 and 3 return 3, 3 and 1 questions, and
      together, in order, they contain every question exactly once; page 4 is empty.
- [ ] Hidden questions are still skipped and do not shift the pages.
- [ ] `page < 1` and `per_page < 1` still raise `ValueError`.
- [ ] A test that fails on today's code and passes with the fix is added.
- [ ] Every existing test passes; `ruff check` and `ruff format --check` are clean; CI is green.""",
notes="""- The page offset is computed inside `list_questions`; the SQL itself is fine.
- `tests/test_questions.py` has `ask_many()` for making several questions quickly.""",
)

# ---------------------------------------------------------------- T2
T2_EXAMPLE = """Class "Biology" (and nothing else in it), in this order:

| id | student | asked_at | text | hidden | answer |
|---|---|---|---|---|---|
| 1 | Ada | `2026-03-01T09:00:00` | `What is DNA?` | no | `From the class material: DNA carries genetic information.` |
| 2 | Ben | `2026-03-01T09:05:00` | `Why, though?` | no | none |
| 3 | Ada | `2026-03-01T09:10:00` | `What does "ATP" mean?` | no | none |
| 4 | Ben | `2026-03-01T09:15:00` | `Is this on the test?` | **yes** | none |

`export_class_questions(conn, biology.id)` returns exactly this string (every line ends with `\\n`,
including the last):

```
question_id,student,asked_at,question,answer
1,Ada,2026-03-01T09:00:00,What is DNA?,From the class material: DNA carries genetic information.
2,Ben,2026-03-01T09:05:00,"Why, though?",
3,Ada,2026-03-01T09:10:00,"What does ""ATP"" mean?",
```"""

T[2] = dict(
title="Export a class's questions as CSV",
problem="""Teachers want to take a class's questions into a spreadsheet (to plan a revision lesson, or to
share with a colleague). Study Buddy has no way to get them out other than paging through the CLI
`list` command, which leaves out who asked and whether the question was answered.""",
why="""Teachers already keep their planning in spreadsheets. Without an export they copy questions by
hand, which nobody does, so the questions students ask never feed back into teaching.""",
scope_in="""A new function `export_class_questions(conn, class_id) -> str` in a new module `src/lab/export.py`
that returns the class's questions as CSV text, and tests for it.""",
scope_out="""A CLI command, writing files, other formats (JSON, Excel), filtering or paging the export,
and any change to existing modules or the schema.""",
decisions="""- The function returns the CSV as a `str`; it writes no file. Import path: `from lab.export import
  export_class_questions`.
- Header line, exactly: `question_id,student,asked_at,question,answer`.
- One row per **visible** question of the class (hidden questions are left out), ordered by question
  id ascending.
- Columns: `question_id` = the question's id; `student` = the asking student's name; `asked_at` = the
  stored `asked_at` value as is; `question` = the question text; `answer` = the stored answer's body,
  or empty if the question has no answer.
- Quoting is Python's `csv` module default (`csv.writer`, `QUOTE_MINIMAL`): a field is wrapped in
  double quotes only if it contains a comma, a double quote or a line break, and double quotes inside
  it are doubled.
- Every line ends with `\\n` (not `\\r\\n`), including the last one.
- A class with no visible questions returns the header line only:
  `"question_id,student,asked_at,question,answer\\n"`.
- An unknown `class_id` raises `LookupError` (as `get_class` does).""",
examples="""- The worked example below returns exactly the string shown.
- A class with no questions (or only hidden ones) → `"question_id,student,asked_at,question,answer\\n"`.
- A question whose text contains a line break, `Line one\\nline two`, appears as
  `"Line one\\nline two"` (quoted, the line break kept inside the quotes).
- Questions from other classes never appear.
- `export_class_questions(conn, 999)` with no class 999 → `LookupError`.

""" + T2_EXAMPLE,
mustnot="""- Every existing module, function and test, unchanged (this is a new module only).
- The schema: no migration.
- Hidden questions stay out of anything a teacher exports.""",
done="""- [ ] `from lab.export import export_class_questions` works; it returns a `str`.
- [ ] The output follows the format in Decisions exactly; for the worked example in Notes it is
      byte-for-byte the string shown there.
- [ ] A class with no visible questions returns the header line only.
- [ ] Hidden questions and other classes' questions are left out; rows are ordered by question id.
- [ ] Fields with commas, double quotes or line breaks are quoted as `csv.writer` does by default.
- [ ] An unknown class raises `LookupError`.
- [ ] Tests cover the above; every existing test passes; ruff clean; CI green.""",
notes_a="""- `csv.writer(buf, lineterminator="\\n")` on an `io.StringIO` gives exactly the quoting and line
  endings above.
- Answers live in the `answers` table (one row per question at most).

**Worked example.** """ + T2_EXAMPLE,
notes_b="""- `csv.writer(buf, lineterminator="\\n")` on an `io.StringIO` gives exactly the quoting and line
  endings above.
- Answers live in the `answers` table (one row per question at most).
- The worked example's exact output is in Examples of done.""",
)

# ---------------------------------------------------------------- T3
T[3] = dict(
title="Record when each student was last seen",
problem="""Teachers cannot tell which students have gone quiet. The `students` table only has `id`,
`class_id`, `name` and `created_at`; nothing records when a student last asked a question, and
working it out means scanning every question.""",
why="""A teacher wants to notice, early, the student who stopped asking questions three weeks ago.
A stored last-seen time makes that a cheap lookup and is the basis for any later "gone quiet" view.""",
scope_in="""- A new migration adding a `last_seen` column to `students`, backfilled for existing students.
- `ask_question` keeps `last_seen` up to date.
- `Student` (in `src/lab/models.py`) gains a `last_seen` field.
- Tests.""",
scope_out="""Showing `last_seen` anywhere (summary, CLI), "inactive student" alerts or reports, and any
other change to the schema.""",
decisions="""- `students.last_seen` is a nullable text column holding an ISO timestamp, like every other time
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
  `Student.from_row`.""",
examples="""- Existing database (0001 and 0002 applied) where Ada asked at `2026-03-01T09:00:00` and
  `2026-03-04T10:00:00` (the second one later hidden) and Ben asked nothing → after migrating, Ada's
  `last_seen` = `2026-03-04T10:00:00`, Ben's = `NULL`; every class, student, question and answer row
  is still there; running the migration script again applies nothing.
- A fresh database migrated twice → `students` has a `last_seen` column; the second run applies
  nothing.
- `enrol_student(...)` → `get_student(...).last_seen is None`.
- Ada (last_seen `2026-03-04T10:00:00`) asks with `asked_at="2026-03-05T08:00:00"` → `last_seen` becomes
  `2026-03-05T08:00:00`. She then asks with `asked_at="2026-02-01T08:00:00"` → it stays
  `2026-03-05T08:00:00`.""",
mustnot="""- Migrations already applied (`0001_init.sql`, `0002_answers.sql`) are never edited.
- Existing rows in every table survive the migration, unchanged apart from the new column.
- `Student`'s existing fields (`id`, `class_id`, `name`, `created_at`) keep their names and order.
- `ask_question`'s signature and return value.
- Every existing test passes unchanged.""",
done="""- [ ] A new migration file in `migrations/` adds `students.last_seen` and backfills it.
- [ ] Migrating a fresh database twice is clean (the second run applies nothing).
- [ ] On a database that already has 0001 and 0002 applied, with data, the migration script applies
      only the new file; the backfill is right (latest `asked_at`, hidden questions included; `NULL`
      with no questions) and all existing rows survive.
- [ ] `ask_question` moves `last_seen` forward, never back.
- [ ] `get_student(...).last_seen` returns the stored value (`None` when `NULL`).
- [ ] Tests cover the above; every existing test passes; ruff clean; CI green.""",
notes="""- **Pitfall:** `0001_init.sql` and `0002_answers.sql` are already applied on every existing
  database. `scripts/migrate.py` records each file it applies and never runs it again, so a change to
  either file never reaches an existing database and leaves the recorded history wrong. Do not edit
  them; the change goes in a new file (`0003_...sql`).
- SQLite's `alter table ... add column` cannot add a `NOT NULL` column without a default; the column is
  nullable, so this does not bite here.
- `tests/conftest.py` applies migrations with `migrate_script.migrate()`, which also takes a
  `migrations_dir`, handy for building a database from only the old files.""",
)

# ---------------------------------------------------------------- T4
T[4] = dict(
title="Class summary: total counts hidden questions",
problem="""`class_summary(conn, class_id)` in `src/lab/summary.py` includes hidden questions in the class
`total`. A teacher hides a question; it disappears from the list, but the summary's `total` still
counts it, and `unanswered` (worked out as `total - answered`) goes up by one with it.

Example: a class with two questions, one of them hidden → `total` 2 and `unanswered` 2;
it should be `total` 1 and `unanswered` 1.""",
why="""The summary is how a teacher sees how many questions are still waiting. Hidden questions are
ones the teacher removed on purpose; counting them makes the waiting number wrong and makes hiding
look broken.""",
scope_in="""The class-level `total` (and so `unanswered`) in `class_summary`, and a test for it.""",
scope_out="""- `student_breakdown` in the same file. It has a separate, known bug: a student who has asked no
  questions shows `questions: 1` and `unanswered: 1` instead of 0 and 0. That is tracked on its own
  ticket; leave `student_breakdown` exactly as it is in this change, even though it is next door.
- The shape of the returned dict, the CLI, and any other module.""",
decisions="""- Hidden questions are left out of the class `total`, `answered` and `unanswered` (`answered`
  already leaves them out).
- `unanswered` stays `total - answered`.
- The returned dict keeps the same keys and shape.""",
examples="""- One visible question and one hidden question (the hidden one answered) → `total` 1, `answered` 0,
  `unanswered` 1.
- Three visible questions (one answered) and two hidden questions (one answered) → `total` 3,
  `answered` 1, `unanswered` 2.
- Every question hidden → `total` 0, `answered` 0, `unanswered` 0.
- No questions at all → `total` 0, `answered` 0, `unanswered` 0 (as today).""",
mustnot="""- `student_breakdown`: its code stays as it is, known bug included (Scope Out).
- The keys and shape of the dict `class_summary` returns.
- Counts for classes with no hidden questions.
- Every existing test passes unchanged.""",
done="""- [ ] A class with one visible and one hidden (answered) question reports `total` 1, `answered` 0,
      `unanswered` 1.
- [ ] Classes with no hidden questions report the same numbers as today.
- [ ] A test that fails on today's code and passes with the fix is added.
- [ ] `student_breakdown` is not modified.
- [ ] Every existing test passes; ruff clean; CI green.""",
notes="""- `questions.hidden = 1` marks a hidden question (see the comment in `migrations/0001_init.sql`).
- `count_questions` in `src/lab/questions.py` already counts visible questions correctly.""",
)

# ---------------------------------------------------------------- T5
T[5] = dict(
title="Cache answers by question text to speed up answer()",
problem="""`answer(conn, question_id, provider=None)` in `src/lab/ask.py` calls the provider every time,
even when the same question has been answered before. With a real model each call takes seconds and
costs money, and students ask the same thing over and over ("When is the exam?", "What is DNA?").""",
why="""Answers are the slow, paid part of the app. Most repeat questions could be answered instantly
and for free from an answer we already have.""",
scope_in="""- An in-memory cache in `src/lab/ask.py`, keyed by question text: `answer()` looks the text up
  before calling the provider and stores the provider's answer on a miss.
- `clear_answer_cache()` in `src/lab/ask.py`.
- Tests.""",
scope_out="""A cache table or any migration, cache expiry or size limits, caching in the job queue code,
changes to the provider interface, and normalising question text (case, punctuation).""",
decisions="""- The cache key is the question text exactly as stored (`ask_question` already strips spaces). No
  lower-casing or other normalising.
- The cache lives in memory, per process: a module-level dict in `src/lab/ask.py`. No new table.
- On a hit, `answer()` still stores (or replaces) the `answers` row for this question and returns it,
  exactly as on a miss; only the provider call is skipped.
- `lab.ask.clear_answer_cache()` empties the cache (tests call it to start clean).""",
examples="""- Ada asks "What is DNA?" and it is answered: the provider is called once. Ben then asks
  "What is DNA?": `answer()` returns the same body without calling the provider, and Ben's question
  gets its own `answers` row.
- Answering the same question twice in a row calls the provider once.
- After `clear_answer_cache()`, the next `answer()` for that text calls the provider again.""",
mustnot="""- For any question, `answer()` returns the same answer body it would return without the cache.
- `answer()`'s signature and the `Answer` it returns; one `answers` row per question, replaced when
  answered again.
- Hidden questions are still refused (`ValueError`); a missing question still raises `LookupError`.
- Every existing test passes unchanged.""",
done="""- [ ] Answering two questions with the same text calls the provider once.
- [ ] Both questions get their own stored answer.
- [ ] After `clear_answer_cache()`, answering calls the provider again.
- [ ] Tests cover the above; every existing test passes; ruff clean; CI green.""",
notes="""- `answer()` accepts a `provider` argument, so a test can pass a provider that counts its calls.
- The queue path (`answer_pending`) goes through `answer()`, so it gets the cache for free.""",
)

# ---------------------------------------------------------------- T6
T[6] = dict(
title="Show each student's question streak",
problem="""Teachers want to encourage regular practice: a student who asks something every day is
building a habit. Study Buddy has no idea of a streak: how many days in a row a student has asked a
question, or the best run they have had.""",
why="""A visible streak is a cheap nudge that keeps students coming back daily, and it lets a teacher
spot the students whose habit just broke.""",
scope_in="""- `src/lab/streaks.py` with `current_streak`, `best_streak` and `record_streak`.
- A new migration adding a `streaks` table (best streak per student), with a backfill.
- Tests.""",
scope_out="""Calling `record_streak` automatically from `ask_question`, showing streaks in the summary or
CLI, time zones other than UTC, and reminders or notifications.""",
decisions="""- A day is the UTC calendar date of a question's `asked_at`.
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
  get their row on their first `record_streak`.""",
examples="""(Today is 2026-03-12 unless stated.)
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
  nothing.""",
mustnot="""- Migrations already applied (`0001_init.sql`, `0002_answers.sql`) are never edited.
- Existing rows in every table survive the migration unchanged.
- `ask_question` and every other existing function behave exactly as before.
- Every existing test passes unchanged.""",
done="""- [ ] Three consecutive days ending today give a streak of 3; a missed day ends the streak.
- [ ] A streak ending yesterday still counts; one ending earlier is 0.
- [ ] Several questions on one day count as one day; hidden questions do not count.
- [ ] `best_streak` is 0 with no row; `record_streak` keeps the highest value.
- [ ] The migration applies cleanly on an existing database with data, the backfill is as decided,
      and migrating twice is clean.
- [ ] Tests cover the above; every existing test passes; ruff clean; CI green.""",
notes="""- The implementation is up for review on branch `feature/streaks` (see the linked pull request).
- SQLite's `date(asked_at)` gives the UTC date of a stored timestamp.""",
)


def label(name, text):
    sep = "\n\n" if text.startswith("- ") else " "
    return f"**{name}:**{sep}{text}"


def render(n, t, shape):
    notes = t.get("notes") or (t["notes_a"] if shape == "A" else t["notes_b"])
    parts = [
        f"# {t['title']}",
        "## Problem\n\n" + t["problem"],
        "## Why it matters\n\n" + t["why"],
        "## Scope\n\n" + label("In", t["scope_in"]) + "\n\n" + label("Out", t["scope_out"]),
        "## Decisions\n\n" + t["decisions"],
    ]
    if shape == "B":
        parts += ["## Examples of done\n\n" + t["examples"], "## Must not change\n\n" + t["mustnot"]]
    parts += ["## Done when\n\n" + t["done"], "## Notes for the implementer\n\n" + notes]
    return "\n\n".join(parts) + "\n"


for n, t in T.items():
    for shape in "AB":
        (OUT / f"T{n}-{shape}.md").write_text(render(n, t, shape))
print("written", sorted(p.name for p in OUT.glob("*.md")))
