# Export a class's questions as CSV

## Problem

Teachers want to take a class's questions into a spreadsheet (to plan a revision lesson, or to
share with a colleague). Study Buddy has no way to get them out other than paging through the CLI
`list` command, which leaves out who asked and whether the question was answered.

## Why it matters

Teachers already keep their planning in spreadsheets. Without an export they copy questions by
hand, which nobody does, so the questions students ask never feed back into teaching.

## Scope

**In:** A new function `export_class_questions(conn, class_id) -> str` in a new module `src/lab/export.py`
that returns the class's questions as CSV text, and tests for it.

**Out:** A CLI command, writing files, other formats (JSON, Excel), filtering or paging the export,
and any change to existing modules or the schema.

## Decisions

- The function returns the CSV as a `str`; it writes no file. Import path: `from lab.export import
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
- Every line ends with `\n` (not `\r\n`), including the last one.
- A class with no visible questions returns the header line only:
  `"question_id,student,asked_at,question,answer\n"`.
- An unknown `class_id` raises `LookupError` (as `get_class` does).

## Examples of done

- The worked example below returns exactly the string shown.
- A class with no questions (or only hidden ones) → `"question_id,student,asked_at,question,answer\n"`.
- A question whose text contains a line break, `Line one\nline two`, appears as
  `"Line one\nline two"` (quoted, the line break kept inside the quotes).
- Questions from other classes never appear.
- `export_class_questions(conn, 999)` with no class 999 → `LookupError`.

Class "Biology" (and nothing else in it), in this order:

| id | student | asked_at | text | hidden | answer |
|---|---|---|---|---|---|
| 1 | Ada | `2026-03-01T09:00:00` | `What is DNA?` | no | `From the class material: DNA carries genetic information.` |
| 2 | Ben | `2026-03-01T09:05:00` | `Why, though?` | no | none |
| 3 | Ada | `2026-03-01T09:10:00` | `What does "ATP" mean?` | no | none |
| 4 | Ben | `2026-03-01T09:15:00` | `Is this on the test?` | **yes** | none |

`export_class_questions(conn, biology.id)` returns exactly this string (every line ends with `\n`,
including the last):

```
question_id,student,asked_at,question,answer
1,Ada,2026-03-01T09:00:00,What is DNA?,From the class material: DNA carries genetic information.
2,Ben,2026-03-01T09:05:00,"Why, though?",
3,Ada,2026-03-01T09:10:00,"What does ""ATP"" mean?",
```

## Must not change

- Every existing module, function and test, unchanged (this is a new module only).
- The schema: no migration.
- Hidden questions stay out of anything a teacher exports.

## Done when

- [ ] `from lab.export import export_class_questions` works; it returns a `str`.
- [ ] The output follows the format in Decisions exactly; for the worked example in Notes it is
      byte-for-byte the string shown there.
- [ ] A class with no visible questions returns the header line only.
- [ ] Hidden questions and other classes' questions are left out; rows are ordered by question id.
- [ ] Fields with commas, double quotes or line breaks are quoted as `csv.writer` does by default.
- [ ] An unknown class raises `LookupError`.
- [ ] Tests cover the above; every existing test passes; ruff clean; CI green.

## Notes for the implementer

- `csv.writer(buf, lineterminator="\n")` on an `io.StringIO` gives exactly the quoting and line
  endings above.
- Answers live in the `answers` table (one row per question at most).
- The worked example's exact output is in Examples of done.
