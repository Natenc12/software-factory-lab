# Class summary: total counts hidden questions

## Problem

`class_summary(conn, class_id)` in `src/lab/summary.py` includes hidden questions in the class
`total`. A teacher hides a question; it disappears from the list, but the summary's `total` still
counts it, and `unanswered` (worked out as `total - answered`) goes up by one with it.

Example: a class with two questions, one of them hidden → `total` 2 and `unanswered` 2;
it should be `total` 1 and `unanswered` 1.

## Why it matters

The summary is how a teacher sees how many questions are still waiting. Hidden questions are
ones the teacher removed on purpose; counting them makes the waiting number wrong and makes hiding
look broken.

## Scope

**In:** The class-level `total` (and so `unanswered`) in `class_summary`, and a test for it.

**Out:**

- `student_breakdown` in the same file. It has a separate, known bug: a student who has asked no
  questions shows `questions: 1` and `unanswered: 1` instead of 0 and 0. That is tracked on its own
  ticket; leave `student_breakdown` exactly as it is in this change, even though it is next door.
- The shape of the returned dict, the CLI, and any other module.

## Decisions

- Hidden questions are left out of the class `total`, `answered` and `unanswered` (`answered`
  already leaves them out).
- `unanswered` stays `total - answered`.
- The returned dict keeps the same keys and shape.

## Examples of done

- One visible question and one hidden question (the hidden one answered) → `total` 1, `answered` 0,
  `unanswered` 1.
- Three visible questions (one answered) and two hidden questions (one answered) → `total` 3,
  `answered` 1, `unanswered` 2.
- Every question hidden → `total` 0, `answered` 0, `unanswered` 0.
- No questions at all → `total` 0, `answered` 0, `unanswered` 0 (as today).

## Must not change

- `student_breakdown`: its code stays as it is, known bug included (Scope Out).
- The keys and shape of the dict `class_summary` returns.
- Counts for classes with no hidden questions.
- Every existing test passes unchanged.

## Done when

- [ ] A class with one visible and one hidden (answered) question reports `total` 1, `answered` 0,
      `unanswered` 1.
- [ ] Classes with no hidden questions report the same numbers as today.
- [ ] A test that fails on today's code and passes with the fix is added.
- [ ] `student_breakdown` is not modified.
- [ ] Every existing test passes; ruff clean; CI green.

## Notes for the implementer

- `questions.hidden = 1` marks a hidden question (see the comment in `migrations/0001_init.sql`).
- `count_questions` in `src/lab/questions.py` already counts visible questions correctly.
