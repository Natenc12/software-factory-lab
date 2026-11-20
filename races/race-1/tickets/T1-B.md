# Question list: page 2 repeats the last question of page 1

## Problem

`list_questions(conn, class_id, page, per_page)` in `src/lab/questions.py` returns overlapping
pages. Page 2 starts with the last question already shown on page 1, and each later page starts with
the last question of the page before. With 7 questions and 3 per page, a teacher paging through sees
one question twice and the pages do not line up with the question count.

Seen with the CLI: `python -m lab.cli list 1 --per-page 3 --page 2` shows question 3 again (it was
the last line of page 1).

## Why it matters

Teachers page through a class's questions to answer them. Repeated rows make them think a
question was asked twice and make "how many are left" impossible to judge from the pages.

## Scope

**In:** Pagination in `list_questions` (`src/lab/questions.py`), and a test that would have caught it.

**Out:** The function's signature and defaults (`page=1`, `per_page=20`), its ordering (oldest first, by
question id), `count_questions`, the CLI, and any other module.

## Decisions

- Pages start at 1. A page past the end returns an empty list.
- Order stays oldest first by question id; hidden questions are never listed and do not take up a slot.
- Bad arguments (`page < 1`, `per_page < 1`) still raise `ValueError`, as today.

## Examples of done

- 7 visible questions q1…q7 in a class, `per_page=3`: page 1 → `[q1, q2, q3]`; page 2 → `[q4, q5, q6]`;
  page 3 → `[q7]`; page 4 → `[]`.
- 6 questions q1…q6 where q2 is hidden, `per_page=2`: page 1 → `[q1, q3]`; page 2 → `[q4, q5]`;
  page 3 → `[q6]`.
- 4 questions, `per_page=1`: pages 1–4 return q1, q2, q3, q4 one each; page 5 → `[]`.
- `page=0` or `per_page=0` → `ValueError`.

## Must not change

- `list_questions`' signature and defaults (`page=1`, `per_page=20`).
- Page 1's results (already correct today).
- Oldest-first order by question id; hidden questions are never listed.
- The CLI `list` command's output format.
- Every existing test passes unchanged.

## Done when

- [ ] With 7 visible questions and `per_page=3`, pages 1, 2 and 3 return 3, 3 and 1 questions, and
      together, in order, they contain every question exactly once; page 4 is empty.
- [ ] Hidden questions are still skipped and do not shift the pages.
- [ ] `page < 1` and `per_page < 1` still raise `ValueError`.
- [ ] A test that fails on today's code and passes with the fix is added.
- [ ] Every existing test passes; `ruff check` and `ruff format --check` are clean; CI is green.

## Notes for the implementer

- The page offset is computed inside `list_questions`; the SQL itself is fine.
- `tests/test_questions.py` has `ask_many()` for making several questions quickly.
