# T8 audit: review of "list the files in a class" (review only)

**Verdict: PASS WITH FIXES** (one must-fix item, in the ticket text)

Audited at tickets commit `0707b5b`, branch `base/T8` = `169f391` on review base `283ebf8`. Each claim
is tagged Script (I ran it), Read (I read it) or Not checked.

## Findings, ranked by effect on the experiment

1. **Must fix. The ticket's `scratch/review.md` is not where the grader looks, if read from the
   run's own folder.** Read. The run prompt says "The repository is checked out in your current
   folder" and gives the scratch space as a separate absolute path (`harness/run.py`:
   `scratch=str(root / "scratch")`; layout in `harness/sandbox.py`: `repo/` and `scratch/` are
   siblings). The ticket says "Write your review to `scratch/review.md`" and "write throwaway tests or
   scripts under `scratch/`; leave the rest of the tree as you found it", which reads as a folder
   inside the repository. The grader and the judge read only `<run folder>/scratch/review.md`
   (`grader/grade.py`, `grader/judge.py`). A run that writes `repo/scratch/review.md` has no report as
   far as the grade goes, for a reason unrelated to its arm. Smallest fix: change both sentences to
   "your scratch space (the folder the run instructions name, outside the repository), as
   `review.md`"; optionally let the grader fall back to `repo/scratch/review.md`.
2. **The branch has real defects the key does not list, and one of them collides with a not-bug.**
   - Script. `GET /classes/{id}/files?page=9223372036854775807` answers `500 internal`, with the
     planted bugs fixed as well (`page` has no upper bound; the offset overflows bigint). The key's
     not-bug 5 says "`page` must be at least 1; FastAPI answers 422 outside those bounds. Intended."
     A judge holding only the key is likely to score a blocking finding about this as a false alarm.
   - Read. The change regenerates `web/openapi.json` but not `web/src/api/schema.gen.ts` (0 mentions
     of the new route), which `web/scripts/api-types.test.ts` pins to the snapshot; the repository's
     own message says to commit both. Not run (no `npm test`).
   - Read. There is no test of the route and none of the status filter, which is why bugs 1 to 3
     survive a green suite. A reviewer may file this as blocking.

   The judge brief has `real_extra_findings`, but the judge cannot see the code, so it has to guess
   whether each is real. Smallest fix: add a `real_unplanted` list to `key.json` with these three
   (each "real; blocking or not is the reviewer's call; never a false alarm"), and reword not-bug 5 to
   "the lower bound of `page` and both bounds of `per_page`".
3. Small. Read. On a class with at most `per_page` files, bug 1 alone makes page 1 empty and bug 2
   then turns that into `404 class_not_found`. A reviewer who runs the route sees one symptom with two
   causes; a report that names only the offset has caught bug 1 and missed bug 2. The judge brief
   handles this ("names its cause"); no change needed, but expect bug 2 to be the one most often missed.

## Checked and fine

- Each planted bug is real (Script, hidden tests on `base/T8`: `3 failed`): page 1 skips the newest
  files; an empty class answers 404; `status=` raises `UndefinedObject: type "file_status" does not
  exist`. With `reference.patch` all three pass. The key's line numbers are exact
  (`classes.py:217`, `classes.py:226`, `files.py:148`).
- Each is findable the way the key says (Read): bug 1 from the diff against the description ("Page 1
  is the newest `per_page` files"); bug 2 from the empty-class case in the description; bug 3 only by
  running a status filter or by checking the schema (`files.status` is `text` with a CHECK; no such
  type in `migrations/`). The feature's own suite is green on the branch (Script: 1179 passed).
- Every `not_bugs` entry is true (Script, probe over the route with the planted bugs fixed, unless
  noted): another owner's class 404; malformed id 400; `status=bogus`, `page=0`, `per_page=101` are
  422; `created_at` carries an offset; a `urn:uuid:` class id works. Read: only the fixed fragment is
  interpolated into the SQL; `files_class_idx` exists (`migrations/0001_init.sql`); nothing in `src/`
  deletes a class; the private message maps are imported as described.
- The ticket says what to produce and overrides the shared prompt's last line in so many words ("Do
  not change the code, push, or open a pull request: the review is the whole deliverable"). The
  branch name `base/T8` and the base commit both exist in a run's clone (Read, `harness/sandbox.py`).
- Replies parse (Script); none has `Rescue`, which is right for a review.
- Leaks (Script): no hidden-test text or key wording in the tree or history; the branch is the review
  base plus one commit, message "Add a list of the files in a class"; no agent-instruction files.

## Not checked

- The review judge itself (no judge calls). `npm test` in `web/`.
