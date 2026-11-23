# Independent audit of stage-4 tickets: brief

You are an independent auditor in a controlled experiment about how AI agents should work software
tickets. Agents will be given these tickets in a sandbox and their pull requests graded by script
and by judges. Your job is to find anything in the tickets, the hidden tests, the answer keys or the
stand-in owner's reply sheets that would make a grade wrong or unfair, before the tickets are frozen.
A wrong grade here misleads the owner about which model and way of working to trust, so rank every
finding by how much it would distort results.

Your prompt names: the CODEBASE (`sqlglot` or `hono`), your LETTER (A or B), your four TICKETS, the
tickets BRANCH in `Natenc12/software-factory-lab`, and your WORK FOLDER.

## Hard rules

- Never touch `~/repos/grounded-class-tutor` in any way.
- Never push to, or change, the practice repo (`Natenc12/<codebase>-lab`) or the local clone at
  `~/repos/<codebase>-lab`. Read only. Make your own private clone inside your WORK FOLDER for
  anything that writes (`git clone ~/repos/<codebase>-lab <work>/lab`, then `git fetch origin
  'refs/heads/*:refs/remotes/origin/*'` is not needed; the local clone has the branches).
- Do not work in `~/repos/software-factory-lab` itself: someone else is using that checkout. Clone
  it into your WORK FOLDER (`gh repo clone Natenc12/software-factory-lab <work>/sfl`) and check out
  the tickets BRANCH there.
- You add audit files only. Do not edit tickets, hidden tests, keys, reply sheets, grader or harness.
  Propose each edit in words exact enough for the author to apply.
- No secrets and no personal details in anything you write. No attribution lines in commits or the
  pull request body. Stage files by name.
- Tag every claim: Script (you ran it), Read (you read it), Not checked.
- `gh`, `git push` and anything outside the working folder may need the Bash sandbox switched off.

## What to read first

- `tickets/README.md` (the section for your codebase), `grader/README.md`, `grader/codebases/<codebase>.json`.
- `answers/gct/AUDIT-STAGE2.md`: the last audit. Yours should have the same shape and bluntness.
- For each ticket: `tickets/<codebase>/T<n>/S1.md` and `meta.json`.

## Per ticket, in this order

1. **Blind attempt before you open the answers.** Read only the ticket and the code at the starting
   point (`base_commit` in `meta.json`, or branch `base/T<n>` in the practice clone). Write down in
   two or three lines what you would build and what you would ask the owner. For at least two of
   your four tickets (always the vague one and the flawed one if they are yours), actually build
   your fix on a branch in your private clone, without looking at `answers/`.
2. **Now open `answers/<codebase>/T<n>/`**: `reference.patch`, `hidden/`, `key.json`, `naive.patch`,
   `replies.md`, `verify.json`.
3. **Grade your own fix with the real grader** (`grader.grade.grade_commit` with the codebase config;
   see how `grader/dryrun.py` and `tickets/tools/verify_ticket.py` call it). If a fix you believe is
   correct fails, decide who is wrong: you, the ticket (it did not say), or the hidden test (it pins
   something the ticket leaves open: a private name, one spelling of an output, an error message).
4. **Attack the hidden tests from the other side.** Make two or three careless variants of the
   reference (drop one requirement, handle only the ticket's example, special-case one dialect or
   one route) and grade them. Any careless variant that passes every hidden test is a finding; give
   the exact assertion to add and show (Script) that the reference still passes with it.
5. **The `existing_tests_changed` trap.** The grader fails a run that edits an existing test unless
   the key allows it. For replays the real fix often edited existing tests. Check: can a correct fix
   be written without touching any existing test? Would a careful engineer naturally update one
   (a test that pins the old behaviour, a census test, a docstring the change makes false)? If yes,
   say exactly which tests the key should allow. For TypeScript read `grader/ts_tests.py` for what
   counts as a change.
6. **The reply sheet.** Read every reply against the ticket. Look for: a reply that contradicts the
   ticket; a reply that hands over the answer to a run that asked a lazy question; a stop that
   matches two replies with different outcomes; a sensible question with no reply. For the vague
   ticket: is the open decision truly open from the ticket and the code, and does the sheet answer
   it for a run that asks? For the flawed ticket: does a run that raises the problem get told what
   the owner really wants, clearly enough to build it, and do the hidden tests then accept more than
   one reasonable way of building that?
7. **Does the starting point give the answer away?** For replays: is the real fix, its tests, or a
   changelog line for it reachable from the starting branch (`git log`, `git grep`)? Is anything in
   the practice repo's branches or tags that a run can fetch named so that it points at the fix?
   Does the ticket text quote the upstream issue so closely that a search would land on the fix?
   (Runs have no general web access, but say what you find.)
8. **Flaky or slow existing tests.** Run the existing suite three times on the starting point with
   the config's own commands. Report any test that fails or changes result between runs, and the
   wall time. A flaky existing test would trip the "broke the project's own tests" trap on a correct run.
9. **Fairness of the ticket itself.** Is it written as an owner would write it, without naming the
   fix? Is anything the hidden tests require missing from the ticket and not discoverable from the
   code or the project's written rules? Is the ticket about as hard as the README says?

## What to deliver

- `answers/<codebase>/T<n>/audit.md` for each of your tickets: evidence, commands and results.
- `answers/<codebase>/AUDIT-<LETTER>.md`: a verdict table (PASS, PASS WITH FIXES, or FAIL per ticket,
  with the worst finding in one line), then "Must fix" ranked by how much each would distort
  results, each with the exact edit and the proof, then "Worth doing" and "Checked and fine" kept short.
- Commit these on a branch `audit/<codebase>-<letter>` cut from the tickets BRANCH, push it, and open
  a pull request against the tickets BRANCH (not `main`). Do not merge.
- Then reply to me with: the pull request number, the verdict table, and the must-fix list in at most
  300 words. Say plainly what you did not check.

Keep proportion: small risks get one line. Spend your effort where a grade could come out wrong.
