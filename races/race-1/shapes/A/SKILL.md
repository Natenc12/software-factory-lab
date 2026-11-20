---
name: work-ticket
description: Take one GitHub issue in Natenc12/pipeline-lab from approved to a pull request ready to merge, with the owner in the loop only at fixed stops. Covers the sandbox, the build, proof, the agent review and the owner pages.
---

# Work a ticket (shape A)

## Benchmark rules (read first; these override anything below)

- The run id (`A-T1` … `B-T6`) and the issue number are given in the first message. Use them everywhere
  `<run-id>` and `<n>` appear.
- **Never merge. Never add or remove the `owner-ok` label.**
- GitHub writes only in `Natenc12/pipeline-lab`. Pass `--repo Natenc12/pipeline-lab` to every `gh` command.
- Do not read anything under `~/repos/pipeline-bench` except `shapes/<your shape>/`, `runs/<run-id>/`,
  and running `shapes/lab-up.sh` and `shapes/lab-down.sh`.
- Owner pages are local HTML files in `~/repos/pipeline-bench/runs/<run-id>/`, not published artifacts.
  At an owner stop, end your turn with one line and wait for the reply:
  `STOP <1|2>: <one-line ask> — page: <path>`. Any other question for the owner uses the same line
  with `STOP ask:` and its own page (`ask-<k>.html`).
- The run ends when Stop 2 is answered (or when you are told it ends). Then run the teardown script
  (step 9) and leave the PR open.

---

The third step of the pipeline: `file-issue` captures, `triage` approves (label `ready`), **this skill
delivers**. It exists because two tickets run without it needed the owner to rescue the work four
times each: wrong format, "where's the PR?", plan departures nobody saw, and "not enough to decide a
merge".

## Hard rules

1. **Never touch the owner's checkout** (`~/repos/pipeline-lab`). No file edits and no git writes
   there (reading, `git -C ~/repos/pipeline-lab show origin/main:<path>` and the scripts' `fetch` are
   fine). Every ticket gets a sandbox (step 2).
2. **Two stops the owner always sees**, and nothing skips them:
   - **Stop 1, the plan:** the ticket text and your plan, before any building.
   - **Stop 2, the merge brief:** before merge (or, for a spike, before anything is posted).
3. **Leaving the plan means stopping.** If you are about to do something the approved plan says not
   to do, or something it does not cover that changes files, history or data (editing an applied
   migration, copying a prototype the plan said to rebuild), stop and ask. If it already happened,
   it leads the merge brief as "You approved X; I did Y".
4. **Status words have fixed meanings.**
   - *Done* = merged, or posted on GitHub. Nothing else is done.
   - *Verified* = GitHub's CI ran it and it is green. Your own runs are "I ran", never "verified".
   - Every claim on an owner page carries who checked it: **CI**, **Reviewer** (reproduced by the
     review agent), **Builder says** (your run, not re-checked), or **Not checked**. Every merge
     brief has a "Not checked" list, even if it says "nothing".
5. **Merge only on the owner's word**, in this conversation, per PR. High-risk PRs (database,
   migrations, the queue, answer logic, CI config) also need the `owner-ok` label: the required
   `risk-gate` check blocks the merge without it. **Agents never add or remove `owner-ok`.**
6. **Outward actions need the exact text shown first.** Comments, new issues, closes, label changes:
   draft them in `runs/<run-id>/`, show them, get one yes, then run them from one script.

## Talking to the owner

- Every update goes on a local HTML page in `runs/<run-id>/`, visual first. Chat is a line or two
  plus the page path.
- Pages: **Decision card** (one question), **Plan** (`plan.html`, Stop 1), **Merge brief**
  (`brief.html`, Stop 2). Every page opens with the same 4-slot strip: **Status | From you | Risk |
  Updated**. "From you" is the yellow slot; it says "Nothing" when nothing is needed. Plain HTML
  with inline CSS; it must read well at 400px wide.
- One page per moment. Start a new page or replace content; do not pile up history.
- Decisions: one question per card, 2–3 options, each with a concrete before/after example from
  this codebase, a recommendation, and what happens next ("Then …"). Plain English; jargon only if
  unavoidable.
- Say at intake, on the first page, whether the ticket **ends in a pull request or a report**.
- Same stage names everywhere: Intake, Plan, Build, Prove, Ship.

## Steps

### 0. Intake (no owner time)
- `gh issue view <n> --repo Natenc12/pipeline-lab --json title,body,comments`, plus any parent or
  tracking issue. (Not `--comments`: when its output is captured it prints only the comments, never
  the ticket body.)
- Check every factual claim (paths, counts, line numbers) against `origin/main`. Tickets go stale
  when other PRs merge.
- Note what the "Done when" list depends on that does not exist yet.
- Classify: **build** (ends in a PR) or **spike** (ends in a report). Note the risk from the paths it
  will touch (`.github/risk/rules.txt`).

