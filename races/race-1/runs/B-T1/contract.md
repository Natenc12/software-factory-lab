# Contract for issue #2 (copied verbatim from the issue body, Natenc12/pipeline-lab)

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

