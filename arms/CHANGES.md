# Departures from the sources

Every place an arm differs from the text it was built from, and why. Sources: the approved table in
`results/setup/arms-v1.html` ("The arms I will freeze"), race 1's shape B (`races/race-1/shapes/B/`),
the owner's `work-ticket` skill and its `templates/` (read only), and race 1's shape A for comparison.
No change was made on research evidence about model behaviour (owner's decision, 2026-11-21).

The harness loads only top-level `.md` files other than `README.md` from an arm folder, plus
`agents/*.md`. This note, `SIZES.md` and `P0/README.md` are never loaded into a run.

## Lab mechanics, every arm with a source (P1R, P3, P2)

| Source said | Arm says | Why |
| --- | --- | --- |
| Skill front matter (`name`, `description` with trigger phrases) | removed | It is skill metadata, not instructions; the text is appended to the system prompt |
| `gh issue view <n>` | read `TICKET.md` | The ticket is a file; there are no issues |
| `gh pr create --draft`, then "mark the PR ready" | open the pull request early, not as a draft | `lab pr open --draft` exists, but nothing can mark a draft ready |
| `gh pr update-branch` before the brief | push the last commit, then read the checks, waiting until they report | No fetch in the sandbox; the base is frozen. Reading the checks before the merge brief is the ending P3, P2 and P4 share |
| `gh pr checks`, or `pr-facts.py` (P2) | the checks as reported; P2 adds `git diff --stat` for size by area | Only `lab pr checks` reaches GitHub; `pr-facts.py` lives in the owner's skill and calls `gh` |
| `gh issue edit --add-label in-progress`, `owner-ok`, risk-gate label rules | removed | No labels are touched; `lab` cannot |
| "Merge only on the owner's word" / step 8 merge and close | "Never merge"; after Stop 2 the PR stays open, a requested change is made and the run stops again | Nothing is ever merged |
| Outward actions rule (comments, issues, closes) | removed | None of them is possible; the PR is the only outward action |
| Artifact pages / local pages under `~/repos/...` | local HTML pages in the scratch folder, named on the `STOP:` line | Pages are files in the run's `scratch/` |
| `STOP 1: …`, `STOP 2: …` | "end the turn with a `STOP:` line" | One stop syntax for every arm; the harness already explains it to every run |
| `origin/main` | the commit the branch started from, noted at intake with `git rev-parse HEAD` | The run's clone has no remote |
| Sandbox step (`lab-up.sh`, `ticket-up.sh`), clean-up step (`lab-down.sh`, `ticket-down.sh`), "never touch the owner's checkout" | removed; steps renumbered | The harness builds and removes the sandbox and keeps the run inside it; the run prompt says so |
| `uv run pytest -q` (B) / `uv run pytest -m "not live" -q` (skill) | run the tests the way CI runs them (`.github/workflows/ci.yml`) | One text must work on both practice repos |
| Helper and reviewer databases: `LAB_DB=…/lab_h<k>.db` (B), `createdb gct_…` (skill) | a new SQLite file in the scratch folder, or a new database on the same Postgres server, dropped when done | Same reason: SQLite on one repo, Postgres on the other |
| Commit trailers `Ticket: #<n>`, `Agent-Session: $CLAUDE_CODE_HOST_SESSION_ID` | removed; "commit by path, `git status` first" kept | No issue number; that variable is not passed into runs |
| "Put the brief's path/link in the PR body" | put a short Markdown version of the brief in the pull request's description | A local path means nothing on GitHub and contains the run id |
| Reviewer brief as a file the builder pastes into a fresh agent, angle brackets filled in | an `agents/reviewer.md` subagent: the brief is its prompt; the facts it needs (ticket, contract, diff command, test command, scratch folder) come in the message that starts it | Lets every reviewer be pinned to `claude-opus-5-5` and defined the same way in every arm. Its tools are Read, Glob, Grep and Bash: the sources already said "no edits" and "run things" |
| Reviewer: "do not read anything under `~/repos/pipeline-bench`", "GitHub: Natenc12/…" | removed | Paths outside the run folder; no GitHub |

## P0 Bare

No instruction files, as defined. `README.md` is for people only.

## P1 Loose

No source text beyond the table row. One page, 145 words: read first and run the tests, work only in
the checkout and scratch folder, change only what the ticket asks, add tests that fail without the
change, open a PR with a short summary, ask when unsure. It does not read checks or stop at the end;
that difference from P3, P2 and P4 is intended, and P1R shares it.

## P1R Loose + reviewer

- `GUIDE.md` is P1 word for word, then the reviewer rule from the table and from
  `research/arms/p1r-loose-plus-reviewer.md`.
- Nothing else is added: no check reading, no merge brief and no closing `STOP:`. The approved table
  gives P1R the same owner stops as P1 ("when it chooses"), so P1 against P1R isolates the reviewer.
- The rule tells the builder how to get the diff (`git diff <the commit your branch started from>`),
  because the sandbox has no `origin/main`.
- Reviewer brief: race 1 shape B's brief, adapted as the research proposal says: the contract checks
  become checks against the ticket text; it must run the code on at least one input the ticket names;
  findings are blocking (reproduced) or notes. "Required before a pull request merges" became "before
  its pull request opens", matching when P1R runs it.

## P3 Contract (from race 1 shape B)

The four changes the task set:

1. **No contract comes with the ticket.** "The contract the owner signed at triage" became "at intake
   you write the contract from the ticket": Examples of done (input and result, covering every "done
   when" line and its failure cases), Must not change, Decisions (marked "from the ticket" or "mine"),
   Scope In/Out; the ticket's own words kept; every unstated line marked "inferred". "Copy the
   contract sections verbatim" was removed.
2. **Every factual claim in the ticket is checked against the code** and recorded with ✓/✗ under
   "Ticket facts checked" in `contract.md`.
3. **Every stop carries a recommendation the owner can simply accept**, worded so "yes" is a complete
   answer, with what "yes" will make the run do (new bullet under "Talking to the owner"; Stop 1 and
   Stop 2 lines say the same).
4. **The fresh review cannot be skipped.** Step heading "(database, queue, migrations, answer logic,
   CI changes)" became "(every change; never skipped)".

