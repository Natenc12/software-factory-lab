# Stage 2 results

Page: https://claude.ai/artifact/VfgFrkDdVNx9mLcxwZkFkd (copy: `page/stage-2-results.html`). Freeze note:
`FREEZE.md` (page copy: `page/stage-2-freeze.html`). 88 runs on 2026-11-22, graded, none discarded.

Trustworthy pull requests of 8 tickets, each ticket weighted equally (T2, T5, T6, T7, T9, T10, T11, T12;
P1 is the control, with its three earlier runs on T2, T5, T6 and T7):

| Arm | As frozen | With the corrections | Second reading, corrected | Tokens per run | By the rule |
|---|---|---|---|---|---|
| P1 Loose (control) | 5.5 | 6.0 | 6.2 | 102k | |
| P1T + tests first | 5.0 | 6.0 | 6.0 | 108k | stays out (0 of 3) |
| P1L + small slices | 4.0 | 5.0 | 5.0 | 113k | stays out (1 of 3) |
| P1A + architecture brief | 6.5 | 7.5 | 7.5 | 107k | stays out (1 of 3) |
| P5 + skills, pure discretion | 5.0 | 6.5 | 7.0 | 127k | stays out (0 or 1 of 3) |
| P5P + skills, pointed | 6.0 | 7.0 | 7.0 | 113k | **goes in** (2 of 3, cost x1.10) |

The rule (charter Q3, `grader/summarize.py`) gives the same answer in all four cases: as frozen or
corrected, current rules or second reading (Script: `as-frozen/summary.json`, `corrected/summary.json`,
keys `decision` and `decision_second_reading`).

- Wrong-request tickets: on T11 and T12 every run of every arm raised the problem before building (24
  of 24). On T6: P5P 2 of 2, P1A 1 of 2, P1T, P1L and P5 0 of 6, P1 0 of 3. (Script)
- Skill use: P5 used a skill in 3 of 16 runs (fresh-eyes-review only); P5P in 16 of 16, each of the two
  pointed skills in 15. (Script)
- Corrections: `FLAWS.md` items 1 (T11 key) and 2 (grader crash on one run), made in pull requests 33
  and 32. `git diff stage-2-frozen -- arms tickets answers grader harness` shows only those two.
- Spend: 10.3M counted tokens for runs and owner replies, 8.2M for grading judges, 1.1M for the second
  reading. (Script)
- `corrected/` was made from a copy of the stage 2 records with the 12 T11 runs re-graded and
  `p5-t10-1` judged, using the checkout at the corrections. Run records stay on the orchestrator's
  machine.
