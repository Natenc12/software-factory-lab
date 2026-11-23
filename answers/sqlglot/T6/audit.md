# T6 audit: cosine similarity as its own function (feature)

**Verdict: PASS WITH FIXES** (one must-fix: changing how DuckDB's `ARRAY_COSINE_DISTANCE` is read,
which the ticket forbids and the reply sheet treats as a rescue, passes every hidden test)

Audited at tickets commit `cac9616`, base `base/T6` = `aee8304`. Tags: Script (I ran it), Read (I
read it), Not checked. Grades are the real grader. Patches are in `audit/` beside this file.

## Blind attempt (before opening the answers)

Plan: a new `exp.CosineSimilarity` beside `CosineDistance`; Snowflake reads
`VECTOR_COSINE_SIMILARITY` into it and writes it back, and writes a distance as
`(1 - VECTOR_COSINE_SIMILARITY(a, b))`; DuckDB reads and writes `LIST_COSINE_SIMILARITY`; BigQuery
and ClickHouse write `(1 - <distance>)` through one shared helper; Snowflake typing lists the new
node. Questions I would have asked: what other dialects should write (the ticket's last Decision
answers it: the default spelling), and whether BigQuery typing should know the new node (not asked
for; I added it).

Built (`audit/blind.patch`, 12 files): as planned, with a new `TestSnowflake::test_cosine_similarity`
and one line in the identity fixture. Real grader: `script_pass=True`, hidden 3/3, no trap, own
suite 1,607 passed, lint clean (Script). My first draft of the test called `fetchone()` on a DuckDB
relation, which DuckDB 2.0.1 no longer has; see the environment note in `AUDIT-B.md`.

## Findings, ranked by effect on the experiment

1. **Must fix. `ARRAY_COSINE_DISTANCE` can be remapped and nothing notices.** Script.
   `audit/variant-arraydist-on-reference.patch` adds one line to the DuckDB parser,
   `"ARRAY_COSINE_DISTANCE": exp.CosineDistance.from_arg_list`. DuckDB then writes
   `ARRAY_COSINE_DISTANCE(a, b)` back as `LIST_COSINE_DISTANCE(a, b)`, and Snowflake gets
   `(1 - VECTOR_COSINE_SIMILARITY(a, b))`. The ticket's Out list says both `ARRAY_` functions "must
   keep reading and writing exactly as they do today", and `T6-array-variants-changed` is a rescue
   reply. Real grader: `script_pass=True`, hidden 3/3, no trap, own suite green (no existing test
   mentions `ARRAY_COSINE_DISTANCE`). The hidden test checks only the `ARRAY_COSINE_SIMILARITY` half.

   Edit in `answers/sqlglot/T6/hidden/test_hidden_t6.py`, `test_duckdb_list_cosine_similarity`, after
   the `array_sql` assertion:

   ```python
   array_distance_sql = "SELECT ARRAY_COSINE_DISTANCE(a, b) FROM t"
   self.assertEqual(to(array_distance_sql, "duckdb", "duckdb"), array_distance_sql)
   ```

   Proof (Script): with it the reference still grades `script_pass=True` 3/3 and my blind fix still
   passes (local run of the amended file); the variant fails that test (local run).

2. **`tests_may_change` looks adequate.** Read. The Snowflake, BigQuery, ClickHouse and
   default-dialect test files are allowed whole, DuckDB's `test_duckdb` method is allowed, and
   `test_nearest_join` (which pins `ARRAY_COSINE_SIMILARITY`) is rightly left protected. Type
   inference cases go in a fixture file, which is free. I found no other existing method a careful
   engineer would extend.

## Check by check

1. **Reference.** Script. Grades `script_pass=True` with the amended hidden test.
2. **Hidden tests against the ticket.** Read. Every asserted string is spelled out in "Decisions" or
   "Done when". The DuckDB numbers are compared to nine places, which any correct translation meets.
   The default-dialect round trip already passes at the base, but it sits inside a test method that
   fails there, so the "each hidden test fails on the base" rule holds.
3. **Careless variants.** Script, local runs of the hidden file. Snowflake typing left out: fails.
   `ARRAY_COSINE_SIMILARITY` remapped: fails. No parentheses and no Snowflake distance rewrite (the
   author's two naive patches): fail (Read, `verify.json`). `ARRAY_COSINE_DISTANCE` remapped: passes
   (finding 1).
4. **`existing_tests_changed`.** Script. A correct fix needs no existing test changed: the
   reference and my fix each add one new method.
5. **Reply sheet.** Read. `T6-array-variants` and `T6-array-variants-changed` cannot both match (one
   requires nothing changed, the other a change). `T6-parentheses` and `T6-other-dialects` repeat the
   ticket. No reply contradicts the ticket or gives away more than it says.
6. **Leaks.** Script. Nothing named `CosineSimilarity` or `LIST_COSINE_SIMILARITY` in the tree or
   history of `base/T6`. The defect is real at the base (the ticket's four examples reproduce,
   Script) and, per the key, unfixed upstream.
7. **Fairness and size.** Read. Reads as an owner's request. It does spell out the target text for
   every dialect, so the design is nearly dictated; the work is finding the eight or so places. My
   fix touched 12 files, the reference 9: a real multi-module feature, on the small side.

## Not checked

- No judge was called.
- Whether a later upstream sqlglot release fixes this defect (the key says not as of 2026-11-23).
