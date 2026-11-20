# Contract for issue #10 (copied verbatim from the issue body, 2026-11-20)

Source: `gh issue view 10 --repo Natenc12/pipeline-lab --json body`. Owner amendments, if any, are recorded at the end.

## Scope

**In:**

- An in-memory cache in `src/lab/ask.py`, keyed by question text: `answer()` looks the text up
  before calling the provider and stores the provider's answer on a miss.
- `clear_answer_cache()` in `src/lab/ask.py`.
- Tests.

**Out:** A cache table or any migration, cache expiry or size limits, caching in the job queue code,
changes to the provider interface, and normalising question text (case, punctuation).

## Decisions

- The cache key is the question text exactly as stored (`ask_question` already strips spaces). No
  lower-casing or other normalising.
- The cache lives in memory, per process: a module-level dict in `src/lab/ask.py`. No new table.
- On a hit, `answer()` still stores (or replaces) the `answers` row for this question and returns it,
  exactly as on a miss; only the provider call is skipped.
- `lab.ask.clear_answer_cache()` empties the cache (tests call it to start clean).

## Examples of done

- Ada asks "What is DNA?" and it is answered: the provider is called once. Ben then asks
  "What is DNA?": `answer()` returns the same body without calling the provider, and Ben's question
  gets its own `answers` row.
- Answering the same question twice in a row calls the provider once.
- After `clear_answer_cache()`, the next `answer()` for that text calls the provider again.

## Must not change

- For any question, `answer()` returns the same answer body it would return without the cache.
- `answer()`'s signature and the `Answer` it returns; one `answers` row per question, replaced when
  answered again.
- Hidden questions are still refused (`ValueError`); a missing question still raises `LookupError`.
- Every existing test passes unchanged.

## Owner amendment (Stop 1 answer, 2026-11-20, verbatim)

> Good catch: answers depend on the class's own material, so a cache keyed by text alone would hand one class another class's answer. Amend it: the cache is per class. The cache key is the class and the question text, so the same text asked in two classes is answered separately, each from its own class's material. A cached answer is only used while the class's material is unchanged: after `set_material`, the next answer comes from the new material. Everything else stays as the ticket says. Go ahead.

Effect on the lines above (as the owner stated; everything else unchanged):
- Decisions, 1st line, now reads: the cache key is the class and the question text exactly as stored (no normalising). A cached answer is only used while the class's material is unchanged; after `set_material`, the next answer comes from the new material.
- Scope In, 1st line: the cache is keyed by class and question text (not text alone).
