# Gate log

Every owner decision, newest first. The orchestrator starts nothing past a gate without an entry here.

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
