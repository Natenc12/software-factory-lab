# Contract for issue #8 (copied verbatim from the issue body, origin: Natenc12/pipeline-lab#8)

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

## Decisions

- Hidden questions are left out of the class `total`, `answered` and `unanswered` (`answered`
  already leaves them out).
- `unanswered` stays `total - answered`.
- The returned dict keeps the same keys and shape.

## Scope

**In:** The class-level `total` (and so `unanswered`) in `class_summary`, and a test for it.

**Out:**

- `student_breakdown` in the same file. It has a separate, known bug: a student who has asked no
  questions shows `questions: 1` and `unanswered: 1` instead of 0 and 0. That is tracked on its own
  ticket; leave `student_breakdown` exactly as it is in this change, even though it is next door.
- The shape of the returned dict, the CLI, and any other module.
