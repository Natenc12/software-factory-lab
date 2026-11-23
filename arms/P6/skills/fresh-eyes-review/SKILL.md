---
name: fresh-eyes-review
description: Use when the change is ready and before opening the pull request.
---
Start one subagent. Give it only the ticket, the command that shows your diff against the starting
commit, and how to run the tests. Do not paste your reasoning into its brief. Ask it to find
defects, missed cases, scope creep, and any claim in your draft description that the evidence does
not support.

Judge each finding yourself. Fix the real ones and re-run the tests.
