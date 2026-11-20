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
| A-T2 | #3 | a9ff1eb534157487c | 2026-11-20 | running |
| B-T2 | #4 | af5cdecd92307f531 | 2026-11-20 | running |
