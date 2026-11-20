# Contract: issue #4 (copied verbatim from the issue body, 2026-11-20)

Source: `gh issue view 4 --repo Natenc12/pipeline-lab`. Sections: Scope, Decisions, Examples of done, Must not change.

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

## Amendments

None. Stop 1 answer (2026-11-20): "The contract stands as written. Go ahead."
Read as: card 1 = B (quoting is literally `csv.writer`'s default; on Python 3.10 a lone `\r` stays unquoted, listed as not handled in the brief); card 2 = A (export exact text; formula-injection risk named in the brief, follow-up issue offered as a draft only).
