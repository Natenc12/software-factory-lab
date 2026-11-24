# What changes from `work-ticket`

The owner's skill (`~/.claude/skills/work-ticket/SKILL.md` and `NOTES.md`, as of 2026-11-22) against
the winning checklist (this plugin, which is arm P5P). "Tested" cites the stage and the count; the
results are in `results/<stage>/` and `results/final/`. A practice the experiment never ran is marked
**not tested here**, with a recommendation. Every practice in the owner's `SKILL.md` and `NOTES.md`
has a line in one of the four tables below; corrected against the independent fact check
(`results/final/FACT-CHECK-guide-and-checklist.md`).

Two arms matter as references, both from the stage 1 confirm round (24 runs each):

- **P2** was `work-ticket` adapted to the lab (plan stop, merge brief, claim tags, mandatory review):
  14 trustworthy runs of 24 (4.7 of 8) on the current reading, **18 of 24 (6.0 of 8) on the second
  reading**; 49 owner stops in 24 runs; 153k tokens and 2,738 owner words per ticket.
- **P1** was the one-page guide alone: 21 of 24 (7.0 of 8), **20 of 24 (6.7 of 8) on the second
  reading**; 78k tokens and 1,468 words per ticket.

So the trust gap is seven runs on one reading and two on the other; the cost and reading gaps hold on
both. P5P is P1 plus the six skills: 22 of 24 on gct-lab (stages 2 and 2b, corrected) and 27 of 32 on
Hono and sqlglot (stage 4; Hono 15 of 16, sqlglot 12 of 16), 0.19 stops per ticket in stage 4. P2
tested `work-ticket`'s practices together, so its result cannot be split between them.

Skill use in P5P runs, stages 2 and 2b (24 runs) and stage 4 (32 runs): `check-the-ask` 23 and 32;
`prove-each-claim` 23 and 31; `test-that-bites` 5 and 9; `fresh-eyes-review` 2 and 3; `stay-in-scope`
0 and 0; `find-the-cause` 0 and 0 (`results/final/profiles.md`).

## The way of working

