Ticket: #10 (run B-T5). Contract as amended by the owner at Stop 1: the cache key is the class and the question text, and a cached answer is only used while the class's material is unchanged.

- `src/lab/ask.py`: module-level cache, `clear_answer_cache()`. `answer()` skips the provider on a hit and still writes the `answers` row as before.
- `tests/conftest.py`: autouse fixture empties the cache around every test.
- `tests/test_answer_cache.py`: one test per Example of done and per Must not change line.

Merge brief (owner page, local): `~/repos/pipeline-bench/runs/B-T5/brief.html`

risk:high (src/lab/ask.py). Needs the owner's owner-ok label to merge; agents do not add it.
