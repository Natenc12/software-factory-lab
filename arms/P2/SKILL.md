# Work a ticket

Take one ticket from approved to a pull request ready to merge (or, for a spike, a report), with the
owner in the loop only at fixed stops. This checklist exists because two tickets run without it
needed the owner to rescue the work four times each: wrong format, "where's the PR?", plan departures
nobody saw, and "not enough to decide a merge".

## Hard rules

1. **Two stops the owner always sees**, and nothing skips them:
   - **Stop 1, the plan:** the ticket text and your plan, before any building.
   - **Stop 2, the merge brief:** before merge (or, for a spike, before the report is final).
2. **Leaving the plan means stopping.** If you are about to do something the approved plan says not
   to do, or something it does not cover that changes files, history or data (editing an applied
   migration, copying a prototype the plan said to rebuild), stop and ask. If it already happened,
   it leads the merge brief as "You approved X; I did Y".
3. **Status words have fixed meanings.**
   - *Done* = merged. Nothing else is done.
   - *Verified* = CI ran it on the pull request and it is green. Your own runs are "I ran", never
     "verified".
   - Every claim on an owner page carries who checked it: **CI**, **Reviewer** (reproduced by the
     review agent), **Builder says** (your run, not re-checked), or **Not checked**. Every merge
     brief has a "Not checked" list, even if it says "nothing".
4. **Never merge.** The owner merges, on their word, after reading the merge brief.

## Talking to the owner

- Every update goes on a page, visual first: a local HTML file in your scratch folder. The `STOP:`
  line is a line or two plus the page path.
- Pages: **Decision card** (one question), **Plan** (Stop 1), **Merge brief** (before merge). Every
  page opens with the same 4-slot strip: **Status | From you | Risk | Updated**. "From you" is the
  yellow slot; it says "Nothing" when nothing is needed.
- One page per moment. Start a new page or replace content; do not pile up history.
- Decisions: one question per card, 2–3 options, each with a concrete before/after example from
  this codebase, a recommendation, and what happens next. Plain English; jargon only if unavoidable.
- Say at intake, on the first page, whether the ticket **ends in a pull request or a report**.

### Page rules
1. Every page opens with the 4-slot strip: Status | From you | Risk | Updated. "From you" is yellow,
   or says "Nothing".
2. One page per moment. Replace content; don't pile history.
3. One decision per card; each option gets a concrete before/after and a "Then" line.
4. Tag every claim by who checked it: CI / Reviewer / Builder says / Not checked.
5. Calls made without the owner each get "Should have asked" or "Low stakes".
6. Merge brief order: strip, then the **Refresher** (the problem, the solution, 2–3 plain sentences
   each, one real before/after, and what the owner chose at the plan), then the four answers, then
   Merge / Change / Hold. The owner signs off the plan, works on other tickets, and must be able to
   understand the ticket again at merge time without re-learning it.
7. Diagrams fit 320px wide, at most ~6 labels, drawn to scale.
8. Same stage names everywhere: Intake, Plan, Build, Prove, Ship.
9. Plain HTML with inline CSS; colours as tokens with dark-mode overrides; works at 400px.

## Steps

### 0. Intake (no owner time)
- Read `TICKET.md`, all of it. Note the commit your branch starts from (`git rev-parse HEAD`); every
  diff below is against it.
- Check every factual claim (paths, counts, line numbers) against the code. Tickets go stale when
  other work merges.
- Note what the "Done when" list depends on that does not exist yet.
- Classify: **build** (ends in a PR) or **spike** (ends in a report). Note the risk from the paths it
  will touch.

### 1. Stop 1: the plan
Page with the strip, the decisions as decision cards, the defaults you will use, and "this ends in a
PR / report". End the turn with a `STOP:` line pointing to the page. Wait for the yes.

### 2. Baseline
Before any edit, run the tests the way CI runs them (`.github/workflows/ci.yml`). Record the result.
A failure here is not yours; note it.

### 3. Build
- You own `src/` and shared fixtures. Add any shared fixture before helpers start.
- Long, noisy work (big test files, wide reads) goes to helper agents, **one file set each, never two
  on one file**, each with its own database (a new SQLite file in your scratch folder, or a new
  database on the same Postgres server, dropped when done).
- Helper brief: what changed (the new API in a few bullets), your files (edit only these), the task,
  how to run (with your database), "if product code looks wrong, report it, don't edit", and a short
  report with before/after line counts.
- Helper reports are claims. Re-run what they claim before you repeat it.
- Commit by path, never `git add -A`. Run `git status` first.

### 4. Prove
- **Open the pull request early.** CI is the proof; your runs only cover what CI cannot run yet.
- Read `.github/workflows/ci.yml` and run its steps **as written** locally before pushing. For any
  migration change, also migrate a database built from the starting commit's migrations, twice.
- Run each "Done when" check. Label each result CI / Builder says / Not checked.

### 5. Agent review (every change; never skipped)
Start the `reviewer` subagent, a **fresh** reviewer with no access to your reasoning: give it the
ticket text, the command that shows the diff (`git diff <starting commit>`), how to run things, and
your scratch folder for its files, nothing else. It writes its own acceptance checks from the ticket
before reading the diff. Rules for it:
- Blocking findings must be **proven by running something**; give the reproduction.
- Also list non-blocking design concerns it cannot prove, clearly separated.
- Check the diff against the ticket's In/Out scope and the approved plan.
- Its own database; no edits.

Fix proven findings, re-run, and keep its report for the merge brief.

### 6. Stop 2: the merge brief
- Push your last commit and read the pull request's checks, waiting until they report.
- The facts: the checks as reported and `git diff --stat <starting commit>` (size by area, tests
  removed). Paste them unedited; your view goes in a separate box labelled "Builder's view". If your
  view of the risk differs from the repository's rules, say so plainly.
- Merge brief page. Top of the page: the strip; the **Refresher** (the problem, then the solution,
  2–3 plain sentences each, one real before/after, and what the owner chose at the plan), because by
  merge time the owner has been thinking about other tickets; then the four answers ("Did the
  reviewer flag anything? What was built? Worth looking at? Dangerous or easy?") and Merge / Change /
  Hold.
- Below: evidence tagged by who checked it, reviewer findings, **calls made without the owner** (each
  tagged "Should have asked" or "Low stakes"), at most 4 files worth reading, and exact undo steps.
- Put a short Markdown version of the brief in the pull request's description.
- End the turn with a `STOP:` line pointing to the brief.

### 7. After Stop 2
Nothing is merged; the pull request stays open. If the owner asks for a change at Stop 2, make it,
re-prove, update the brief, and stop again.

## Spikes

The same steps, except the output is a report page in your scratch folder, with any follow-ups
drafted on it. Stop 2 shows the report. If the owner approves the results, the prototype may become
the follow-up's pull request directly (say so plainly), instead of a separate rebuild.
