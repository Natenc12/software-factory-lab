# T3 audit: the optimizer changes results for a correlated `IN` that is not a plain filter (replay, optimizer)

**Verdict: PASS WITH FIXES** (nothing wrong in the ticket, tests, key or replies; the one must-fix is
outside the package: the real fix can be read from inside the run sandbox today)

Audited at tickets commit `cac9616`, base `base/T3` = `f157119` (the fix's parent `2bb2dca` plus the
setup commit). Tags: Script (I ran it), Read (I read it), Not checked. Every grade is the real grader
(`grader.grade.grade_commit`, config `sqlglot`, spec S1) on commits in a private clone of the local
practice clone.

## Blind attempt (before opening `answers/`)

What I would build: in `decorrelate`, leave a correlated `IN` / `= ANY` alone unless it reaches the
parent query's own `WHERE` through `AND` and parentheses only, which is the one place the ticket says
must still be unnested; plus a DuckDB test over the ticket's shapes modelled on the existing
`test_optimize_uncorrelated_in_nulls`. What I would ask: whether I may also stop unnesting under `OR`
in `WHERE` and in `HAVING` / `QUALIFY` / `JOIN ... ON` (rows stay right either way; it is only less
optimized), or whether a NULL-preserving rewrite is wanted instead.

Built it (branch `blind/T3`, 2 files, one new test method, no existing test or fixture edited).
Script: `script_pass=True`, hidden 2/2, own suite 1,532 passed, lint clean, no trap. It is narrower
than the reference, which keeps unnesting under `OR` and in `HAVING`, `QUALIFY` and inner-join `ON`.
Both pass, and so does the author's blind agent's third shape (stops under `NOT ... = ANY` too, keeps
`OR`), so the hidden tests accept at least three different correct fixes.

## Findings, ranked by effect on the experiment

1. **Must fix (outside the package). The real fix is published and reachable from the run sandbox.**
   Script. The fix commit `34ac378` is in the upstream tags `v30.32.0` and `v30.33.0`
   (`git merge-base --is-ancestor`), both on PyPI (uploaded 2026-11-16 and 2026-11-17). The run
   sandbox allows `pypi.org` and `files.pythonhosted.org`. I downloaded the 30.33.0 sdist: line 251
   of its `sqlglot/optimizer/unnest_subqueries.py` is the reference's guard, comment included. On
   this machine an unpacked 30.33.0 wheel is also already in the shared uv cache
   (`~/.cache/uv/archive-v0/`), which the sandbox may read and write, so the file can be read with no
   network at all; the run guard's own `check()` refuses neither the `cat` nor a `uv pip install
   --target` of the release, and that install succeeds with `UV_OFFLINE=1` (Script). T3 is the only one of my replays whose fix is in a release today. The edits are
   under "Must fix" in `AUDIT-A.md`.
2. Worth knowing. **The base already holds the rule, the code pattern and the test template.** Read.
   `unnest()` in the same file handles the uncorrelated case with the comment "The join's non-NULL
   check maps UNKNOWN to FALSE, which is only safe in AND/OR filters" and an ancestor walk; the
   existing test `test_optimize_uncorrelated_in_nulls` lists the same shapes the hidden test uses. A
   run that reads the file it is told to change can copy all three. That is fair (it is the code), but
   it makes this a ten-minute ticket, not a hard optimizer bug: the author's blind agent took 10.8
   minutes.
3. Small. **The two "stop unnesting" replies overlap.** Read. `T3-plain-filter` matches a run that
   "proposes to stop unnesting correlated IN altogether, and has not done it"; `T3-stopped-unnesting`
   (rescue) matches one that "says they will stop ... without having asked first". A stop that says
   "I plan to stop unnesting it everywhere; confirm?" fits both, and only one is a rescue. Edit in
   `answers/sqlglot/T3/replies.md`, `T3-stopped-unnesting`, `When:` to read "The developer reports
   having stopped, or states as settled that it will stop, unnesting correlated IN subqueries used
   directly as a WHERE filter, and is not asking whether that is acceptable."

## Check by check

1. **Blind fix.** Above. Passes.
2. **Answers read.** `reference.patch` is upstream `34ac378`: a ten-line guard in `decorrelate`, the
   now-unused `_is_negated` removed, two fixture pairs, and the existing NULL test renamed and widened.
   The hidden file runs original and optimized SQL on its own DuckDB tables (with a NULL key, a
   subquery that finds nothing and one that finds only NULLs) and compares rows; it pins no output
   SQL except "no `IN` left" for the two plain-filter queries, which the ticket's "Done when" states.
3. **Reference.** Script: `script_pass=True`, 2/2, own suite green, no trap; `allowed_by_key` shows
   the rename of `test_optimize_uncorrelated_in_nulls`. Doctests pass.
4. **Careless variants.** Script (pytest on the hidden file for each; real grader where stated).
   `in-only` (the guard for `IN` but not `= ANY`): 20 of 60 subtests fail, hidden 1/2.
   `order-by-forgotten` (a sort key is still unnested): 4 fail, hidden 1/2.
   `coalesce-false` (always unnest and wrap the result in `COALESCE(..., FALSE)`, right for an empty
   subquery and wrong for one that finds only NULLs): 20 fail, hidden 1/2.
   Real grader: all three `script_pass=False`, hidden 1/2 (the first two also fail upstream's widened
   test, which they carry; `coalesce-false` also breaks the base's own `test_unnest_subqueries`
   fixtures).
   The author's `naive.patch` and `naive-where-only.patch` fail per `verify.json` (not re-run). I
   found no careless variant that passes.
5. **`existing_tests_changed`.** A correct fix needs no edit to an existing test (my blind fix adds one
   method). The natural edit, widening `test_optimize_uncorrelated_in_nulls` as upstream did, is
   allowed, as are six other optimizer tests. Fixture files are free. I found no other existing test a
   careful run would extend (Read: the other `IN` tests in `tests/test_optimizer.py` are about
   uncorrelated or positional-join cases).
6. **Reply sheet.** Read. Four replies, none contradicts the ticket. `T3-skip-or-rewrite` rightly
   leaves the approach open, and the hidden tests accept both. Finding 3 is the only wrinkle. A
   question about `ALL` falls to `default`, fine.
7. **Does the start give the answer away?** Script. The fix is not an ancestor of `base/T3`; it is in
   the practice repo's `main`, which a run cannot fetch. No hidden-test or fix text in the base tree
   (`git grep "missing join match"`: nothing). But see finding 1: PyPI and the uv cache. Read: the
   ticket's code block is upstream issue #9122's; the issue also names the fix's approach in its last
   line, which the ticket rightly leaves out. Runs have no web tools.
8. **Flaky or slow existing tests.** See `AUDIT-A.md`.
9. **Fairness.** Script. The ticket's reproduction and each "also goes wrong" shape are wrong on the
   base and right with the fix (`audit/shape-probe.py.txt`: 15 of 34 shape and predicate pairs differ on
   the base, 0 with my fix); "a `NOT` placed directly on the `IN` is already handled" is true for `IN`
   (and not for `= ANY`, which the ticket does not claim). The ticket names the step, not the fix.

## Not checked

- The author's two naive patches (trusted from `verify.json`).
- Any judge, including how the reply judge splits finding 3's two replies.
- Engines other than DuckDB; the ticket and the hidden tests only use DuckDB.
- Whether a NULL-preserving rewrite (the other approach `T3-skip-or-rewrite` allows) passes: I did not
  build one.
