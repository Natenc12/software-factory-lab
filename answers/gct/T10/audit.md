# T10 audit: call a class a "course" in the API, step by step, without breaking any existing client (long)

**Verdict: PASS WITH FIXES** (one must-fix item: a hidden-test gap on two late-biting rules)

Audited at tickets commit `2cdf7fd`, base `base/T10` = `283ebf8`, `base/T10-s3` = `e1fa196`. Each
claim is tagged Script (I ran it), Read (I read it) or Not checked. Grades are the real grader on
`grade_audit2_*` databases, dropped afterwards.

## Findings, ranked by effect on the experiment

1. **Must fix. Two of the rules stated at the top can be broken late and still pass 9/9.** Script.
   On top of `reference.patch` I made two careless changes: (a) `POST /ask` sets the deprecation
   flag after parsing the id instead of before, so `POST /ask {"class_id": "biology", ...}` answers
   today's `400 bad_class_id` **without** `Deprecation: true`; (b) `POST /courses/{course_id}/ask`
   turns every id refusal into `404 course_not_found`, so `/courses/biology/ask` no longer answers
   `400 bad_course_id`. Hidden tests: 9 passed. Rule 6 says the header goes on every old-name reply
   "success or error, whatever the error", and S2's failure cases say "`class_id=biology` and every
   other old-name error"; the header test's list has `POST /files` with `class_id=biology` but no
   malformed `POST /ask`. The S1 paragraph after part 6 says every `/courses` route answers a
   malformed id with `400 bad_course_id`; the hidden test checks that for `GET /courses/...` and
   `POST /courses/.../files` but not for `.../ask`. These are exactly the "rule stated once, bites
   in the last part" cases the ticket exists for. Fix, in `hidden/test_hidden_t10.py`: add
   `client.post("/ask", json={"class_id": "biology", "question": "what is it?"})` to the `replies`
   list in `test_every_reply_to_an_old_name_request_carries_the_deprecation_header` (expected status
   400), and in `test_course_scoped_upload_and_ask_follow_every_earlier_rule` add
   `assert client.post("/courses/biology/ask", json={"question": "q?"}).json()["error"]["kind"] == "bad_course_id"`.
   Both hold on the reference and on the blind fix (Script: the hidden file with both checks
   added passes 10/10 on each; the careless variant answers the first without the header and the
   second with 404, so it would fail).
2. **The reference does not keep the old `POST /ask` 422 exactly.** Script (probe against the base
   and the reference). On the base, `POST /ask {"question": "q?"}` answers 422 with one detail entry
   `{"loc": ["body", "class_id"], "msg": "Field required", "type": "missing"}`. With the reference it
   is a model-level entry `{"loc": ["body"], "msg": "Value error, send course_id (or the older
   class_id)"}`; `{"class_id": null}` changes the same way. Rule 1 lists "the `422` for a missing
   id, which still names `class_id`" among the refusals that must stay word for word. The reference
   is arguably inside the letter (the message names `class_id`) and the hidden test only checks the
   kind, so no run is graded wrongly; but the judgement judge is shown this reference as the
   comparison, and the blind fix, which preserved the old 422 byte for byte with a copy of the old
   model, is the more faithful of the two. Fix: either make the reference keep the old entry, or
   say in rule 1 that the 422's detail may change as long as it names `class_id`.
3. **S2 contradicts S1 on what may be added below the API.** Read. S1 rule 4: "Below the API, add
   only what part 5 needs, in class words." S2 "Must not change": "The database, the migrations, and
   everything below `src/gct/api/`." An S2 run that reads the second line literally does the
   counting in the router; one that asks gets `T10-rename-below-question` ("Only the API surface
   changes"), which reads as a no. The key does not trap `gct.classes` or `gct.files` (correct, per
   rule 4), so nothing is graded wrongly; the S2 text is just inconsistent. Fix: S2 line to "renaming
   anything below `src/gct/api/` (adding what part 5 needs, in class words, is allowed)".
4. Small. `POST /courses/{course_id}/files` with a stray form field. Script. The reference accepts
   `class_id=<some other uuid>` in the form and uploads into the path's course (202). The ticket
   says "multipart field `file` only" for the upload and "any other key is a `422`" only for ask.
   The blind fix refuses extra fields with 422. Neither is tested, so nothing is graded wrongly.
   Fix (optional): say which in S1 part 6.

## Check by check

