Fixes #1.

**Problem:** `list_questions` passed `max((page - 1) * per_page - 1, 0)` as the SQL offset, so page 2 started one row early and repeated the last question of page 1 (pages after 2 were each shifted back by one; page 1 was clamped).

**Change:** the offset is now `(page - 1) * per_page`. Signature, defaults, ordering and the `ValueError` checks are unchanged.

**Tests:** two new tests in `tests/test_questions.py` (7 questions / 3 per page cover every question once in pages 3, 3, 1 with page 4 empty; hidden questions take no slot). Both fail on `main` and pass with the fix.

Merge brief (owner page, local): `~/repos/pipeline-bench/runs/A-T1/brief.html`
