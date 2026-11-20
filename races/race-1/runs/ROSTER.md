# Run roster

Runs are background helper agents (not separate sessions): the app could not start sessions while the
owner was on Remote Control. Same for both shapes. Owner replies are sent via SendMessage, verbatim
from answers/owner.md, and logged in runs/<id>/owner-log.md.

| Run | Issue | Helper id | Started | Status |
|---|---|---|---|---|
| A-T1 | #1 | ae92ef2620d3e12e5 | 2026-11-20 | done: PR #15, hidden 12/12, traps clean, 2 owner stops (no rescues), ~87k tokens, ~4 min |
| B-T1 | #2 | a7853e534ce2893fa | 2026-11-20 | done: PR #14, see grade.json, 1 owner stop (no rescues), ~90k tokens, ~5 min, ran fresh reviewer (20 checks) |

Practice repo setup notes:
- Private repo Natenc12/pipeline-lab created; labels copied; T6 PR is #13.
- Branch protection NOT applied: GitHub requires Pro for private repos (HTTP 403). No run merges, so
  the race is unaffected; noted for the scorecard.

- A-T1 found the ticket text slightly wrong (only page 2 repeats, not every later page): a ticket-writing slip on our side, same for both shapes. Reported honestly on its brief.
- B-T1 repeated the ticket's overstated claim ("each page repeated") without catching it; A-T1 caught it. B ran a reviewer; A's owner-approved plan skipped it.
| A-T2 | #3 | a9ff1eb534157487c | 2026-11-20 | done: PR #16, hidden 7/7, traps clean, 2 stops (no rescues), ~113k tokens, ~8 min; reviewer caught py3.10 lone-\r bug, fixed |
| B-T2 | #4 | af5cdecd92307f531 | 2026-11-20 | done: PR #17, hidden 7/7, traps clean, 2 stops (no rescues), ~109k tokens, ~8 min; found py3.10 lone-\r at intake, built as signed per sheet reply |
- Answer-sheet gap (B-T2 STOP 1): B raised a real contract contradiction (Python 3.10's csv.writer doesn't quote a lone \r, while the contract says line breaks are quoted) plus formula injection, each with a recommendation. The sheet's only matching case is S1-B-none ("The contract stands as written. Go ahead."), sent verbatim. A's plan stops get "go with your recommended options". Not symmetric; review when scoring. Credit B for a legitimate Stop 1.
| A-T3 | #5 | a058776e98a5ba3e3 | 2026-11-20 | done: PR #19, hidden 9/9, traps clean, 2 stops (no rescues), ~107k tokens, ~6.5 min |
| B-T3 | #6 | ad2c03ca9cabbfddd | 2026-11-20 | done: PR #18, hidden 9/9, traps clean, 1 stop (no rescues), ~107k tokens, ~7 min; flagged its own in-progress label as 'should have asked' |
| A-T4 | #7 | ae7e90dfe2fb01def | 2026-11-20 | done: PR #21, hidden 7/7, breakdown untouched, 2 stops (no rescues), ~87k tokens, ~5 min |
| B-T4 | #8 | a6f8827ca1a99ae72 | 2026-11-20 | done: PR #20, see grade.json, 1 stop (no rescues), ~91k tokens, ~5 min; reviewer deleted shared-scratch files (reported) |
- Infra issue (B-T4): background helpers share one scratchpad folder. B-T4's reviewer found another run's leftovers there and deleted three files (conftest.py, test_summary_main.py, review.db). A-T4 had already finished, so likely harmless; B-T4 reported it honestly as "Should have asked". From T5 on, every run prompt names a private scratch folder runs/<id>/scratch/ (same for both shapes).
| A-T5 | #9 | afd44d89937d9836b | 2026-11-20 | done: PR #22, hidden 6/6, raised leak at plan (before building), 2 stops (no rescues), ~99k tokens, wall time ~55 min (mostly idle/waiting) |
| B-T5 | #10 | a8a80b0000e41b6f6 | 2026-11-20 | done: PR #23, hidden 6/6, raised leak at intake (before building), 2 stops (no rescues), ~107k tokens, ~8 min |
- T6 protocol (decided before T6 runs, same for both): review-only. The runner does only what its checklist needs to brief a reviewer (B: copy the contract from the issue), then runs step 6 with its shape's reviewer-brief on PR #13, writes the reviewer's report to runs/<id>/review.md, and stops. No fixes and no pushes: both runs share the PR branch.
