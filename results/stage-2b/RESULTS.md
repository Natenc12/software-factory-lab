# Stage 2b (tie-break round) results

Page: https://claude.ai/artifact/9cB9GrBLpzS5N5LY6KM7Qy (copy: `page/tie-break-results.html`). Freeze note:
`FREEZE.md`. 33 runs on 2026-11-22: 32 planned and one re-run. Graded with post-freeze corrections 2
and 3 in place from the start.

Trustworthy pull requests of 8 tickets, each ticket weighted equally, all runs of each arm (stage 2 and
this round; P1's are its earlier runs):

| Arm | Runs | Current rules | Second reading | Tokens per run | Raised T6 before building |
|---|---|---|---|---|---|
| P1 Loose | 20 | 6.0 | 6.2 | 102k | 0 of 3 |
| P1A + architecture brief | 24 | 7.3 | 7.3 | 110k | 1 of 3 |
| P5P + skills, pointed | 24 | 7.3 | 7.0 | 116k | 3 of 3 |
| P5PA + skills, pointed, and the brief | 16 (+1 discarded) | 7.5 | 7.5 | 126k | 2 of 2 |

**The round's rule** (`GATES.md`, gate 4, item 4): `P5PA` replaces `P5P` only if it is at least one
trustworthy pull request in eight better at no more than 30% extra cost. It is 0.17 better (0.5 on the
second reading) at 9% more cost, so **`P5P` stays the base** (Script: `summary-against-p5p/summary.json`).

- Against P1 under the charter's Q3 rule, with three runs in, `P1A`, `P5P` and `P5PA` all go in
  (Script: `summary/summary.json`). The three are tied with each other.
- Skill use: check-the-ask in 23 of 24 `P5P` runs and 16 of 16 `P5PA` runs; prove-each-claim in 23 of 24
  and 15 of 16 (Script).
- One run (`p5pa-t10-2`) was discarded by the leak scan on a false positive and re-run once as
  `p5pa-t10-3` (`plan-rerun.json`, `FLAWS.md` item 1).
- `P5P` needed one correction round in its 24 runs. With `P5P` at 7.3 of 8, the charter's Q5 rule
  (Fable builds only if it gains one per 8 or cuts correction rounds by 30%) cannot come out for Fable
  on these eight tickets.
- Spend: 4.3M counted tokens for runs and owner replies, 3.1M for grading judges, 0.2M for the second
  reading (Script).
