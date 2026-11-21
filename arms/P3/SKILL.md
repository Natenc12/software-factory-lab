# Work a ticket (contract first)

This checklist takes one ticket to a pull request ready to merge, with the owner in the loop only at
fixed stops. It exists because two tickets run without it needed the owner to rescue the work four
times each: wrong format, "where's the PR?", plan departures nobody saw, and "not enough to decide a
merge".

**The contract.** At intake you write the contract from the ticket: **Examples of done**, **Must not
change**, **Decisions** and **Scope** (In and Out). It is the source of truth for every step after
intake: you build to it, CI proves it, the reviewer checks it, and the merge brief ticks it. Once
written, only the owner changes it.

## Hard rules

1. **One stop the owner always sees, one only when needed:**
   - **Stop 1, contract amendment:** only if intake finds the ticket wrong, incomplete, or
     contradicting itself or the code. Otherwise there is no Stop 1.
   - **Stop 2, the merge brief:** once the pull request is open and its checks have reported (or, for
     a spike, when the report is ready). Always.
2. **The contract is fixed; some things always stop.** Stop and ask before anything that touches a
   **Must not change** line, anything outside **Scope In** (or inside **Scope Out**), or anything
   that changes stored data, history or an applied migration. If it already happened, it leads the
   merge brief as "The contract said X; I did Y". Every other judgment call is yours: record it in
   the brief under "calls made without you".
3. **Status words have fixed meanings.**
   - *Done* = merged. Nothing else is done, and nothing in this work is merged.
   - *Verified* = CI ran it on the pull request and it is green. Your own runs are "I ran", never
     "verified".
   - Every claim on an owner page carries who checked it: **CI**, **Reviewer** (reproduced by the
     review agent), **Builder says** (your run, not re-checked), or **Not checked**. Every merge
     brief has a "Not checked" list, even if it says "nothing".
4. **Never merge.** The owner merges after reading the merge brief.
5. **Never edit `TICKET.md`.** A contract change is proposed on a page and decided by the owner.

## Talking to the owner

- Every update goes on a local HTML page in your scratch folder, visual first. The `STOP:` line is a
  line or two plus the page path.
- Pages: **Decision card** (one question), **Contract amendment** (`plan.html`, Stop 1, only when
  needed), **Merge brief** (`brief.html`, Stop 2). Every page opens with the same 4-slot strip:
  **Status | From you | Risk | Updated**. "From you" is the yellow slot; it says "Nothing" when
  nothing is needed. Plain HTML with inline CSS; it must read well at 400px wide.
- One page per moment. Start a new page or replace content; do not pile up history.
- Decisions: one question per card, 2–3 options, each with a concrete before/after example from
  this codebase, a recommendation, and what happens next ("Then …"). Plain English; jargon only if
  unavoidable.
- **Every stop carries a recommendation the owner can simply accept.** Word the `STOP:` line so that
  "yes" is a complete answer, for example "STOP: I recommend A (keep the old format for existing rows).
  Go ahead with A?", and say on the page exactly what "yes" will make you do.
- Say at intake, on the first page, whether the ticket **ends in a pull request or a report**.
- Same stage names everywhere: Intake, Plan, Build, Prove, Ship.

## Steps

### 0. Intake (no owner time)
- Read `TICKET.md`, all of it. Note the commit your branch starts from (`git rev-parse HEAD`); every
  diff below is against it.
- **Check every factual claim in the ticket against the code**: paths, names, counts, line numbers,
  and every behaviour it says exists today. Record each claim in `contract.md` under "Ticket facts
  checked", with ✓ or ✗ and what you found.
- **Write the contract** in `contract.md` in your scratch folder, from the ticket:
  - **Examples of done**: concrete cases, each an input and the result it must give, covering every
    "done when" line in the ticket and its failure cases.
  - **Must not change**: behaviour, interfaces, stored data and tests that must stay as they are.
  - **Decisions**: the ticket's decisions, plus any it leaves open that the work needs, each marked
    "from the ticket" or "mine".
  - **Scope**: In and Out.
  Keep the ticket's own words where it has them. Mark every line the ticket does not state outright
  as "inferred".
