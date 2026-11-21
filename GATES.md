# Gate log

Every owner decision, newest first. The orchestrator starts nothing past a gate without an entry here.

## Gate 1 · revised arms · waiting for the owner (page published 2026-11-21)

Page: https://claude.ai/artifact/XxXDgFGwhceevDuEgCVWfr (copy: `results/setup/arms-v1.html`)

Asked: approve six arms (P0, P1, P1R new, P3, P2, P4), default effort for every run, and starting
stage 1 after the freeze note with no further stop; and run `claude update` (CLI 2.1.302 to 2.1.321+).

Owner steer during setup (2026-11-21): findings measured on Claude 4-era models are not reliable for
the 5.5 generation, and anything older than about a month is suspect. Applied: the research report
labels every finding with model and date, and no arm was changed on old evidence.

Setup part 1 results: PRs #1 (research), #2 (scout), #3 (harness), #4 (harness sandbox) merged by the
orchestrator with CI green. Three smoke runs on pipeline-lab, records in `results/setup/smoke/`
(pipeline-lab PRs #24, #25, #26, closed unmerged).

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