| `work-ticket` does | The checklist does | Tested? | Recommendation |
| --- | --- | --- | --- |
| Intake: read the issue and any parent issue | Read the ticket and the code it touches; run the existing tests first | Yes, every run of every arm | Use the checklist. Reading the issue with `gh` stays as plumbing |
| Check every factual claim in the ticket (paths, counts, line numbers) | `check-the-ask` (pointed): list what the ticket asks, search the decision records, docs, tests and limits that touch it, stop and ask if one breaks | Yes. Wrong-ask ticket T6 raised before building: 0 of 15 runs of P0, P1, P1R, P3, P2 (confirm round); P5P 3 of 3 (stages 2 and 2b). T11 and T12: 24 of 24 runs, 12 each, all arms (stage 2). Hono T8 6 of 6, sqlglot T8 P5P 2 of 2 (stage 4). Used in 55 of 56 P5P runs | Use the checklist. The case for it on recorded decisions rests mostly on one ticket (T6) |
| Direction check against `NOTES.md` | Nothing | **Not tested here** | Keep the direction note, but in the project's own notes (its CLAUDE.md), not in the checklist, so it stays current with the product |
| **Stop 1, the plan**: always, before building | No fixed stop; ask when unsure, or when `check-the-ask` finds a conflict | Only inside P2. Its 49 stops: 24 at the plan, 22 at the merge brief, 3 later. At the plan, 15 of 24 drew a ticket-specific answer, 4 were plain approvals, 3 were the T6 rescue, 2 were out-of-scope replies. Of the 33 stops the grader counts as routine (reply not ticket-specific, or a rescue), 24 came after the plan, mostly at the merge brief. P2 scored lowest on the current reading only (P0 is lowest on the second); P3, which also stops at a contract problem and at the brief, had 20 of 24 against P1's 21 | Drop the fixed plan stop as a rule, but not because plan stops were empty: most drew a real answer. P5P got to those questions without it (it asked when it needed to, and raised T6 in 3 of 3). The routine stops were mostly the end-of-work stop, which the owner keeps as the merge decision (below) |
| Leaving the plan means stopping | `stay-in-scope` (at the run's discretion): smallest change; anything beyond goes under "Not done" | Not as a separate rule. `stay-in-scope` was called in 0 of 56 P5P runs; only its one-line description was in front of the run | Keep it as shipped, since it is part of what ran, but expect nothing from it; the guide's "make the change the ticket asks for, and nothing beyond it" is what was in force |
| Status words and claim tags (CI, Reviewer, Builder says, Not checked) on every claim | `prove-each-claim` (pointed): every claim backed by a command run in the session; "not checked" beats a wrong "checked" | The tags only inside P2 and P3. `prove-each-claim` used in 54 of 56 P5P runs. Stage 4, corrected: six runs with a false claim across the three rows; five of them outside T7 and T8, and four of those five were counts of tests or files | Use `prove-each-claim`. The tags are **not tested here** on their own; keep them only if the owner wants them in pull request descriptions |
| Helper agents, one file set each, own scratch data | Nothing; the run decides | Delegation, as P6P (told to delegate): 6.5 of 8 corrected (6.0 as frozen) against P5P's 6.75, at $1.94 against $0.95 per run (stage 4). Three P5P runs started a helper unprompted (stage 4) | Drop the rule; leave helpers to the session |
| "Helper reports are claims; re-run what they claim" | Nothing beyond `prove-each-claim` ("the command you ran in this session") | Only inside P2. Stage 4's flaw 2 is this failure: a lead's "re-run by me after the worker's commit" judged false | **Keep** the line; it costs nothing and the one failure seen was exactly this |
| Agent review on every pull request, fresh reviewer, brief template | `fresh-eyes-review` at the run's discretion | A mandatory fresh reviewer (P1R): 6.7 of 8 against P1's 7.0 on the current reading, 6.7 each on the second (confirm round, 24 runs each). P5P called `fresh-eyes-review` in 5 of 56 runs. But in the owner's real sessions reviewers found blocking problems in 5 of 15 pull requests, on changes much bigger than the lab's tickets (`research/owner-sessions-audit.md`) | **Keep a fresh review for large or high-risk pull requests** (not tested here at that size); on ticket-sized work, the checklist's discretion is what was tested. The owner decides where the line is |
| The reviewer's rules: findings proven by running, a realistic threat model, safety lines (no printing secrets, generated files only, a scratch library), started by someone other than the builder | `fresh-eyes-review`: one subagent with the ticket, the diff command and the test command; find defects, missed cases, scope creep, unsupported claims | **Not tested here** (P1R's reviewer had the proof rule; the safety lines and the threat model never ran) | **Keep** the owner's reviewer brief for the reviews kept in the row above |
| "Now and then, run the reviewer on another model" | Nothing | **Not tested here** | Drop |
| Baseline tests before any edit | Same (guide step 1) | Every run | Same |
| Tests that prove the change | Guide step 4 (a new test fails without the change); `test-that-bites` | Tests first as a rule (P1T): stayed out by the stage's rule (0 of 3), 6.0 of 8 against P1's 6.0 (stage 2). `test-that-bites` called in 14 of 56 P5P runs | Use the checklist |
| Nothing | `find-the-cause` for bugs and failed fixes | Called in 0 of 56 P5P runs, and by no run of any arm in any stage | Keep it as shipped, since it is part of what ran, but nothing shows it helped |
| **Stop 2, the merge brief** (artifact page, now an explainer video) with refresher, evidence, reviewer findings, calls made without the owner, undo steps | The pull request description: what was wrong, what changed, how it was tested (commands), what was not checked | The brief only inside P2 and P3; P2's brief stop was where most of its routine stops fell. Owner reading per ticket: P5P 1,421 words (stage 4, Hono and sqlglot) against P2 2,738 (confirm round, gct-lab), so on different codebases | Keep the owner's word before merge (below). Let the description be the written record, as the owner already decided on 2026-11-21 (`NOTES.md`). The video is **not tested here**; keep it if the owner still wants it |

## Intake, proof and questions: practices with no counterpart in the checklist