- Check the contract against the code: every Example of done (can it be played out, and is its
  expected result right?); every Must not change line (is it true today?); and whether the lines
  contradict each other or the code. Would building exactly this cause harm the ticket does not
  mention?
- Classify: **build** (ends in a PR) or **spike** (ends in a report). Note the risk from the paths it
  will touch (and the repository's risk rules, if it has any).

### 1. Stop 1: only if the ticket is wrong, incomplete or contradictory
- **Ticket is sound:** no stop. Write a short `plan.html` (strip, "Ticket checked against the code:
  no amendment needed. Ends in a PR / report.", the contract's inferred lines and "mine" decisions,
  the defaults you will use) and go straight to step 2.
- **Ticket is wrong, incomplete or contradictory** (a fact that is false, an open decision the work
  cannot proceed without guessing, lines that contradict each other or the code): `plan.html` as a
  contract amendment page: for each problem, what is wrong, a concrete example from this codebase, and
  the contract line you recommend (as a decision card when there is a real choice). End the turn with
  a `STOP:` line that asks the owner to accept your recommended contract. The amended contract is
  what the owner says, recorded in `contract.md`.

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
- **Turn every Example of done into a test** (or, where a test is impossible, a reproducible check
  with its exact command) so CI runs it. Name each test after its example. Where a Must not change
  line can be checked mechanically, check it too.
- Read `.github/workflows/ci.yml` and run its steps **as written** locally before pushing. For any
  migration change, also migrate a database built from the starting commit's migrations, twice.
- Label each contract line's result CI / Builder says / Not checked.

### 5. Fresh review (every change; never skipped)
Start the `reviewer` subagent. It has no access to your reasoning. Give it only: the ticket text, the
contract from `contract.md` verbatim, the command that shows the diff (`git diff <starting commit>`),
how to run the tests, and your scratch folder for its files. Not your plan, notes or explanation of
the change. It writes its own checks from the contract before reading the diff. Rules for it:
- Blocking findings must be **proven by running something**; give the reproduction.
- Also list non-blocking design concerns it cannot prove, clearly separated.
- Check the diff against every contract line: Examples, Must not change, Decisions, Scope In/Out.
- Its own database; no edits.

Fix proven findings, re-run, and keep its report for the merge brief.

### 6. Stop 2: the merge brief
- Push your last commit and read the pull request's checks, waiting until they report.
- `brief.html`. Top of the page: the strip; then **the contract, ticked**: every line of Examples of
  done, Must not change, Decisions and Scope Out, each with ✓ or ✗ and who checked it (CI / Reviewer
  / Builder says / Not checked), plus the test or command that shows it. The owner checks the ticks
  without re-learning the ticket. Then Merge / Change / Hold, with your recommendation.
- Then **calls made without you** (each tagged "Should have asked" or "Low stakes"); then the
  checks, as reported, pasted unedited. Your view goes in a separate box labelled "Builder's view".
  If your view of the risk differs from the repository's rules, say so plainly.
- Below: reviewer findings, the "Not checked" list, at most 4 files worth reading, and exact undo
  steps.
- Put a short Markdown version of the brief in the pull request's description.
- End the turn with a `STOP:` line that recommends Merge, Change or Hold and points to the page.

### 7. After Stop 2
Nothing is merged; the pull request stays open. If the owner asks for a change at Stop 2, make it,
re-prove, update `brief.html`, and stop again.

## Spikes

The same steps, except the output is a report page in your scratch folder, with any follow-ups
drafted on it. Stop 2 shows the report. If the owner approves the results, the prototype may become
the follow-up's pull request directly (say so plainly), instead of a separate rebuild.
