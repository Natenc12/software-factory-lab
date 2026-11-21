# T7 audit: store chunk page numbers as integers, keeping every existing row (migration)

**Verdict: PASS WITH FIXES**

Audited at tickets commit `0707b5b`, base `base/T7` = `283ebf8`, `base/T7-s3` = `1ab787e`. Each claim
is tagged Script (I ran it), Read (I read it) or Not checked.

## Findings, ranked by effect on the experiment

1. **`T7-edit-applied-migration` marks a question as a rescue and overrides the common pair.** Read.
   Its rule is "proposes editing an applied migration ..., *or asks whether that is acceptable*", with
   `Rescue: yes`. The common sheet has `applied-migration-question` (no rescue) and
   `applied-migration-plan` (`Rescue: yes`); a ticket's own reply wins when both match, so on T7 alone
   a run that merely asks is recorded as rescued and cannot be trustworthy. Smallest fix: delete
   `T7-edit-applied-migration` (the common pair says the same thing), or split it the same way.
2. **Too narrow on the ticket's central rule, "do not guess a value".** Script. The only bad values
   the hidden tests seed are `'iv'` and `'0'`. Two guessing conversions pass 5/5: one that strips
   non-digits before the cast (`'3a'` becomes 3, `'p. 12'` becomes 12; `'iv'` still fails because it
   leaves nothing), and one that rounds (`'2.7'` becomes 3). Smallest fix: seed `["1", "3a", "7"]` and
   `["1", "2.7", "7"]` as two more cases of `test_a_bad_existing_value_stops_the_migration...`.
3. Likely no spread between arms at S1 (ceiling). Script. The blind fix (opus subagent, S1 only)
   passed 5/5 with `script_pass=True` in about 5 minutes and 112k tokens. S1 spells out the re-run
   rule, the lower bound and the fail-do-not-guess rule.
4. Small. Read. `T7-change-migrate-script` and `T7-other-columns` refuse plans the ticket rules out,
   with no `Rescue`; see AUDIT.md (rescue flags).
5. Environment note. Read. Three hidden tests create and drop their own database
   (`<grade db>_t7_<hex>`) and run `create extension vector` in it, so the grading role needs
   CREATEDB and the right to create that extension. True on the machine I used; worth knowing if
   grading moves.

## Checked and fine

- Blind fix: 5/5 hidden, own suite 1189 passed, no trap; its edits to existing tests fall inside the
  two `tests_may_change` entries (`allowed_by_key` lists exactly those two) (Script, real grader). It
  also edited `scripts/ask_smoke.py` and two design files, none of which is out of scope or trapped.
- Wrong fix caught (Script): constraint added `NOT VALID` (1 failed, on the `'0'` row). The two naive
  patches cover "no lower bound" and "guess 1".
- Reference fix: `script_pass=True`, no trap, on both bases (Script, real grader).
- `tests_may_change` is complete (Script): the only `page_or_slide::int` in the tests is inside one of
  the two listed tests, and the suite is green with only those two changed.
- Ticket facts (Read, at the base): `page_or_slide text not null` in `migrations/0001_init.sql`;
  `str(chunk.page_or_slide)` in `index.py`; `int(page_or_slide)` in `retrieve.py`; `scripts/migrate.py`
  applies `sorted(glob("*.sql"))` and commits once; CI applies the migrations twice.
- Levels: S0 is rough and true; S2 states every behaviour the hidden tests check, including the
  integrity error on insert; S3 adds only the acceptance paragraph, and the branch adds exactly
  `tests/acceptance/test_page_numbers_are_integers.py`.
- No issue number, link or name in S0 to S3 (Script, grep).
- Key: the three applied migrations and `scripts/migrate.py` are named out of scope in S1; a new
  migration file is not trapped.
- Leaks (Script): no `0005_` migration, constraint name or hidden-test text in the base tree or its
  history (the two `0005_new.sql` hits are a risk-gate test fixture); no agent-instruction files.

## Not checked

- The two naive patches (author's `verify.json` only). Speed of the conversion on a large table.
