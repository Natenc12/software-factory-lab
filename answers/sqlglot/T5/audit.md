# T5 audit: SQLite `UPDATE OR <action>` (replay)

**Verdict: PASS WITH FIXES** (one must-fix: reporting "unsupported" only for the three dialects the
ticket names passes every hidden test)

Audited at tickets commit `cac9616`, base `base/T5` = `06e1c2b` (parent of the real fix `68ef75b`
plus the setup commit). Tags: Script (I ran it), Read (I read it), Not checked. Grades are the real
grader. Patches are in `audit/` beside this file.

## Blind attempt (before opening the answers)

Plan: add an `alternative` argument to `exp.Update`; read `OR <action>` in the base parser's
`_parse_update` (upper-cased, parse error if the word is not one of the five); write it from a
generator flag that is on for SQLite and for the default dialect and reports "unsupported"
everywhere else, including Teradata's own `update_sql`. Questions I would have asked: should other
dialects refuse to *read* it (the ticket's Out line reads that way), and what should the
non-raising output be for a dialect that cannot express it (drop the clause, I assumed).

Built (`audit/blind.patch`): exactly that, with the test cases added inside the existing
`TestSQLite::test_ddl` next to the `INSERT OR` cases. Real grader: `script_pass=True`, hidden 4/4,
no trap, own suite 1,603 passed, lint clean; `existing_tests_changed` lists `test_ddl modified`
under `allowed_by_key` (Script).

My fix reads `UPDATE OR` in every dialect, which the ticket puts out of scope and the reply
`T5-reading-elsewhere` refuses. The hidden tests do not look, so it passes. See finding 3.

## Findings, ranked by effect on the experiment

1. **Must fix. A block-list passes.** Script. `audit/variant-blocklist-on-reference.patch` turns
   the reference inside out: `UPDATE OR` is read and written by every dialect, and reported only for
   Postgres, MySQL and Teradata, the three the ticket gives as examples. Snowflake, BigQuery, T-SQL,
   DuckDB and Oracle then get `UPDATE OR IGNORE t SET ...` passed through silently, the very thing
   the ticket's third Decision forbids. Real grader: `script_pass=True`, hidden 4/4, no trap.

   Edit in `answers/sqlglot/T5/hidden/test_hidden_t5.py`,
   `test_dialects_without_update_or_report_it`: change the loop to
   `for dialect in ("postgres", "mysql", "teradata", "snowflake", "bigquery", "tsql"):`.
   Proof (Script): with it the reference still grades `script_pass=True` 4/4 and my blind fix still
   passes (local run of the amended file); the block-list variant fails that test (local run).

2. **`tests_may_change` covers the natural places but not every dialect file.** Read. The eight
   listed files cover SQLite, the default dialect and the three named targets. A run that also
   checks a target the ticket does not name (T-SQL has its own `_parse_update`; DuckDB and Snowflake
   are the usual cross-checks) would add a line to an existing method in an unlisted file and trip
   `existing_tests_changed`. The same thing is shown by Script on T4. Edit in `key.json`: replace the
   five dialect entries with `"tests/dialects/*.py"` and add `"tests/test_transpile.py"`.

3. **The Out line about other dialects is not enforced.** Script. My blind fix reads `UPDATE OR`
   as Postgres and passes. That is harmless for grading as it stands; say in the README whether it
   is meant. If it should fail, add to `test_update_or_without_an_action_is_an_error`:
   `with self.assertRaises(ParseError): parse_one("UPDATE OR IGNORE t SET b = 'x'", read="postgres")`
   (the reference passes this; my fix and the author's `naive.patch` would fail it). I would leave
   it out: a run that asks is told, and a run that does not ask has only widened what is read.

4. **"MySQL has nothing like it" is not quite true.** Script and Read. MySQL has `UPDATE IGNORE`,
   and sqlglot already maps MySQL's `INSERT IGNORE` to SQLite's `INSERT OR IGNORE` (Script, at the
   base). A run that knows this could map `UPDATE OR IGNORE` to `UPDATE IGNORE` for MySQL and would
   then fail the hidden test, which uses exactly `OR IGNORE` for MySQL. The ticket does name MySQL
   explicitly, so the grade would be defensible, but it punishes knowledge. Edit: in `S1.md` and in
   the hidden test swap MySQL for BigQuery, or add a reply `T5-mysql-ignore` ("When: the developer
   asks whether MySQL's UPDATE IGNORE should be used. Reply: No, report it as unsupported for MySQL
   too in this change.").

## Check by check

1. **Reference.** Script. `reference.patch` is byte-for-byte the real fix's diff; it grades
   `script_pass=True` with the amended hidden test too.
2. **Hidden tests against the ticket.** Read. Every assertion is in "Done when". The test class
   extends the repo's own `tests.dialects.test_dialect.Validator`; it does not check the private
   argument name.
3. **Careless variants.** Script, local run of the hidden file: no upper-casing fails
   (`update or ignore`); the author's `naive.patch` fails 1/4 (Read, `verify.json`). The block-list
   passes (finding 1).
4. **`existing_tests_changed`.** Script. A correct fix needs no existing test changed (the real fix
   adds a new method). Adding cases inside the existing SQLite test is allowed by the key.
5. **Reply sheet.** Read. The four replies agree with the ticket's Decisions and with each other;
   none gives away more than the ticket already says. A question about the non-raising output falls
   to `default`, which is right since nothing checks it.
6. **Leaks.** Script. `git log -S` and `git grep` on `base/T5` for `SUPPORTS_UPDATE_OR`,
   `CONFLICT_ALGORITHMS` and `test_update_or`: nothing. The fix is not an ancestor of `base/T5`.
   The fix is in no upstream release tag in the clone (the newest is `v30.33.0`), so it is not on
   PyPI yet; it will be in the next release, and the run sandbox can reach PyPI (see `AUDIT-B.md`,
   must-fix 3).
7. **The ticket's example.** Script. All five actions raise the quoted `ParseError` at the base, and
   `INSERT OR REPLACE` round-trips.
8. **Fairness and size.** Read. Written as an owner would write it; the fix is not named. About
   forty lines across six or seven files, in line with the README.

## Not checked

- No judge was called. The upstream issue text was not compared with the ticket (no web access).
