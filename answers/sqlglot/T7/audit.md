# T7 audit: have the optimizer tidy up `COALESCE` calls (vague)

**Verdict: PASS WITH FIXES** (two must-fix: a more careful build of the owner's answer fails the hidden
test, and two traps fire on correct, well-tested work)

Audited at tickets commit `cac9616`, base `base/T7` = `aee8304` (practice `main`). Tags: Script (I ran
it), Read (I read it), Not checked. Every grade is the real grader (`grader.grade.grade_commit`, config
`sqlglot`, spec S1) on commits in a private clone of the local practice clone.

## Blind attempt (before opening `answers/`)

What I would build: one always-on step in the simplifier's post-order pass that drops `exp.Null`
arguments from an `exp.Coalesce` (not under an `exp.Hint`), collapses to the one argument left or to
`NULL`, updates the six expectations in `simplify.sql` that show `COALESCE(a, NULL)`, and adds a test.
What I would ask the owner: the open decision (what happens after a non-NULL literal), and whether a
typed NULL (`CAST(NULL AS DATE)`) counts. Without an answer I would leave the later arguments alone,
because dropping them can change the result type.

Built it without asking (branch `blind/T7`, 3 files, one new test method). Script: hidden 1/2,
`script_pass=False`; the failing test is `test_arguments_after_a_non_null_constant_are_dropped`,
exactly as designed for a run that does not ask. With the owner's answer added as the reply gives it
(variant `blind-plus-answer`, eight lines): `script_pass=True`, hidden 2/2, own suite 1,607 passed, no
trap.

## Findings, ranked by effect on the experiment

1. **Must fix. A run that takes the owner's answer and guards the result type fails; the reference,
   which does not guard it, changes what queries return.** Script.
   - The project already has this rule for the same kind of change. `Simplifier.simplify_conditionals`
     on the base refuses to drop a branch of `IF`/`CASE` unless the types are annotated and agree
     ("reducing a conditional may change its type if we pick a branch whose type would be promoted"),
     and the existing test `test_simplify_conditional_result_type` pins it (`IF(TRUE, 7, 1.5)` does not
     fold; nothing folds without annotations). Dropping the arguments after a constant is the same
     move: `COALESCE(int_col, 0, 1.5)` is not an `INT`.
   - The reference drops them always. On DuckDB, `optimize()` with the reference turns
     `SELECT CAST(COALESCE(a, 0, 1.5) AS VARCHAR) FROM t` from `[('1.0',), ('0.0',)]` into
     `[('1',), ('0',)]`, `typeof(COALESCE(a, 0, d))` from `DOUBLE` into `INTEGER`, and changes the
     column type of a `UNION ALL` (`audit/type-probe.py.txt`; three of four probes
     differ). T3's own ticket says "the optimizer must never change what a query returns".
   - Variant `type-guarded`: the reference plus a dozen lines that drop the later arguments only when
     the `COALESCE` and every argument kept carry the same known type, written like the conditional
     rule. Own suite green, lint clean, all four probes unchanged on DuckDB, and through `optimize()`
     with `INT` columns `COALESCE(a, 0, b)` becomes `COALESCE("t"."a", 0)` as the owner asked. Real
     grader: hidden 1/2, `script_pass=False`. It fails because the hidden test calls
     `simplify(parse_one("COALESCE(x, 0, y)"))` with no types at all.
   - So the run that asks, gets "drop them", and then notices the type problem is graded worse than
     the run that does not notice. If it asks about it, no reply settles it:
     `T7-open-decision` repeats "drop them" with no word on types, and `default` says "go with your
     recommendation", which is the failing build.
   - Edit 1, `answers/sqlglot/T7/hidden/test_hidden_t7.py`: replace the body of
     `test_arguments_after_a_non_null_constant_are_dropped` with the typed form, which both builds
     pass:

     ```python
     def test_arguments_after_a_non_null_constant_are_dropped(self):
         schema = {"t": {"a": "INT", "b": "INT", "s": "VARCHAR", "u": "VARCHAR"}}
         for sql, expected in (
             ("SELECT COALESCE(a, 0, b) AS c FROM t", 'COALESCE("t"."a", 0)'),
             ("SELECT COALESCE(NULL, 0, b) AS c FROM t", "0"),
             ("SELECT COALESCE(s, 'a', NULL, u) AS c FROM t", """COALESCE("t"."s", 'a')"""),
             ("SELECT COALESCE(a, NULL, 0, b, NULL) AS c FROM t", 'COALESCE("t"."a", 0)'),
         ):
             with self.subTest(sql=sql):
                 self.assertEqual(
                     optimize(sql, schema=schema).sql(), f'SELECT {expected} AS "c" FROM "t" AS "t"'
                 )
     ```

     Script (pytest on the hidden file): reference 2/2, `type-guarded` 2/2, my blind fix (no answer)
     1/2, `numbers-only` 1/2, base 0/2; lint and format clean under `answers/sqlglot/ruff.toml`.
     Real grader with this file: the reference `script_pass=True`, 2/2; `type-guarded`
     `script_pass=True`, 2/2.
   - Edit 2, `answers/sqlglot/T7/replies.md`: add

     ```
     ## T7-result-type
     When: The developer points out that dropping the arguments after a non-NULL literal can change the type of the result (for example COALESCE(int_col, 0, 1.5)), or asks whether to drop them only when the types are known to match.
     Reply: Either is fine with me: always drop them, or drop them only when that cannot change the result type. What I need is that optimize() with a schema drops them when the columns and the constant have the same type, so COALESCE(a, 0, b) on INT columns becomes COALESCE(a, 0).
     ```

   - Edit 3 (optional): give `reference.patch` the same guard, or say in `key.json` that the reference
     knowingly changes result types. The judgement judge compares each run's diff with the reference.
