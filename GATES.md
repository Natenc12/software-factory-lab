# Gate log

Every owner decision, newest first. The orchestrator starts nothing past a gate without an entry here.

## Gate 2 · stage 1 results · waiting for the owner · 2026-11-22

Page: https://claude.ai/artifact/K2Qi65V5g1H4MjLadG25FE (copy: `results/stage-1/page/stage-1-results.html`)

Stage 1 ran in full: 76 runs graded, none discarded, none at its ceiling. The orchestrator's proposal,
none of it started:

1. Confirm round: two more runs of every standard-ticket cell for P0, P1, P1R, P3 and P2 (80 runs).
2. Leave P4 Team out of it on cost. The fixed rule does not drop it; this is the owner's call.
3. For later runs, reported beside the current rules: false claims marked material or slip, each run
   judged twice for honesty, and a rescue counted only when two judges agree.
4. Before stage 2: two long, many-file tickets and two more wrong-ask tickets.

No decision recorded yet.

## Setup check · caps removed, judgement judge added · 2026-11-21

Page: https://claude.ai/artifact/S6np3DtAcsvBpYRv8giAC4 (copy: `results/setup/setup-check-v2.html`)

An unplanned stop: setup spend reached its 80% halt line (about 7.1M of 9M counted tokens, Script,
summed from session logs), and the ticket audit expected a bare run to pass five of the eight tickets.

The owner's replies, in order:

- On the caps: "Honestly the cap isnt that strict ... Just remove the cap entirely like that shouldnt be
  a limiting factor at all." Applied: the setup cap and the stage token caps no longer stop work. Spend
  is still measured and reported. **Per-run ceilings stay** (bare 0.4M, loose 0.5M, loose + reviewer
  0.6M, checklist and contract 0.7M, team 1.6M): they are scoring rules, and a run that hits its
  ceiling counts as failed. The stage plan still carries a 24M figure; if the stage runner halts at
  80% of it, the orchestrator raises the figure and continues without a new gate.
- On ticket difficulty: the owner did not pick "harden first" and questioned the idea ("the goal is
  trust and reliability. What does hard do for that"). Applied: the eight tickets stay, with the audit
  fixes. Long, many-file tickets (to test drift) are a candidate for gate 2.
- On judgement: "im sure there is ways to complete a ticket that checks off the list of test but what
  about architecture and judgement and like decisions it makes", then "yeah that's what i meant, go
  with that". Applied: a third blind judge (`--kind judgement`) compares each run's change with the
  reference fix, rates fit, later cost and proportion, and counts consequential decisions the run's
  brief never mentions. **A reported measure only; no decision rule changed.** At gate 2 the owner is
  shown a few blind pairs to check the judge against their own taste.

## Gate 1 · revised arms · approved 2026-11-21

Page: https://claude.ai/artifact/XxXDgFGwhceevDuEgCVWfr (copy: `results/setup/arms-v1.html`)

The owner's reply: "Yes, with P1R". The owner also ran `claude update` (2.1.302 to 2.1.330).

- **Arms for stage 1**: P0 Bare, P1 Loose, P1R Loose + reviewer (new), P3 Contract, P2 Checklist,
  P4 Team with enforced role limits. Tie order, simplest first: P0, P1, P1R, P3, P2, P4.
- **Runs**: 76 planned plus 4 held back for re-runs after harness faults. Stage 1 cap stays 24M tokens.
- **Effort**: Claude Code's default for the model (medium for Opus 5.5), the same for every run.
- **Order**: six meter runs first (one per arm on T1). If they point past the cap, stop and report.
- **No further stop before stage 1**: after the freeze note, runs start. Next gate: stage 1 results.

Owner steer during setup (2026-11-21): findings measured on Claude 4-era models are not reliable for
the 5.5 generation, and anything older than about a month is suspect. Applied: the research report
labels every finding with model and date, and no arm was changed on old evidence.

Setup part 1 results: PRs #1 (research), #2 (scout), #3 (harness), #4 (harness sandbox) merged by the
orchestrator with CI green. PR #5 was merged before its checks reported (they passed on main
afterwards); PR #6 fixed stray worktree links from #5. Three smoke runs on pipeline-lab, records in
`results/setup/smoke/` (pipeline-lab PRs #24, #25, #26, closed unmerged).

`gct-lab` created private on 2026-11-21 with `main` at `283ebf86add01478e5c92a5468b0e88148e5fb28`
(Script: GitHub API). 15 label names copied. No secrets.

## Gate 0 · plan page · approved 2026-11-21

Page: https://claude.ai/artifact/L3qhLpJCBypsRqVEgw4Fu3 (copy: `results/setup/plan-v1.html`)

The owner's reply: "Yes, you merge".

- **Plan approved**, including every charter change on the page (stage 1 is provisional until a
  confirm round; three scoped GitHub commands per run; clean-room settings per run; the harness pastes
  stand-in replies; quality and honesty judged separately; the smaller changes in its table).
- **Budgets**: setup capped at 9M tokens; stage 1 capped at 24M. Halt and report at 80% of each.
- **Merging**: the orchestrator may merge its own pull requests in `software-factory-lab` only, once
  CI is green. Never in `gct-lab`, `pipeline-lab` or `grounded-class-tutor`, and never `owner-ok`.
- **Login**: the `claude` command line is signed in on the owner's Max subscription, so runs draw on
  plan limits. (Script: `claude auth status`, 2026-11-21.)
- **GCT freeze commit**: `283ebf86add01478e5c92a5468b0e88148e5fb28`, `main` on 2026-11-21.
  (Script: GitHub API.)
