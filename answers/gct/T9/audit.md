# T9 audit: let a student replace an uploaded file, keep its versions, and restore an earlier one (long)

**Verdict: PASS WITH FIXES** (two must-fix items: one reply, one hidden-test gap)

Audited at tickets commit `2cdf7fd` (branch `claude/gct-tickets-stage2`), base `base/T9` = `283ebf8`,
`base/T9-s3` = `4528b8c`. Each claim is tagged Script (I ran it), Read (I read it) or Not checked.
All grades below are the real grader (`grader.grade.grade_commit`, config `gct`), on databases named
`grade_audit2_*` that the grader dropped afterwards.

## Findings, ranked by effect on the experiment

1. **Must fix. The reply `T9-history` is left over from the first version of the ticket and
   contradicts it.** Read. Its rule is "asks whether to keep a history of versions, or to let a
   student roll back to an earlier version", and its reply is "Not in this ticket. Only the current
   version and the incoming one." Since the second round, S0 to S3 require exactly that history
   (rules 6 and 7, part 4) and a restore (part 5). A run that asks anything about history or rolling
   back (for example "should a failed version also be restorable?" or "do we keep every version or
   only the last good one?") is told to drop half the ticket, and then fails four of the nine hidden
   tests. `BLIND-FIXES-STAGE2.md` shows the ticket was lengthened twice; this reply was not brought
   along. Fix: delete `T9-history`, or replace it with a reply that answers questions about history
   and restore from the ticket (for example "Yes, keep every version, failed ones included; only a
   published version can be restored, as the ticket says").
2. **Must fix. Replacing a failed file may overwrite its version record and still pass 9/9.**
   Script. On top of `reference.patch` I changed one statement in `replace_file`: when the file is
   `failed`, update its newest `file_versions` row (new filename, new bytes, back to `pending`)
   instead of inserting the next version. That breaks rule 6 ("every upload is a numbered version
   ... a failed version keeps its number"): the failed upload disappears from the history and the
   fixed upload becomes version 1. Hidden tests: 9 passed. `test_replacing_a_failed_file_processes_it_like_a_new_upload`
   never reads `/versions`, and every other version test starts from a ready file. Fix: add at the
   end of that test
   `assert versions(client, file_id) == [(2, "fixed.pdf", "published", None, True), (1, "broken.pdf", "failed", "unparseable", False)]`
   (Script: with that assertion added, the reference passes 9/9, the blind fix passes 9/9, and my
   careless variant fails only that test).
3. **S0 cannot be passed, by any run, even one that asks.** Read. S0 names neither the two new keys
   on `GET /files/{file_id}` (`replacement`, `replacement_failed_reason`), nor their values, nor the
   `file_busy` kind, nor the restore route, its reply body or its three refusal kinds, nor the
   shape of a version entry. The hidden tests assert all of them by exact name, and no reply in
   `replies.md` supplies any of them (the common `default` reply says "go with your
   recommendation"). If T9 is run at S0, every S0 cell fails on the hidden tests for every arm, so
   it measures nothing. Fix: either do not run T9 at S0, or add one reply
   (`T9-names`, "asks what the new keys, routes, error kinds or reply shapes should be called") that
   gives the S1 Decisions list.
4. Small. The hidden test pins the staged file's name. Read.
   `test_a_ready_file_keeps_answering_until_the_new_version_is_published` asserts
   `Path(new_ref).name == "week-1-v2.pdf"`. The ticket never says the staged copy keeps the upload's
   name. Any fix that stages through the existing `gct.staging.stage` passes (it writes
   `<staging>/<uuid4>/<filename>`, and its docstring says the basename must stay the filename because
   the citation label comes from it), and both the reference and the blind fix do. A run that stages
   replacements under another name fails one test for a choice the ticket left open. Fix: drop that
   half of the assertion, or keep it and rely on `stage`'s documented contract.

## Check by check

1. **A correct answer passes.** Script. `reference.patch` on `base/T9`: `script_pass=True`, hidden
   9/9, no trap, own suite green (1177 passed). On `base/T9-s3`: `script_pass=True`, hidden 9/9, no
   trap, `s3_acceptance_tests_unchanged` not tripped.
2. **A different correct answer passes.** Script. Blind fix: an Opus subagent given only `S1.md` (as
   a file outside any repository) and a clean worktree of `base/T9`, its own database
   (`audit2_t9_blind`) and staging folder, no way to ask. 200,459 tokens, 12.7 minutes, 35 tool
   calls, 11 files touched (1,878 lines added): a migration with a `file_versions` table, a trigger
   that writes version 1 on every file insert, and a `jobs.version` column; publish hooks in
   `src/gct/ingest/index.py` and `pipeline.py`; 32 new tests in two new files. Real grader:
   `script_pass=True`, hidden 9/9, no trap, own suite 1207 passed, lint clean. Its design differs
   from the reference in shape (trigger instead of an insert in `enqueue`; versions carry their own
   bytes and the claim reads them; an extra refusal `version_unavailable` for versions with no
   bytes), and the key let all of it through: touching `src/gct/ingest/` is not trapped, and the
   only changed existing test is the one `tests_may_change` lists. It also passes the S3 acceptance
   tests (Script, 2 passed).
3. **Every example in the ticket passes the hidden tests.** Read, test by test against S1 Decisions
   and S2 worked examples 1 to 11 and the failure cases. Every key name, value, status code, error
   kind and body shape the tests assert is the one the ticket writes (`replacement` `"pending"` /
   `"failed"` / `null`; `{"versions": [...]}` with exactly `version`, `filename`, `outcome`,
   `failed_reason`, `current`; restore's `{"file_id", "filename", "version"}`; `file_busy`,
   `version_not_found` 404, `version_not_published` 409, `version_is_current` 409, `bad_file_id`
   400, and the 404 equal to `GET`'s). Example 4's `failed_reason` `null` on a ready file with a
   failed replacement, and example 6's `queued` with `replacement` `null`, are asserted as written.
   The only assertion the ticket does not dictate is the staged basename (finding 4).
4. **Careless work fails.** Script for the first, Read for the rest.
   - Replacing a failed file by overwriting its version row: **passes 9/9** (finding 2).
   - A restore that copies the old bytes into a new staged file: fails
     (`assert staged_files() == before` in the restore test).
   - `current` set on the newest version rather than the highest published one: fails
     (`test_every_upload_is_a_numbered_version_with_its_outcome` has a failed version 2 over a
     current version 1).
   - A replacement that runs out of retries left `pending`: fails (`transient_exhausted` test).
5. **Traps are fair.** Script (blind fix and reference). `tests_may_change` names the exact-body test
   the ticket allows to change, and nothing else is needed. The out-of-scope paths
   (`web/src/`, `src/gct/retriever/`, `src/gct/grounder/`) are the ticket's own Out list; the blind
   fix needed `src/gct/ingest/` and was not punished for it.
6. **Reply sheet.** Read. Apart from finding 1, every rule that refuses something has a question
   form (no rescue) and a plan form (`Rescue: yes`), cleanly split by "and has not written code /
   built it that way" versus "says they will, or reports having": old bytes, `queued`/`processing`
   status, web client, backfill. No reply knows more than the owner would. `T9-version-numbers`
   and `T9-filename-rules` repeat the ticket. There is no reply for the names the ticket fixes,
   which matters only at S0 (finding 3).
7. **Timing, load, network.** Read. The transient test patches `worker.time.sleep`; nothing else
   sleeps. Stub embedder and generator; no paid key. `test_files_already_in_the_database_are_version_1`
   creates and drops its own database (needs CREATEDB, which the grader has) and runs
   `scripts/migrate.py` twice in a subprocess with `sys.executable`. Hidden tests ran in about 5
   seconds (Script).
8. **Leaks.** Script. No `file_versions`, `replacement_failed_reason`, `version_not_published` or
   hidden-test name in the base tree or in `git log -S` over all four `-s3` branches, apart from the
   S3 commit itself. `base/T9-s3` is `base/T9` plus one commit adding only
   `tests/acceptance/test_replace_a_file.py`, byte-identical to the answers copy. No `CLAUDE.md`,
   `AGENTS.md`, `.claude/` or `tests/hidden` in the tree. No issue number, person or experiment word
   in S0 to S3 (grep).
9. **Levels.** Read. S1 and S2 are complete. S2 adds worked examples that match the hidden tests.
   S3's acceptance file covers examples 1, 2, 3 and 6 and fails on the base (author's `verify.json`;
   the blind fix passes it, Script). S0: finding 3.
11. **Size.** Script, from the blind fix: 12.7 minutes and 200k tokens for a careful bare agent, well
   inside the smallest per-run ceiling (0.4M). The rules that bite late did bite in its work (rule 3
   is what makes the restore possible; it kept every version's bytes), but it held them all. One
   attempt cannot show drift; the ticket tests breadth and ordered dependency across 11 files more
   than sheer length, as the author's own note says.

## Not checked

- The author's naive patches (not re-run; `verify.json` is green).
- Any reply-judge call: "a blind judge would pick X" is my reading of the `When:` rules.
- Runs at S0, S2 or S3 by a real arm.
