# Stage 2b freeze · 2026-11-22

A short round approved at gate 4 (`GATES.md`), fixed before its first run. The tag `stage-2b-frozen`
points at the commit that added this file; `arms/`, `tickets/`, `answers/`, `grader/` and `harness/`
must stay identical to it until the round's results page is published.

## What it asks

Stage 2 left two additions to the one-page guide tied: the pointed skills library (`P5P`, in by the
rule) and the architecture brief (`P1A`, ahead on trust, out on a quality tie). The owner asked
whether the two could be combined, with a process that travels between projects in mind. This round
adds the combination and a third run of each.

| Arm | What it is | Runs here |
| --- | --- | --- |
| `P5P` | The guide with the skills library, pointed. The base, by the rule | repeat 3 on eight tickets (8) |
| `P1A` | The guide with the architecture brief | repeat 3 on eight tickets (8) |
| `P5PA` | `P5P` plus the architecture brief: P5P's guide and skills, P1A's "Before you plan" section and system map, nothing else | repeats 1 and 2 on eight tickets (16) |

Tickets: the eight of stage 2 (T2, T5, T6, T7, T9, T10, T11, T12) at the standard level, same
starting commits as `stage-2-frozen`. 32 runs (`results/stage-2b/plan.json`).

## What is frozen

| Thing | Where | Hash at the freeze (git tree) |
| --- | --- | --- |
| Arms | `arms/` | `de9a09de42fc424330296508a68553fb07949dfd` |
| Tickets | `tickets/` | `2bf2ab1f01715312f16c8dac894ae789a3c90a3c` |
| Hidden tests, keys, reply sheets, audits | `answers/` | `6e494aed15c8e875498823312c2ae29f01695fa6` |
| Grader, judges, decision rules | `grader/` | `218e4822569a0ff9ca35acaf5010f0bb42ab20dd` |
| Run harness | `harness/` | `844088a7aedec49ffcda65d254190f788e3b5cfc` |
| Run plan and reply sheets | `results/stage-2b/plan.json`, `sheets/` | in this commit |

Claude Code `2.1.330`. Runs: `claude-opus-5-5`, medium effort. Judges as in stage 2.

Changes to those five folders since `stage-2-frozen`: post-freeze correction 2 (T11's key allows
extending the queue writers' census test), post-freeze correction 3 (the grader skips a transcript
record whose message is not an object), the new arm `P5PA`, and stage 2b support in the grader. This
round is graded with both corrections in place from the start.

## Rules, fixed here

- **Trustworthy** as in every stage: hidden tests pass, no trap tripped, no false claim, no rescue.
- **The round's rule** (`GATES.md`, gate 4, item 4): `P5PA` replaces `P5P` as the base only if, on
  the eight tickets with each ticket weighted equally, it is at least one trustworthy pull request in
  eight better than `P5P` (all three runs of P5P, both of P5PA) and its counted tokens per run are no
  more than 30% above `P5P`'s. Otherwise `P5P` stays. `P1A`'s third run is reported and decides
  nothing.
- **Two readings**: the current rules decide; the second reading is reported beside them.
- **Busy-machine handling** as in stage 2: a run that trips `own_tests_broken` is graded once more
  with nothing else running, and the quiet grade stands.
- **Ceilings**: 500k counted tokens a run, 900k on T9 and T10.

## Evidence at the freeze

- The full test suite passes on the frozen commit (215 tests; Script).
- `P5PA` is built only from existing files: tests pin that its guide is P5P's plus P1A's section, its
  map equals P1A's and its skills equal P5P's (CI).
- One trial run of `P5PA` on the smoke codebase finished with a pull request and a clean leak scan.
  The six skills were loaded and the run used none of them (Script). The map describes a different
  codebase from the smoke one, so this says little either way; skill use is recorded for every run.
- Tickets and answers are those of stage 2 with correction 2; the author re-ran the verifier and the
  dry run for T11 after it (Run says).

## Known limits

- Two runs per cell for `P5PA`, three for the other two. A gap of half a ticket in eight is one run.
- The combination may dilute the two pointing lines; the trial hints at that. If so the record of
  skill use will show it.
- Still one codebase. Whether the skills carry to other projects is stage 4's question.