| `work-ticket` piece | Tested? | Recommendation |
| --- | --- | --- |
| Say at intake whether the ticket ends in a pull request or a report | Only inside P2 | Keep; one line, and it matters for spikes |
| List what the "Done when" list depends on that does not exist yet, and run each "Done when" check with its result labelled | Only inside P2 | Keep the "Done when" checks; `prove-each-claim` asks for the same proof without the labels. The dependency list is the owner's call |
| Ask at intake what the work is worth, what it costs, and how any reference code was made | **Not tested here.** The owner-sessions audit ranks it first: it would have caught direction errors that only the owner caught | Keep, ahead of planning; it is the one audit suggestion the lab never tested |
| For a ticket that names a GitHub or CI mechanism, check the platform's current rules | **Not tested here** | Keep in the owner's notes |
| How to put a question to the owner: one question, two or three options with a before and after from this codebase, a recommendation, plain English | Only inside P2 and P3 (the lab's stand-in owner read the pages as text) | Keep as the owner's preferred format |
| For a schema change, open data made by the old code with the new code | **Not tested here** (stage 2's migration ticket was graded by hidden tests, not by this check) | Keep for schema changes |
| Commit by path, never everything at once; check the status first | **Not tested here** | Keep; cheap |

## Project plumbing the experiment replaced with its own

Every run had a harness-made sandbox, a ticket file, a scratch folder and three `lab` commands, and
nothing was ever merged. So none of these was tested here; each is marked **not tested here**.

| `work-ticket` piece | Recommendation |
| --- | --- |
| Sandbox: `ticket-up.sh` (worktree per ticket) and `ticket-down.sh` | **Keep.** The checklist assumes it works in "this checkout and your scratch folder"; the sandbox script is what provides them outside the lab. Say in the session where the scratch folder is |
| Hook that blocks writes to the owner's main checkout | **Keep.** Cheap safety, and every run here had a stronger wall |
| Merge only on the owner's word, per pull request, with the hook that asks on every `gh pr merge` | **Keep unchanged**, outside the checklist. This is the one fixed stop the owner keeps |
| Step 8: `gh pr merge --squash`, confirm the issue closed, remove `in-progress` | **Keep** as plumbing after the owner's word, with the "closes #N" check from `NOTES.md` (2026-11-22) |
| The `risk-gate` check and risk labels on every pull request; naming the risk at intake | **Keep**; CI plumbing that informs the merge decision |
| Mark the pull request ready, wait for a clean state before merging, keep the required-check conventions (`merge-check`) | **Keep** |
| `gh pr update-branch` and `pr-facts.py` before the merge decision | **Keep**; they feed the owner's merge decision, not the build |
| Draft pull request early; run CI's steps as written before pushing | **Keep** running CI's steps locally (the guide asks only for the whole test suite); draft-early is the owner's call |
| `in-progress` label on claim | Owner's call; harmless |
| Outward actions (comments, issues, closes, labels) shown first, run from one script | **Keep.** A safety rule for actions the lab never allowed |
| Commit trailers (`Ticket: #n`, `Agent-Session`) | **Keep**; cheap traceability |
| Artifact pages, templates, the board | Owner's call. Not part of the way of working that won |
| Spikes (report instead of a pull request) | **Keep** the spike paragraph in the owner's notes until a spike is tested; every ticket here ended in a pull request or a review report |
| Retro entry in `NOTES.md` after each ticket | Owner's call; it is how `work-ticket` learned, not how a ticket is worked |

## Packaging (not tested here)

- **When the guide loads.** In the runs it was in the system prompt from the first turn. In the plugin it
  is the body of the `work-ticket` skill and loads when that skill is triggered. The six skills load
  the same way in both.
- **The run prompt is not in the plugin.** Each run also got `harness/prompts/run.md`: the ticket is a
  file, here is your scratch folder, use `lab` for GitHub, end a turn with `STOP:` to ask. In the owner's
  sessions the issue is the ticket, the sandbox script gives the folder, `gh` is GitHub, and asking is
  an ordinary question at the end of a turn. The skill texts say "your scratch folder" and "stop and
  ask"; both read naturally there.
- **The entry skill's description is new**: the old skill's trigger phrases, so "do #N" still starts it.
