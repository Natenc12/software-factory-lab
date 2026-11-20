# Run roster

Runs are background helper agents (not separate sessions): the app could not start sessions while the
owner was on Remote Control. Same for both shapes. Owner replies are sent via SendMessage, verbatim
from answers/owner.md, and logged in runs/<id>/owner-log.md.

| Run | Issue | Helper id | Started | Status |
|---|---|---|---|---|
| A-T1 | #1 | ae92ef2620d3e12e5 | 2026-11-20 | running |
| B-T1 | #2 | a7853e534ce2893fa | 2026-11-20 | running |

Practice repo setup notes:
- Private repo Natenc12/pipeline-lab created; labels copied; T6 PR is #13.
- Branch protection NOT applied: GitHub requires Pro for private repos (HTTP 403). No run merges, so
  the race is unaffected; noted for the scorecard.
