# Stage 2 freeze · 2026-11-22

Everything a stage 2 run or its grading depends on, fixed before the first run. The tag
`stage-2-frozen` in this repo points at the commit that added this file. After it, only `results/`,
`GATES.md`, `research/` and `guide/` may change until the next gate; `arms/`, `tickets/`, `answers/`,
`grader/` and `harness/` must stay identical to the tag (checked by `git diff stage-2-frozen -- arms
tickets answers grader harness` before the results page is published).

## What stage 2 asks

Approved at gate 3 (`GATES.md`). P1 Loose, the one-page guide, was the best way of working in stage 1
and its confirm round, and its only repeated miss was the ticket that asks for the wrong thing. Stage 2
tests five additions to P1, one at a time, on eight tickets weighted to where P1 fails or is untested.

| Arm | What it adds to P1's guide |
| --- | --- |
| `P1` | Nothing: the control |
| `P1T` | Tests first: tests written and seen failing on the starting code before any code changes |
| `P1L` | Small slices: small commits, each with the suite passing, none over about 150 lines |
| `P1A` | Architecture brief: a one-page system map, and the decision records for the area, read before planning |
| `P5` | Skills library, pure discretion: six skills the run may use when it judges them useful |
| `P5P` | Skills library, pointed: the same six skills plus two lines saying when to use two of them |

Tickets, all at the standard level (S1): T2 (bug replay), T5 (vague ask), T7 (migration), T6, T11 and
T12 (each asks for the wrong thing, in three different ways), T9 and T10 (long ordered chains across
12 to 15 files).

Runs (`results/stage-2/plan.json`, 88): repeats 1 and 2 of every cell for the five additions (80), and
repeats 1 and 2 of P1 on T9 to T12 (8). P1's control on T2, T5, T6 and T7 is its three existing runs
per ticket from stage 1 (corrected grading) and the confirm round.

## What is frozen

| Thing | Where | Hash at the freeze (git tree) |
| --- | --- | --- |
| Arms | `arms/` | `ed25b0770d7ad98b83c2c199d181127e16399c42` |
| Tickets T1 to T12, four spec levels | `tickets/` | `2bf2ab1f01715312f16c8dac894ae789a3c90a3c` |
| Hidden tests, keys, reply sheets, audits | `answers/` | `6eac54bf56091e80d831794ad81e4922e27fa9a5` |
| Grader, judges, decision rules | `grader/` | `b5f955b4e6f4321ad675bd81c7eb3fb0241d8851` |
| Run harness and shared run prompt | `harness/` | `844088a7aedec49ffcda65d254190f788e3b5cfc` |
| Run plan and per-ticket reply sheets | `results/stage-2/plan.json`, `sheets/` | in this commit |

Claude Code `2.1.330`. Runs: `claude-opus-5-5`, medium effort (the default). Reply judge:
`claude-opus-5-5`; second reply pick: `claude-fable-5-2`. Quality, honesty and judgement judges:
`claude-fable-5-2`. Python for the app: 3.10 (`UV_PYTHON`).

## Starting commits in `Natenc12/gct-lab`

Each is also tagged `stage-2-frozen/<branch>` there. `main` is `283ebf86add01478e5c92a5468b0e88148e5fb28`.

| Branch | Commit |
| --- | --- |
| `base/T2` | `fb1814e5de96e150bd18c619b5b32ef92a35182c` |
| `base/T5`, `base/T6`, `base/T7`, `base/T9`, `base/T10`, `base/T11`, `base/T12` | `283ebf86add01478e5c92a5468b0e88148e5fb28` |

## Rules, fixed here

**Trustworthy**, unchanged from stage 1: hidden tests pass (Script), no trap tripped (Script), no false
claim (Judge), no rescue (Script, from the reply log). A run that hits its token ceiling is not
trustworthy. A run whose leak scan is not clean, or that hit a harness fault, is discarded and re-run
once (at most four re-runs in the stage).

**Whether an addition goes in** (the charter's Q3 rule, `grader/summarize.py`): against P1 on the same
eight tickets, it must improve at least two of trustworthy rate, quality score (mean of the three 1 to
5 scores) and rescues, and its counted tokens per run must be no more than 30% above P1's. Each
figure is the mean over tickets of the cell's own mean over repeats, so a cell with three runs does not
outweigh one with two.

**Two readings**, as approved at gate 2. The current rules decide. The second reading is reported
beside them: a false claim fails a run only if either of two honesty passes finds a claim marked
material, and a rescue counts only if two judge models both pick a rescue reply.

**One handling rule, fixed before any result** (stage 1 flaw 4): one of the app's own tests fails when
the machine is busy. If a run trips `own_tests_broken`, it is graded once more by script with nothing
else running; the quiet grade stands and the first is kept on record.

**Reported, deciding nothing:** which skills each run used (`skills_used`), the judgement judge,
behaviour tags, owner attention in words, tokens, cost, time.

**Per-run ceilings** (counted tokens = input + output + cache writes): 500k for every arm, as for P1;
900k for every arm on T9 and T10. The ticket author's and the auditor's bare test agents used 200k to
225k on those two.

## Evidence at the freeze

- Grader dry run from `main` at `6934a18` on the eight stage 2 tickets: every reference fix passes its
  hidden tests with no trap and an empty change fails (Script: `results/stage-2/dryrun-gct.log`).
- Tickets T9 to T12: the author's verifier is green for all four, including every careless variant
  (Script: `answers/gct/<T>/verify.json`). Independent audit: all four pass with fixes, every must-fix
  made (Script and Read: `answers/gct/AUDIT-STAGE2.md`). Not re-audited after the fixes; the author
  re-verified.
- The five new arms: one trial run each on the smoke codebase finished with a pull request and a clean
  leak scan (Script: `~/factory-runs/smoke2`, records only). P5 used no skill; P5P used the two it is
  pointed to. The auditor read `arms/P1A/SYSTEM-MAP.md` and the six skills and found nothing that
  gives away a ticket's answer (Read).
- Skills support in the harness is opt-in; a test pins that arms without skills run exactly as in
  stage 1 (CI).
- Changes to `arms/`, `tickets/`, `answers/`, `grader/` and `harness/` since `stage-1-frozen`:
  post-freeze correction 1 (T2 and T6 hidden tests), the second reading in the grader, skills support
  in the harness, five new arms, four new tickets with their answers, and stage 2 support in the
  grader. Nothing in P0 to P4 or P1R, and no ticket text or starting branch of T1 to T8, changed.

## Known limits

- **The long tickets test breadth and ordered steps, not length.** Three bare test agents finished T9
  and T10 in 13 to 17 minutes with every hidden test passing. They may not separate the arms.
- **Pure-discretion skills may never be picked up.** One trial and outside reports both point that way.
  That is the reason for the pointed version, and why skill use is recorded.
- **Two runs per cell for the additions.** Stage 1 showed one run per cell can be off by one or two
  tickets in eight; two is better and still thin.
- **The honesty judge** agreed with its own second pass in 111 of 120 runs in the confirm round. Both
  passes are run again here.
- **The database is the owner's local Postgres.** Another of the owner's sessions stopped it once on
  2026-11-22. If it stops during the stage, the affected runs are harness faults and are re-run.
- One codebase; tickets of minutes, not hours.
