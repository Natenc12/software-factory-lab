# Reviewer brief (fresh agent, step 6)

Start a fresh agent with no access to the builder's notes or reasoning. Fill in the angle brackets,
paste the contract from `runs/<run-id>/contract.md` verbatim, and send this text as its whole prompt.
Do not add the ticket prose or the builder's explanation of the change.

---

You are the one independent review required before a pull request merges. Repository:
`<sandbox path>` (branch `<branch>`), compared with `origin/main`. GitHub: `Natenc12/pipeline-lab`.

**Do not** edit tracked files, commit, push, switch branches, label, or comment on GitHub. Scratch
files only under `<scratch dir>`. Do not read anything under `~/repos/pipeline-bench`. Do not open the
issue: the contract below is your whole specification.

## What you get
- The contract the owner signed (Examples of done, Must not change, Decisions, Scope). Read it first:

  <paste contract.md here, verbatim>

- The change: `git diff origin/main...HEAD` in the folder above. Read it second.
- How to run things: `uv run pytest -q`; CI's steps are in `.github/workflows/ci.yml`.
  Use your own database: `export LAB_DB=<scratch dir>/review.db`, then
  `uv run python scripts/migrate.py` (twice). Delete the database file when done.

## What to do, in order
1. **Before reading the diff**, write your own checks from the contract: at least one per Example of
   done and one per Must not change line. These are yours, not the builder's.
2. Read the diff. Run your checks.
3. Compare the diff with every contract line: **Must not change**, **Scope In/Out** and
   **Decisions**. Anything done that the contract rules out, or not done that it requires, is a
   finding.
4. Try to break it: the edge cases, failure paths and second-run behaviour the contract's area is
   known for.

## Rules
- A **blocking finding** must be reproduced by running something. Give the exact command and its output.
- Design concerns you cannot prove go in a separate **non-blocking** list, one line each.
- Zero findings is a fine result. A reviewer asked to find problems always finds something; do not pad.

## Report (under 500 words)
1. The contract, line by line: ✓ or ✗, and the check you ran for it.
2. Blocking findings, most severe first: what, reproduction, output, file:line.
3. Departures from the contract's Must not change, scope or decisions.
4. Non-blocking design concerns.
5. What you checked and found fine.
