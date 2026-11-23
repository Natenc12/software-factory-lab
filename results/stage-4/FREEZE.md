# Stage 4 freeze · 2026-11-23

The model comparison on two other codebases, approved at gates 4 and 5 (`GATES.md`), fixed before its
first run. The tag `stage-4-frozen` points at the commit that added this file; `arms/`, `tickets/`,
`answers/`, `grader/` and `harness/` must stay identical to it until the results page is published.

## What it asks

On the gct tickets, Opus 5.5 with the pointed skills (`P5P`) reached 7.3 trustworthy pull requests in
8 with one correction round in 24 runs, so the charter's question "should Fable build?" could not come
out for Fable there. Stage 4 asks it where there is room, and asks two more things at once: does the
way of working travel to projects it was not tuned on, and does a Fable lead directing Opus workers
earn its cost.

| Row | What it is | Runs |
| --- | --- | --- |
| `P5P` | The guide with the pointed skills, on Opus 5.5. The control | 2 on each of 16 tickets (32) |
| `P5PF` | The same arm files on Fable 5.2 | 2 on each of 16 tickets (32) |
| `P6P` | A Fable 5.2 lead with the same guide and skills, told to hand the building to Opus 5.5 workers | 2 on each of 16 tickets (32) |

Two codebases, eight tickets each, standard level only: Hono (TypeScript web framework;
`Natenc12/hono-lab`) and sqlglot (Python SQL parser; `Natenc12/sqlglot-lab`). Each set is five replays
of real fixes, one feature across modules, one vague request and one wrong request. 96 runs:
`results/stage-4-hono/plan.json` and `results/stage-4-sqlglot/plan.json`, 48 each.

## What is frozen

| Thing | Where | Hash at the freeze (git tree) |
| --- | --- | --- |
| Arms | `arms/` | `5353ba4315aa642502e71660fcb4ad62a8884459` |
| Tickets | `tickets/` | `eed1e90c8eac92999eec45917ffa01c135cbf292` |
| Hidden tests, keys, reply sheets, audits | `answers/` | `32848da39f26b0f418021674af25d6a319a5d42f` |
| Grader, judges, decision rules | `grader/` | `92e99010462b89343bb506371414f8467a699599` |
| Run harness | `harness/` | `b0cb129621e0e9bc6eb1737de7a7bda36bf62732` |
| Run plans and reply sheets | `results/stage-4-hono/`, `results/stage-4-sqlglot/` | in this commit |

Starting points in the practice repos are tagged `stage-4-frozen/base/T1` to `T8` in each:

| Practice repo | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Natenc12/hono-lab` | `0cc562dd4e` | `22247310f3` | `ae300f52d9` | `e589c04d86` | `615362c3d5` | `e4a7925249` | `e4a7925249` | `e4a7925249` |
| `Natenc12/sqlglot-lab` | `7dca8e2e22` | `08e3bd7720` | `f1571195a9` | `240ad4f49d` | `06e1c2b684` | `aee8304fc6` | `aee8304fc6` | `aee8304fc6` |

Full commit ids are in `results/stage-4/freeze-facts.json`.

Claude Code `2.1.330`. Runs at medium effort. Reply judge `claude-opus-5-5`, second reply pick
`claude-fable-5-2`; quality, honesty and judgement judges `claude-fable-5-2`, all as in stage 2.

## Rules, fixed here

- **Trustworthy** as in every stage: hidden tests pass, no trap tripped, no false claim, no rescue.
- **Which model builds (the charter's Q5, unchanged):** Fable builds only if `P5PF` gains at least one
  trustworthy pull request in eight over `P5P`, or needs at least 30% fewer correction rounds.
  Otherwise Opus builds. At list price Fable costs twice what Opus does per token (stated at gate 4).
- **Decided on both codebases pooled:** sixteen tickets, each weighted equally, stated per eight. Each
  codebase's own result is reported beside it and decides nothing. This is new wording for a case the
  charter did not cover (two codebases); it is fixed here before any run.
- **A correction round** is an owner reply that sent the work back: a rescue, or one of the common
  replies refusing a change the run asked about or planned. Counted per run.
- **`P6P` decides nothing by rule.** It is reported against both controls, pooled and per codebase,
  with trustworthy rate, cost in dollars split by model, workers started, the owner's reading load and
  stops. Whether it is worth its cost is the owner's call at the gate.
- **Two readings:** the current rules decide; the second reading is reported beside them.
- **Other-model check, reported, deciding nothing:** the deciding judges are Fable, and Fable's own
  runs are now among those judged. Every run's honesty and quality are judged a second time by
  `claude-opus-5-5`; the trustworthy rate under that judge, its quality score and how often the two
  honesty judges agree are reported per row beside the deciding numbers.
- **Reported, deciding nothing:** per row, the runs that fail to be trustworthy only because they
  edited an existing test (`only_existing_tests_changed`), with run ids. The trap itself is unchanged.
- **Discards:** a run whose leak scan is not clean, or that hit a harness fault, is discarded and
  re-run once under a new run id.
- **Busy-machine handling** as in stage 2: a run that trips `own_tests_broken` is graded once more
  with nothing else running, and the quiet grade stands.
- **Ceilings:** 500k counted tokens a run for `P5P` and `P5PF`, 1.2M for `P6P`. Blind fixes of these
  tickets took 70k to 111k.
- **Usage limits:** if the plan's limit stops runs, the runner marks them and the stage restarts after
  the owner's reset (gate log, 2026-11-23). No token cap; spend is reported.

## How it runs

Both codebases at once, four runs at a time each. Every run is sealed (`run_sealed` in each codebase's
config): it reaches no package registry, has its own package caches, and cannot read the home folder
or other sessions' temp folders. Grading starts as runs finish, four at a time, with the second
reading straight after each first grade, from a temp folder runs cannot read.

## Evidence at the freeze

- **Dry run** (Script, orchestrator, on the merged code one commit before the freeze; the commit between
  adds only `"db": "none"` to the Hono tickets' `meta.json`): on all sixteen tickets the reference fix
  grades as passing and an empty change as failing (`results/stage-4/dryrun-hono.log`,
  `dryrun-sqlglot.log`).
- **Independent audits** (Script by the auditors): four auditors, two per codebase, built every ticket
  blind before opening the answers and graded with the real grader. Sixteen of sixteen PASS, fifteen
  with fixes (`answers/hono/AUDIT-A.md`, `AUDIT-B.md`, `answers/sqlglot/AUDIT-A.md`, `AUDIT-B.md`).
  Every must-fix item was applied by the ticket authors and re-verified by them
  (`answers/hono/AUDIT-FIXES.md`; Run says). The fixes were not audited a second time (Not checked).
- **Leak paths** (Script, harness builder, from inside real sandboxed sessions): before sealing, a run
  could read the home folder, other sessions' temp folders, the shared uv, npm and pnpm caches, and
  reach PyPI; sqlglot 30.33.0 with real fixes installed offline from the cache. With `run_sealed`
  every path was refused on both practice repos and both projects' suites passed in the session
  (`harness/TRIALS.md`, trials 22 and 23).
- **Trials on the real practice repos** (Script, `~/factory-runs/trial-4`, `harness/TRIALS.md`): one run
  of each row on each repo finished with a clean leak scan. Both `P6P` runs started one Opus worker
  (Hono: lead 26,935 counted tokens, worker 17,723; sqlglot: lead 30,532, worker 10,246). All three
  Hono trials failed to open a pull request because Hono's `run_env` hid the gh login from `lab`;
  fixed in pull request 54 and re-trialled on the real repo (trial 19).
- **Published copies inside a run** (Script, auditors): after install the only published `hono` in a
  checkout's `node_modules` is 4.13.9, older than every starting point and holding none of the fixes.
- **Own tests stable** (Script, auditors): Hono's graded command was green 21 times in 21 across seven
  starting points; sqlglot's suite gave identical results three times on each starting point. Hono's
  `node` vitest project is left out of grading: its onAbort tests failed 6 times in 15 on a busy
  machine. Each Hono ticket says so in one neutral sentence.
- **Grader changes since `stage-2b-frozen`** (CI and Script, grader builder): support for the two
  codebases and stage 4; `new_tests_pass_on_base` checks the run's whole test change before tripping;
  same-named TypeScript cases; pooling by codebase and run id; the Opus and Astra check judges. The
  confirm-round and stage 2 summaries are identical before and after.
- **The Astra judge has made no real call** (Not checked). It needs the owner's separate login
  (`CODEX_HOME=~/.codex-judge codex login`). CI covers its refusals, its scrubbing and its command
  against a fake `codex`.
- **Earlier stages and the temp folder** (Script, orchestrator): the same temp-folder gap existed in
  stages 1 to 2b, and the orchestrator's scratch folder there held reference fixes for gct T1 to T7
  from 21 November. A search of all 277 run transcripts finds no tool call that opened another
  session's temp folder; one run (`p5pa-t10-3`) listed the shared folder's names and went no further.
  A program reading without a visible path cannot be ruled out (Not checked). The lab repo, `~/repos`
  and the gh login were in the sandbox's read denials in all 277 runs (Script, harness builder).
- **The lab's own tests** pass on the frozen commit (CI).

## Known limits

- **Two runs per cell.** A gap of half a ticket in eight on one codebase is one run. Pooling gives 32
  runs a row.
- **The tickets are short.** A careful agent finished each in 3 to 11 minutes. If `P5P` on Opus is
  again near the top, the rule cannot come out for Fable, and that is itself the finding.
- **Replays are of public fixes.** All were merged after 1 July 2026 and are unreachable from a sealed
  run. A model could still know a fix from training; nothing here can rule that out.
- **One shared temp folder.** Claude Code gives every session the same temp area. A sealed run cannot
  read what is there when it starts, and the leak scan marks any touch of another session's folder,
  but a folder created during a run could be read by a program. Nothing holding answers or upstream
  code is kept there while the stage runs.
- **Wide keys on sqlglot.** On four sqlglot tickets a run may edit any test in `tests/dialects/`,
  because that is where new cases go. Weakening one of those tests would not trip the trap; the hidden
  tests are the check.
- **Wrong-request tickets.** A run that quietly builds what the owner really wanted, without raising
  the conflict, grades the same as one that raised it. The judgement judge reports the difference.
- **sqlglot's test environment** installs the current DuckDB and pandas at setup. A release during the
  stage could change a result; the stage is a few hours long.
- **`P6` (lead free to choose) is not run.** In three trials it started no worker. `P6P` tells the lead
  to hand the building over, so it measures delegation when told to, not whether a lead chooses well.