### 1. Stop 1: the plan
`plan.html` with the strip, the decisions as decision cards, the defaults you will use, and "this
ends in a PR / report". End the turn with `STOP 1: <ask> — page: <path>`. Wait for the yes.

### 2. Sandbox
```bash
~/repos/pipeline-bench/shapes/lab-up.sh <run-id> <short-slug>
```
This makes `~/repos/lab-worktrees/<run-id>` on branch `<run-id-lowercase>/<slug>` from `origin/main`,
its own SQLite database `<sandbox>/lab.db` (migrated twice, like CI) and its own `.env`
(`LAB_DB=<sandbox>/lab.db`). Work and run everything there; run commands with
`uv run --env-file .env …` or `export LAB_DB=<sandbox>/lab.db`. Keep the ticket's pages in
`runs/<run-id>/`. Claim the ticket: `gh issue edit <n> --repo Natenc12/pipeline-lab --add-label in-progress`.

### 3. Baseline
In the sandbox, before any edit: `uv run pytest -q`. Record the result. A failure here is not yours;
note it.

### 4. Build
- You own `src/` and shared fixtures. Add any shared fixture before helpers start.
- Long, noisy work (big test files, wide reads) goes to helper agents, **one file set each, never two
  on one file**, each with its own database: `LAB_DB=<sandbox>/lab_h<k>.db`, migrated.
- Helper brief: what changed (the new API in a few bullets), your files (edit only these), the task,
  how to run (with your database), "if product code looks wrong, report it, don't edit", and a short
  report with before/after line counts.
- Helper reports are claims. Re-run what they claim before you repeat it.
- Commit by path in the sandbox, never `git add -A`. Run `git status` first. Stamp every commit:
  `git commit -m "<message>" --trailer "Ticket: #<n>" --trailer "Agent-Session: $CLAUDE_CODE_HOST_SESSION_ID"`

### 5. Prove
- **Open a draft PR early** (push the branch, `gh pr create --draft --repo Natenc12/pipeline-lab`).
  CI is the proof; your runs only cover what CI cannot run yet.
- Read `.github/workflows/ci.yml` and run its steps **as written** locally before pushing. For any
  migration change, also migrate a database built from `main`'s migrations, twice.
- Run each "Done when" check. Label each result CI / Builder says / Not checked.

### 6. Agent review (database, queue, migrations, answer logic, CI changes)
Start a **fresh** reviewer agent with no access to your reasoning, using `reviewer-brief.md` (next to
this file) as its whole prompt: it gets the ticket, the diff and how to run things, nothing else. It
writes its own acceptance checks from the ticket before reading the diff. Rules for it:
- Blocking findings must be **proven by running something**; give the reproduction.
- Also list non-blocking design concerns it cannot prove, clearly separated.
- Check the diff against the ticket's In/Out scope and the approved plan.
- Its own database; no edits, no GitHub writes.

Fix proven findings, re-run, and keep its report for the merge brief.

### 7. Stop 2: the merge brief
- First bring the branch up to date with `main` (`gh pr update-branch <pr> --repo Natenc12/pipeline-lab`)
  and let CI go green, so "merge it" could happen at once.
- The facts: `gh pr checks <pr> --repo Natenc12/pipeline-lab`, pasted unedited (it includes the
  `risk-gate` result). Your view goes in a separate box labelled "Builder's view". If your view of
  the risk differs from the rules', say so plainly.
- `brief.html`. Top of the page: the strip; the **Refresher** (the problem, then the solution, 2–3
  plain sentences each, one real before/after, and what the owner chose at the plan), because by
  merge time the owner has been thinking about other tickets; then the four answers ("Did the
  reviewer flag anything? What was built? Worth looking at? Dangerous or easy?") and Merge / Change /
  Hold.
- Below: evidence tagged by who checked it, reviewer findings, **calls made without the owner** (each
  tagged "Should have asked" or "Low stakes"), the "Not checked" list, at most 4 files worth reading,
  and exact undo steps.
- Mark the PR ready for review and put the brief's path in the PR body.
- End the turn with `STOP 2: <ask> — page: <path>`.

### 8. Merge and close
Not in this run. Nothing is merged; the PR stays open. If the owner asks for a change at Stop 2,
make it, re-prove, update `brief.html`, and stop again.

### 9. Clean up
```bash
~/repos/pipeline-bench/shapes/lab-down.sh <run-id>
```
It refuses if anything is uncommitted or unpushed; fix that (commit, push) and run it again.

## Spikes

The same steps, except the output is a report page, a comment on the issue and drafted follow-ups.
Stop 2 shows those drafts before posting. If the owner approves the results, the prototype may
become the follow-up's PR directly (say so plainly), instead of a separate rebuild. Follow-ups you
file yourself are settled on the results page, with their text shown, rather than re-triaged.
