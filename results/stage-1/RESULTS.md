# Stage 1 results (provisional)

Page: https://claude.ai/artifact/K2Qi65V5g1H4MjLadG25FE (copy: `page/stage-1-results.html`). 76 runs, one
per cell, graded 2026-11-21 and 22. Nothing here has been repeated; the confirm round is proposed at gate 2.

| Arm | Trustworthy of 8, as frozen | With the corrections | Tokens per run | Words the owner reads per ticket | Stops per ticket |
|---|---|---|---|---|---|
| P0 Bare | 4 | 5 | 84k | 1,429 | 0.1 |
| P1 Loose | 6 | 7 | 80k | 1,493 | 0.1 |
| P1R Loose + reviewer | 6 | 7 | 125k | 1,487 | 0.1 |
| P3 Contract | 5 | 7 | 185k | 2,352 | 1.25 |
| P2 Checklist | 5 | 6 | 154k | 2,791 | 2.1 |
| P4 Team | 5 | 6 | 580k | 2,596 | 1.6 |

Bare arm by ticket level, seven build tickets: rough 1, standard 4 (5 corrected), full spec 5 (6), spec
plus acceptance tests 6 (6). P1 on spec plus acceptance tests: 6 of 7.

By the fixed rules, in both gradings (Script: `as-frozen/summary.json`, `corrected/summary.json`):
best process arm P1; process is needed (margin 2 per 8); no arm dropped; a full spec does not replace
the pipeline (within one, but the owner's attention is higher).

- `as-frozen/`: graded with the tree at tag `stage-1-frozen`. `corrected/`: the same runs with the
  corrections in `FLAWS.md` (items 1, 3 and 4). `runs.json` is one record per run.
- `git diff stage-1-frozen -- arms tickets answers grader harness` shows one change since the freeze:
  post-freeze correction 1 (the T2 and T6 hidden tests, `answers/` only).
- Run records stay on the orchestrator's machine under `~/factory-runs/stage-1/`; the pull requests are
  open and unmerged on the practice repository.
- Spend: 12.3M counted tokens for runs and owner replies, 6.8M for grading judges (Script), about 0.6M
  for re-checks (estimate).