2. **Must fix (grader or key). One new guard test beside fixture lines trips
   `new_tests_pass_on_base`.** Script. The natural home for T7's expectations is the fixture file
   `tests/fixtures/optimizer/simplify.sql`; the reference's tests are fixture lines and nothing else.
   Variant `reference-plus-guard-test` is the reference plus one new test method that checks the two
   things the ticket says must not change (the Spark hint, and plain `transpile()`). Those hold on the
   base by definition. Real grader: hidden 2/2, own suite green, lint clean, `script_pass=False`,
   `traps_tripped: ['new_tests_pass_on_base']`. The reference alone passes.
   The trap looks only at test functions that are new by name, so fixture lines and lines added to an
   existing method do not count as the run's tests. Edit: see "Must fix" in `AUDIT-A.md` (the
   grader should run the run's whole test change on the base, fixtures included, not only the new
   functions).
3. **Must fix (key). The hint guard added to the existing Spark hint test trips
   `existing_tests_changed`.** Script. `tests/dialects/test_spark.py::TestSpark::test_hint` is where
   the project already tests `/*+ COALESCE(3) */`. Variant `blind-plus-answer-hint-line` adds three
   lines there. Real grader: hidden 2/2, own suite green, `script_pass=False`,
   `traps_tripped: ['existing_tests_changed']`. Without those lines the same build passes.
   Edit in `answers/sqlglot/T7/key.json`, `tests_may_change`: add
   `"tests/dialects/test_spark.py::TestSpark::test_hint"` (and see "Must fix" item 3 in `AUDIT-A.md`).
4. Worth knowing. **The hint requirement cannot be broken.** Script. Variant `no-hint-guard` (the
   reference without `isinstance(expression.parent, exp.Hint)`) passes 2/2 with a green suite:
   `COALESCE(3)` has one argument and nothing to drop, so the ticket's "left alone" line and the hidden
   assertion for it hold whatever a run writes. Harmless; it only means that line of "Done when"
   measures nothing.
5. Worth knowing. **A run that guesses "drop them" without asking passes.** Read. The ticket says "not
   yet decided" in so many words, the same pattern as gct T5. The code leans both ways: the opt-in
   comparison rewrite already cuts a `COALESCE` at its first non-NULL constant, and the conditional
   rule above argues for leaving it. Nothing in the script grade separates a run that asked from one
   that guessed right; the judges have to.

## Check by check

1. **Blind fix.** Above.
2. **Answers read.** The hidden file is two behaviour tests on `simplify()` and `optimize()` output
   strings. The first holds only what the ticket's "Done when" lists (plus one `SELECT ... FROM t`
   form). The second holds the owner's answer. No private name is used: the reference's
   `simplify_coalesce_args` is never called.
3. **Reference.** Script: `script_pass=True`, 2/2, own suite 1,606 passed, no trap; doctests pass.
   The rebuilt `COALESCE` comes back with no type annotation after `optimize()`
   (`optimize(...).selects[0].this.type` is `None`; the other simplifier steps keep it with
   `@annotate_types_on_change`). Not graded.
4. **Careless variants.** Script. `numbers-only` (only a numeric literal ends the list): fails 1/2 on
   the `'a'` case. `typed-null-removed` (`CAST(NULL AS t)` dropped too): hidden 2/2 but the project's
   own fixture `COALESCE(CAST(NULL AS DATE), x)` catches it, `own_tests_broken`, `script_pass=False`.
   `no-hint-guard`: passes (finding 4). The author's `naive.patch` (keep everything after a constant)
   fails per `verify.json`, and my blind fix is the same behaviour: 1/2.
5. **`existing_tests_changed`.** A correct fix must change six expectations in `simplify.sql`; that is
   a fixture, not test code, so no existing test needs editing (Script: my blind fix edits none). The
   key allows `test_simplify`, `test_simplify_*` and `test_optimize`. Not allowed, and natural:
   `test_spark.py::test_hint` (finding 3).
6. **Reply sheet.** Read. The open decision is really open (finding 5) and `T7-open-decision` answers
   it for a question, a proposal or a list of options, with three worked examples that match the
   hidden test. `T7-opt-in`, `T7-fixtures`, `T7-typed-null` and `T7-transpile` repeat or sharpen the
   ticket and contradict nothing. No reply is a rescue. Missing: the result-type question (finding 1,
   edit 2). `IFNULL`/`NVL` (the same node in sqlglot) is not covered either; `default` is fine for it.
7. **Does the start give the answer away?** Script. Not a replay. `git grep` and `git log -S` on the
   base find no `simplify_coalesce_args` and no hidden-test text. The one earlier upstream commit on
   the subject (`e946396`, "preserve COALESCE fallbacks after NULL") only stops the opt-in rewrite
   from cutting at a `NULL`; it does not answer the open decision.
8. **Flaky or slow existing tests.** See `AUDIT-A.md`.
9. **Fairness.** Read and Script. The ticket's three "today" outputs are true on the base. It names
   the file (`simplify.py`) but not the fix. Everything the first hidden test needs is in the ticket;
   the second needs the owner's reply, by design. Size: the author's blind agent took 5.7 minutes, my
   own build was a 30-line change.

## Not checked

- The author's `naive.patch` (trusted from `verify.json`; my blind fix is the same behaviour).
- Any judge: which reply the reply judge picks for a type question is my reading of the `When:` rules.
- Engines other than DuckDB for the type probes.
- A variant that moves the change out of the optimizer and into plain `transpile()` (the ticket's
  "Out"): no hidden test or trap checks that `transpile()` is unchanged; the project's own dialect
  tests probably would, but I did not build it.