1. **A correct answer passes.** Script. `reference.patch` on `base/T10`: `script_pass=True`, hidden
   9/9, no trap, own suite green. On `base/T10-s3`: `script_pass=True`, hidden 9/9, no trap,
   acceptance file unchanged.
2. **A different correct answer passes.** Script. Blind fix (Opus subagent, `S1.md` only, clean
   worktree of `base/T10`, own database `audit2_t10_blind`, no way to ask): 213,553 tokens, 15.4
   minutes, 55 tool calls, 14 files touched (1,775 lines added). Different shape from the reference:
   a separate `deprecation.py` with the flag on `request.state` read by every error handler (it
   edits `src/gct/api/errors.py`, which the reference does not), a custom route class to rebuild the
   old 422 for `POST /files`, `class_summary` in `src/gct/classes.py`, tests added to the existing
   `tests/gct/test_classes.py`, and a section in `design/components/api.md`. Real grader:
   `script_pass=True`, hidden 9/9, no trap, own suite 1252 passed, lint clean. It also passes the S3
   acceptance tests (Script, 5 passed).
3. **Every example in the ticket passes the hidden tests.** Read, against S1 and S2 examples 1 to 17
   and the failure cases. The exact old bodies in the hidden test (`OLD_BAD_CLASS`,
   `OLD_UPLOAD_NOT_FOUND`, `OLD_ASK_NOT_FOUND`) are the texts of S2 examples 5 and 9 and the failure
   case; the header is checked as the value `true`, as written; `GET /courses/C` is compared to
   the exact body of example 13 with a canonical `course_id`; example 7's `urn:uuid:` spelling is
   used as written; example 17 is a 422. Nothing asserted goes beyond the text.
4. **Careless work fails.** Script for the first, Read for the rest.
   - Header missing on a malformed `POST /ask`, and `/courses/biology/ask` answering 404: **passes
     9/9** (finding 1).
   - `POST /files` with both ids where `course_id` silently wins: fails (conflict test).
   - Old `class_id` requests answered in course words: fails (exact old bodies), and the
     repository's own router tests also pin them.
   - `GET /courses/{id}` without the zero counts: fails (exact body).
5. **Traps are fair.** Script. The blind fix touched `errors.py`, `classes.py`, `design/` and an
   existing test file (new functions only) and tripped nothing. `tests_may_change` is empty and the
   ticket says every existing test passes unchanged; neither fix needed to change one. The trap
   paths (`migrations/`, `src/gct/jobs/`, `ingest/`, `retriever/`, `grounder/`, `web/src/`) are all
   out of scope in S1.
6. **Reply sheet.** Read. Renames below the API, old replies and the web client each have a
   question reply and a plan reply with `Rescue: yes`, split by "has not done it" versus "says they
   will, or reports having". `T10-header-scope`, `T10-summary-shape` and `T10-scoped-routes` repeat
   the ticket. `T10-summary-shape` says "the ticket's shape", which an S0 run does not have, but it
   then lists the keys, so it is usable. No reply knows more than the owner would.
7. **Timing, load, network.** Read. No sleeps, no clocks, stub providers. Hidden tests ran in about
   1 second (Script).
8. **Leaks.** Script. No `conflicting_ids`, `course_not_found` or `Deprecation` in the base tree or
   history apart from the S3 commit; `base/T10-s3` is the base plus one commit adding only
   `tests/acceptance/test_courses_in_the_api.py`, identical to the answers copy. Ticket text clean.
9. **Levels.** Read. S0 gives the new error kinds, the header, both new routes and the
   `conflicting_ids` rule; it lacks the exact `GET /courses` body keys, which `T10-summary-shape`
   gives if asked, so S0 is passable with a question. S2 adds examples consistent with the hidden
   tests, apart from finding 3. S3's acceptance tests fail on the base (`verify.json`: 4 failed, 1
   passed) and pass for both fixes.
11. **Size.** Script, from the blind fix: 15.4 minutes and 214k tokens, inside the smallest ceiling.
   The six parts are ordered and the header rule really does reach into every route, which is what
   drove the blind fix's size (it had to rebuild the old 422s). One attempt shows no drift. The
   ticket tests breadth across about a dozen files and a cross-cutting rule, more than length.

Key nits (Read): `long_ticket.checked_by["4"]` names a trap `below-the-api-renamed`; the trap is
`below-the-api-touched`. `naive_patches["naive-s3.patch"]` says "(breaks rule 5)"; deprecation in the
schema is part 4.

## Not checked

- The author's naive patches (not re-run).
- Reply-judge behaviour.
