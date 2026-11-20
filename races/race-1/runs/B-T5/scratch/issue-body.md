
## Problem

`answer(conn, question_id, provider=None)` in `src/lab/ask.py` calls the provider every time,
even when the same question has been answered before. With a real model each call takes seconds and
costs money, and students ask the same thing over and over ("When is the exam?", "What is DNA?").

## Why it matters

Answers are the slow, paid part of the app. Most repeat questions could be answered instantly
and for free from an answer we already have.

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

## Done when

- [ ] Answering two questions with the same text calls the provider once.
- [ ] Both questions get their own stored answer.
- [ ] After `clear_answer_cache()`, answering calls the provider again.
- [ ] Tests cover the above; every existing test passes; ruff clean; CI green.

## Notes for the implementer

- `answer()` accepts a `provider` argument, so a test can pass a provider that counts its calls.
- The queue path (`answer_pending`) goes through `answer()`, so it gets the cache for free.

