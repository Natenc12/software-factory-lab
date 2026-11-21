# T4 audit: let a student delete a file they uploaded

**Verdict: PASS WITH FIXES** (one must-fix item, in the hidden and acceptance tests)

Audited at tickets commit `0707b5b`, base `base/T4` = `283ebf8`, `base/T4-s3` = `24c7436`. Each claim
is tagged Script (I ran it), Read (I read it) or Not checked.

## Findings, ranked by effect on the experiment

1. **Must fix. The hidden tests fail a careful fix: they stage bytes outside the staging directory
   and require them deleted.** Script. The blind fix (opus subagent, S1 text only) failed 3 of 6:
   `test_deleting_a_ready_file...`, `test_a_queued_file_can_be_deleted...`, `test_the_delete_route`,
   each on `assert not staged.exists()`. Its `unstage` removes only `<staging_dir>/<slot>/<name>`
   under the configured `STAGING_DIR`, because `enqueue` accepts any path and
   `scripts/ingest_smoke.py:587` enqueues real corpus files in place: with the reference fix,
   deleting such a file unlinks the user's original. The hidden helper calls
   `stage(..., staging_dir=tmp_path)`, so every test file sits outside `STAGING_DIR`. With that one
   argument changed to `staging_dir=STAGING_DIR` the blind fix passes 6/6 and so does the reference.
   No reply covers the question ("should bytes outside the staging directory be removed?"); the
   default reply is "go with your recommendation", which leads to the same failure. The S3 acceptance
   test has the same `staging_dir=tmp_path` and `assert not path1.exists()`, so an S3 run is told the
   answer while S1 and S2 runs are not: this also skews the spec-level comparison. Smallest fix: in
   `hidden/test_hidden_t4.py` and `acceptance/.../test_delete_a_file.py` stage under
   `gct.config.STAGING_DIR` (and rebuild `base/T4-s3`). Alternative: keep the tests and add to S1/S2
   Decisions "the file at `files.staging_ref` is removed wherever it is", plus a reply saying so.
2. **`web/src/` is out of scope, but the repository says the generated client is committed with the
   snapshot.** Read. The ticket has the run regenerate `web/openapi.json` only. The failure message of
   `tests/gct/api/test_openapi_snapshot.py` tells the developer to run `cd web && npm run api:refresh`
   "and commit both", and `web/scripts/api-types.test.ts` pins `web/src/api/schema.gen.ts` to the
   snapshot. A run that follows the repository trips `scope_out_paths` (`web/src/`); a run that
   follows the ticket (and the reference) leaves the web drift test stale. CI does not run the web
   tests (`ci.yml` has ruff and pytest only), so nothing goes red on the pull request. Smallest fix:
   add to S1 Scope "do not regenerate `web/src/api/schema.gen.ts`; that is a follow-up", or allow that
   one file.
3. Small, too narrow. Script. Two half-right fixes pass 6/6: one that refuses to delete a `failed`
   file (S1: "queued, ready or failed can be deleted"), and one that deletes the three tables in
   separate autocommit statements after removing the bytes (S1: "all or nothing, and then removes the
   staged bytes"). Smallest fix: add a `failed` file to the first hidden test; atomicity needs a fault
   injected and may not be worth a test.
4. Small. Read. `T4-worker-change`, `T4-migration` and `T4-soft-delete` refuse plans the ticket rules
   out in so many words, with no `Rescue`; see AUDIT.md (rescue flags).

## Checked and fine

- Blind fix: own suite 1202 passed, no trap; about 6.5 minutes, 148k tokens (Script, real grader).
- Wrong fix caught (Script): busy decided from the job state alone (2 failed).
- Reference fix: `script_pass=True`, no trap, on both bases (Script, real grader).
- Ticket facts (Read, at the base): `POST /files` and `GET /files/{file_id}`, `get_file_status`,
  `stage`, `files.staging_ref`, the claim marking the job `processing` before the worker marks the
  file, the `db`, `db_other`, `worker_db` and `api` fixtures, `web/scripts/openapi_snapshot.py` and the
  test that compares the snapshot.
- Levels: S0 names the interface the tests import (`delete_file`, `FileBusy`, `file_busy`); S2 states
  every behaviour the hidden tests check except the location of the staged bytes (finding 1); S3 adds
  only the acceptance paragraph; the branch adds exactly `tests/acceptance/test_delete_a_file.py`.
- No issue number, link or name in S0 to S3 (Script, grep).
- Key: `worker.py`, `retrieve.py` and migrations are named out of scope in S1; the blind fix added a
  function to `src/gct/jobs/queue.py` (not trapped, and S1 only excludes the claim logic).
  `tests_may_change` is empty and neither fix needed to edit an existing test.
- Leaks (Script): no `delete_file`, `FileBusy`, `file_busy` or hidden-test text in the base tree or
  its history; no agent-instruction files.

## Not checked

- The two naive patches (author's `verify.json` only). `npm test` in `web/` was not run; finding 2
  rests on reading the test and on `schema.gen.ts` being untouched by the reference.
