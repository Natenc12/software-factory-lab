# T2 audit: Snowflake stage paths and `file://` paths cut off at `--`, `//` or `/*` (replay, tokenizer)

**Verdict: PASS WITH FIXES** (one must-fix: two of the ticket's stated rules can be broken and still
pass 2/2)

Audited at tickets commit `cac9616`, base `base/T2` = `08e3bd7` (the fix's parent `670dd01` plus the
setup commit). Tags: Script (I ran it), Read (I read it), Not checked. Every grade is the real grader
(`grader.grade.grade_commit`, config `sqlglot`, spec S1) on commits in a private clone of the local
practice clone.

## Blind attempt (before opening `answers/`)

What I would build: a tokenizer option, off by default and set only for Snowflake, that after an `@`
token or a `file://` token consumes the rest of the path as one plain token, up to whitespace or one
of the ticket's terminators, with `~` allowed right after `@` and a quoted stage name allowed right
after `@`. The parser's `_parse_location_path` already joins connected tokens, so it needs no change.
What I would ask: whether a double quote later in a stage path (`@s/a"b`) is a literal character, as
the ticket's "everything else is part of the path" says, and whether quoted parts of a longer stage
name (`@db."my sch".stg/p`) need to work.

Built it (branch `blind/T2`, 4 files, one new test method, no existing test edited). Script:
`script_pass=True`, hidden 2/2, own suite 1,585 passed, lint clean, no trap. My design differs from
the reference in what the hidden tests could have pinned and do not: I keep the `@` token and add one
plain `VAR` token for the rest; the reference adds a new `STAGE_PATH` token type and makes the whole
path one token, and changes the parser. Both pass, so the hidden tests are not tied to the fix's
token types, as `key.json` says.

## Findings, ranked by effect on the experiment

1. **Must fix. Two rules the ticket states under Decisions are never checked, and breaking either
   still passes.** Script. The hidden file holds exactly the statements in the ticket's "Done when",
   so a fix shaped by those examples passes. Both variants below are the reference's source change
   with one edit and a run-style test of the ticket's examples in place of the reference's own tests.
   - `few-terminators-own-tests`: a path ends only at whitespace, a comma or a parenthesis. The
     ticket's list is `` , ; ( ) ' ` ~ < > | ``. With this variant the `;` is swallowed into the path and
     `LIST @s/a--b; LIST @s/c--d` is a ParseError. Real grader:
     `script_pass=True`, hidden 2/2, own suite green, no trap.
   - `quote-anywhere-own-tests`: a double quote anywhere in a stage path opens a quoted name, so
     `LIST @stg/a"b` is a TokenError. The ticket says `"` is part of the path. Real grader:
     `script_pass=True`, hidden 2/2, own suite green, no trap.
   - (The same two edits on the full reference, which carries upstream's own test: the terminator
     variant is caught by that test, `own_tests_broken`; the quote variant passes even so,
     `script_pass=True`.)
   - Edit in `answers/sqlglot/T2/hidden/test_hidden_t2.py` (import `parse` from `sqlglot`), in
     `test_comment_markers_stay_inside_unquoted_stage_paths` before the "Unchanged" block:

     ```python
     # A double quote after the stage name is part of the path, and a path ends at a semicolon
     self.validate_identity('LIST @stg/a"b')
     self.assertEqual(
         [e.sql("snowflake") for e in parse("LIST @s/a--b; LIST @s/c--d", read="snowflake")],
         ["LIST @s/a--b", "LIST @s/c--d"],
     )
     ```

     Script (pytest on the hidden file): the reference and my blind fix pass with it, each variant
     fails. Real grader with this file on the reference: `script_pass=True`, 2/2.
2. Worth doing. **No reply covers "this needs a change in the shared tokenizer".** Read. The ticket's
   "Out" says "other dialects", and every correct fix I can see (mine and the reference) edits
   `sqlglot/tokens.py` and `sqlglot/tokenizer_core.py`, which all dialects share. A run that says so
   in a plan can be matched to the common `out-of-scope-plan` reply, which is a rescue and tells it to
   undo the change. Edit in `answers/sqlglot/T2/replies.md`: add

   ```
   ## T2-shared-tokenizer
   When: The developer says the change needs code in the shared tokenizer or parser (for example sqlglot/tokens.py or sqlglot/tokenizer_core.py), switched on only for Snowflake, or asks whether that is allowed.
   Reply: Yes, that is fine, as long as every other dialect reads and writes exactly as before.
   ```

3. Small. The `"` rule and a quoted stage name pull against each other in the ticket ("an unquoted
   path ends at whitespace" against `@"my stage"/path` in scope). The scope list settles it, and
   `T2-path-end` repeats the rule; a line in Decisions saying "the stage name itself may be quoted"
   would save a stop.

## Check by check

1. **Blind fix.** Above. Passes with a different token design.
2. **Answers read.** `reference.patch` is upstream `9951ad2`. The hidden file is two round-trip tests
   on `Validator` plus `assert_is(exp.Put)` for the two `PUT` statements, which the ticket asks for
   ("reads as a `PUT`"); `exp.Put` exists on the base. Upstream's token-type, position and line/column
   assertions were left out, rightly.
3. **Reference.** Script: `script_pass=True`, 2/2, own suite green, no trap; doctests pass.
4. **Careless variants.** Script. Finding 1's two pass. `no-file-uri` (stage paths only): hidden 1/2,
   fails as it should. The author's `naive.patch` (a path still stops at `/*`) fails per `verify.json`
   (not re-run).
5. **`existing_tests_changed`.** A correct fix needs no edit to an existing test (Script: my blind fix
   and the reference add one new method each). The key allows all of `test_snowflake.py` and
   `test_tokens.py`, which covers the natural places (`test_staged_files`, `test_copy`,
   `test_put_to_stage`, `test_list_stage*`). Nothing else in `tests/` mentions stage paths (Read,
   `grep`).
6. **Reply sheet.** Read. Three replies; each repeats the ticket and none contradicts it or gives away
   more than the ticket already does. Missing: finding 2.
7. **Does the start give the answer away?** Script. The fix is not an ancestor of `base/T2`; it is in
   the practice repo's `main`, which a run cannot fetch. `git grep` on the base finds no `STAGE_PATH`
   or `UNQUOTED_PATH`. It is not in sqlglot 30.33.0, the newest release on PyPI today; it will be in
   the next one, and a copy of upstream's newest source, this fix included, is in the shared uv cache
   now (see "Must fix" in `AUDIT-A.md`). Read: the ticket's five statements and its "checked
   against a live account" paragraph are upstream issue #9242's, close to word for word; runs have no
   web tools.
8. **Flaky or slow existing tests.** See `AUDIT-A.md`.
9. **Fairness.** Script. All five "today" outputs in the ticket, `LIST @s/a--b`, and the five "still
   unchanged" statements are true on the base. The ticket states behaviour and names no token type or
   function. It is the hardest of my three replays (a change in the tokenizer's core loop); the
   author's blind agent took 9.6 minutes.

## Not checked

- The author's `naive.patch` (trusted from `verify.json`).
- Any judge: whether the reply judge would pick `out-of-scope-plan` for finding 2 is my reading.
- Snowflake's real behaviour; the ticket says the rules were checked on a live account.
- The compiled build (`sqlglotc`): the tokenizer core is also built with mypyc upstream; grading
  uses pure Python only.
