## Problem

`export_class_questions` (from #3) writes each question and answer text into the CSV as stored. When a
teacher opens the file in a spreadsheet, a cell that starts with `=`, `+`, `-` or `@` is read as a
formula. A student could type a question such as `=HYPERLINK("http://example.com","click")` and the
teacher's spreadsheet would show a live link or run the formula instead of the question text.

## Why it matters

The export's whole purpose is to be opened in a spreadsheet, and the question text is typed by
students. This is the known "CSV injection" problem; the usual fix is to put a `'` in front of such
cells so the spreadsheet shows them as text.

## Scope

**In:** Deciding whether the export neutralises cells that start with `=`, `+`, `-` or `@` (question
text, answer body, student name), and doing it with tests if so.

**Out:** Other formats, a CLI command, changing what is stored in the database.

## Decisions to make at triage

- Neutralise (prefix `'`) or leave as is? Neutralising means the export no longer round-trips the
  stored text exactly, which #3's decisions currently require.
- Which columns: free text only (question, answer) or also student names?

## Done when

- [ ] The decision above is recorded and, if it is "neutralise", a question starting with `=` comes
      out as `'=...` and a test covers each leading character.