Stop 1 is now triggered by the ticket being wrong, incomplete or contradictory (it was "the contract"),
and the sound-ticket `plan.html` lists the contract's inferred lines and "mine" decisions so the owner
can see them at the brief.

One more change, forced by (1): **the reviewer gets the ticket text as well as the contract.** In
race 1 the contract was owner-signed truth, so the reviewer saw only it. Now the builder writes the
contract, so a reviewer that saw only the contract could not catch a contract that drifted from the
ticket. The brief adds one check: a contract line that contradicts the ticket, or a requirement it
drops, is a finding.

Smaller: "Never edit the issue body" became "Never edit `TICKET.md`"; "*Done* = merged, or posted on
GitHub" became "*Done* = merged… nothing in this work is merged"; Stop 2 happens once the PR is open
and its checks have reported; Spikes end in a report page in the scratch folder, and the line about
filing follow-ups yourself was removed (no issues).

## P2 Checklist (from the owner's `work-ticket` skill)

Kept as close to the skill as the lab allows. The one required change: **step 6, the agent review,
cannot be skipped** (heading "(database, queue, migrations, answer logic, CI changes)" became "(every
change; never skipped)"). Other departures:

- **Removed the direction check and every pointer to `NOTES.md`.** They describe the owner's real
  product's direction (a desktop app, SQLite, no queue), which is false for one practice repo and
  outside the run's folder for both.
- **Removed "Now and then, run it on a different Claude model".** Every reviewer uses
  `claude-opus-5-5`.
