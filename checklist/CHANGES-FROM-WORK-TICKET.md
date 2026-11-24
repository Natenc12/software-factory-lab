# What changes from `work-ticket`

The owner's skill (`~/.claude/skills/work-ticket/SKILL.md` and `NOTES.md`, as of 2026-11-22) against
the winning checklist (this plugin, which is arm P5P). "Tested" cites the stage and the count; the
results are in `results/<stage>/RESULTS.md`. A practice the experiment never ran is marked **not
tested here**, with a recommendation; nothing is dropped or kept without a line in this table.

Two arms matter as references. **P2** was `work-ticket` adapted to the lab (plan stop, merge brief,
claim tags, mandatory review): 4.7 trustworthy pull requests of 8, 2.0 owner stops per ticket, 153k
tokens per run (stage 1 confirm round, 24 runs). **P1** was the one-page guide alone: 7.0 of 8, 0.1
stops, 78k tokens (same round, 24 runs). P5P is P1 plus the six skills: 7.3 of 8 on gct-lab (stages 2
and 2b, 24 runs) and 6.75 of 8 on Hono and sqlglot (stage 4, 32 runs), 0.19 stops per ticket in stage 4.
P2 tested `work-ticket`'s practices together, so its result cannot be split between them.

## The way of working

| `work-ticket` does | The checklist does | Tested? | Recommendation |
| --- | --- | --- | --- |
| Intake: read the issue and any parent issue | Read the ticket and the code it touches; run the existing tests first | Yes, every run of every arm | Use the checklist. Reading the issue with `gh` stays as plumbing |
| Check every factual claim in the ticket (paths, counts, line numbers) | `check-the-ask` (pointed): list what the ticket asks, search the decision records, docs, tests and limits that touch it, stop and ask if one breaks | Yes. Wrong-ask ticket T6 raised before building: 0 of 15 runs of P0, P1, P1R, P3, P2 (confirm round); P5P 3 of 3 (stages 2 and 2b). T11, T12: 24 of 24 runs, all arms (stage 2). Hono T8 6 of 6, sqlglot T8 P5P 2 of 2 (stage 4). `check-the-ask` used in 23 of 24 P5P runs (stages 2 and 2b) and in every replay and feature run in stage 4 | Use the checklist |
| Direction check against `NOTES.md` | Nothing | **Not tested here** | Keep the direction note, but in the project's own notes (its CLAUDE.md), not in the checklist, so it stays current with the product |
| **Stop 1, the plan**: always, before building | No fixed stop; ask when unsure, or when `check-the-ask` finds a conflict | Only inside P2 (above): fixed stops came with the lowest score and the most stops | Drop the fixed plan stop |
| Leaving the plan means stopping | `stay-in-scope` (at the run's discretion): smallest change; anything beyond goes under "Not done" | Not as a separate rule. How often P5P called `stay-in-scope` is not in the results files | Use the checklist |
| Status words and claim tags (CI, Reviewer, Builder says, Not checked) on every claim | `prove-each-claim` (pointed): every claim backed by a command run in the session; "not checked" beats a wrong "checked" | The tags only inside P2 and P3. `prove-each-claim` used in 23 of 24 P5P runs (stages 2 and 2b) and in all but one replay and feature run in stage 4. False claims left in stage 4, all three rows together: five, mostly counts of tests or files | Use `prove-each-claim`. The tags are **not tested here** on their own; keep them only if the owner wants them in pull request descriptions |
| Helper agents, one file set each, own scratch data | Nothing; the run decides | Delegation, as P6P (told to delegate): 6.5 of 8 against P5P's 6.75, at $1.94 against $0.95 per run (stage 4). Three P5P runs started a helper unprompted (stage 4) | Drop the rule; leave helpers to the session |
| Agent review on every pull request, fresh reviewer, brief template | `fresh-eyes-review` at the run's discretion | A mandatory fresh reviewer (P1R): 6.7 of 8 against P1's 7.0 (confirm round, 24 runs each). With review at its discretion, P5 used it in 3 of 16 runs (stage 2); P5P's count is not in the results files | Use the checklist; drop the mandatory review |
| "Now and then, run the reviewer on another model" | Nothing | **Not tested here** | Drop |
| Baseline tests before any edit | Same (guide step 1) | Every run | Same |
| Tests that prove the change | Guide step 4 (a new test fails without the change); `test-that-bites` | Tests first as a rule (P1T): stayed out by the stage's rule (0 of 3), 6.0 of 8 against P1's 6.0 (stage 2) | Use the checklist |
| Nothing | `find-the-cause` for bugs and failed fixes | Shipped in every P5P run; use not counted in the results files | Keep, as tested |
| **Stop 2, the merge brief** (artifact page, now an explainer video) with refresher, evidence, reviewer findings, calls made without the owner, undo steps | The pull request description: what was wrong, what changed, how it was tested (commands), what was not checked | The brief only inside P2 and P3. Owner reading per ticket: P5P 1,421 words (stage 4, Hono and sqlglot) against P2 2,738 (confirm round, gct-lab), so on different codebases | Keep the owner's word before merge (below). Let the description be the written record, as the owner already decided on 2026-11-21 (`NOTES.md`). The video is **not tested here**; keep it if the owner still wants it |

## Project plumbing the experiment replaced with its own

Every run had a harness-made sandbox, a ticket file, a scratch folder and three `lab` commands, and
nothing was ever merged. So none of these was tested here; each is marked **not tested here**.

| `work-ticket` piece | Recommendation |
| --- | --- |
| Sandbox: `ticket-up.sh` (worktree per ticket) and `ticket-down.sh` | **Keep.** The checklist assumes it works in "this checkout and your scratch folder"; the sandbox script is what provides them outside the lab. Say in the session where the scratch folder is |
| Hook that blocks writes to the owner's main checkout | **Keep.** Cheap safety, and every run here had a stronger wall |
| Merge only on the owner's word, per pull request, with the hook that asks on every `gh pr merge` | **Keep unchanged**, outside the checklist |
| Step 8: `gh pr merge --squash`, confirm the issue closed, remove `in-progress` | **Keep** as plumbing after the owner's word, with the "closes #N" check from `NOTES.md` (2026-11-22) |
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