- **Removed the pipeline sentence** ("`file-issue` captures, `triage` approves (label `ready`), this
  skill delivers") and "(for a ticket you triaged yourself, the rewritten issue body)": no skills,
  labels or triage exist in a run. The rescue history sentence is kept.
- **Templates:** `templates.html` (37 KB of artifact styling and example pages) is not shipped. A run
  could only reach it by a path naming its own instruction folder, and appending it would multiply
  P2's size. Its README's nine rules are carried over word for word under "Page rules", except rule 9
  (the artifact page contract: `<title>` first, no doctype, Google Fonts) which became "plain HTML
  with inline CSS; colours as tokens with dark-mode overrides; works at 400px", and the published
  example links, which were dropped. The "(owner, Nov 20)" attribution was dropped.
- **Removed "The board"** (board script and artifact) and **"Not yet built"** (owner's roadmap).
- **Removed step 9's retro** (a dated entry in `NOTES.md`): the file is outside the run.
- **Stop 1** now ends the turn with a `STOP:` line pointing to the plan page (the skill said "wait for
  the yes"). Stop 2 for a spike is "before the report is final" (was "before anything is posted").
- **Reviewer brief:** "Free stand-in models only (`GCT_PROVIDERS=standin`)" became "no paid or
  networked model calls: if the project has a stand-in or offline setting for them, use it", so the
  same text fits both repos.
- Rule 1 ("never touch the owner's checkout") and rule 6 (outward actions) were removed (see the
  table above); rules renumbered.

Compared with race 1's shape A: P2 keeps A's lab choices where they still apply (local HTML pages, a
`STOP:` at the plan, "after Stop 2 the PR stays open"), but starts again from today's skill, so A's
pipeline-lab paths, benchmark block and teardown script are not carried over.

## P4 Team (from the table and the charter; no source text)

Built from the table row: a lead runs planner, architect, builder, tester and reviewer as subagents,
all on `claude-opus-5-5`; at most two build-and-review rounds; stop only if the contract is wrong,
then the merge brief. The architect stays (the owner kept the five roles). Choices made where the
definition was silent:

- **How limits are enforced.** Each role's tool list is set in its definition, and each role has its
  own PreToolUse hook (`hooks/<role>.json`, running `hooks/role_guard.py` from the control folder):
  - planner: Read, Glob, Grep, Write; writes only `scratch/team/contract.md`.
  - architect: Read, Glob, Grep, Write; writes only `scratch/team/design.md`.
  - builder: Read, Glob, Grep, Edit, Write, Bash; may not change the tester's file, the contract, the
    design note or the review folder.
  - tester: Read, Glob, Grep, Write, Edit (no Bash, no Agent). Inside the checkout it reads only an
    allow-list: its own file, `conftest.py` files under `tests/`, `pyproject.toml`, top-level `.md`
    files, and anything under `design/` or `docs/`. Everything else there is refused, because code
    does not live only in `src/` (gct-lab also has `web/`, `scripts/`, `migrations/` and `eval/`).
    In `scratch/` it reads only the contract and the design note. It writes only its own file.
    Searches (Grep) follow the same rule: a folder is searchable only if everything in it is readable
    (so `design/` and `docs/`, never the checkout's top level or `tests/`). File-name listing (Glob)
    is allowed: names, not contents.
  - reviewer: Read, Glob, Grep, Bash; changes nothing outside `scratch/team/review/` (Bash git writes,
    redirects and file commands checked, best effort); may not read `scratch/` beyond the contract,
    the test results and its own folder, so it never sees the design note or anyone's notes.
- **The tester does not run tests; the lead does.** Test output prints source lines in tracebacks, so
  running them would show the tester the code. The lead runs the tester's file on the starting code
  (new-behaviour tests should fail there) and after each build.
- **The tester sees the design note**, whose Interface section names the commands or functions to
  call and how to set up fixtures, described as behaviour. Without it the tester could not know what
  to import. The design note is written before any code exists.
- **The tester's file is fixed:** `tests/test_ticket_acceptance.py`, so the hooks and the grader can
  find it.
- **The lead's own limits are instructions only** ("you do not write product code or tests"). The
  lead is the main session, whose tools the harness sets for every arm alike. A breach shows in the
  transcript as a main-thread edit under `src/`.
- The merge brief has no source format; it uses the same building blocks as P3's (plain summary,
  recommendation, contract ticked with who checked it, findings, rounds, checks, calls made without
  the owner, not checked, undo).

## Harness change

`harness/sandbox.py`: an agent file may name a hooks file (`hooks: hooks/<role>.json`, inside the arm
folder). `{python}`, `{arm}` and `{run}` in it are filled in, and for any arm with agents the arm is
also copied to the run's control folder, which the session can neither read nor write, so the hooks
run from a copy no role can edit. Tests: `tests/test_arms.py`; real trials: `harness/TRIALS.md`
trials 6–8.
