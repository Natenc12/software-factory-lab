# Re-running the kit

How to test a new model, or a new way of working, with this kit. One command per step. Every command
below was checked against the code's own `--help` on 2026-11-23. The plan-editing step was tried on a
scratch copy; nothing here was run end to end for this page (Not checked).

The findings these steps produced are in [working-with-claude-code.md](working-with-claude-code.md).

## What must exist first

**On the machine** (this repo's root is the working folder for every command):

- Python 3.11 or later, `git`, `uv`, and the codebase's own toolchain (for example `pnpm` for Hono).
  `psql` only for a Postgres codebase.
- `claude`, signed in. Note the version and keep it fixed for the whole stage: set
  `DISABLE_AUTOUPDATER=1` in the shell that starts the stage. The experiment ran on 2.1.330.
- `gh`, signed in, with access to the practice repository.

**In this repo, per codebase** (`hono` and `sqlglot` are complete examples):

| What | Where | Notes |
| --- | --- | --- |
| A practice repository on GitHub | e.g. `Natenc12/hono-lab`, private | One branch per ticket that the run starts from (`base/T1` …). Upstream CI workflows removed, no agent-instruction file such as `CLAUDE.md` |
| Tickets | `tickets/<codebase>/T*/S1.md` and `meta.json` | Format in [`tickets/README.md`](../tickets/README.md) |
| Answers | `answers/<codebase>/T*/` | Hidden tests, reference fix, `key.json`, stand-in replies, and an audit by someone other than the author. Never inside a run's reach |
| Codebase config | `grader/codebases/<codebase>.json` | Install, lint and test commands; `run_setup` and `run_env`; **sealed-run settings** `"run_sealed": true` and `"run_own_package": "<package name>"` for any public codebase whose real fixes a run could look up. See [`harness/README.md`](../harness/README.md), "Sealed runs" |
| A price for every model you run | `PRICES` in `grader/common.py` | Without one, list-price cost comes out empty |
| The arm | `arms/<name>/` | Top-level `.md` files go into the system prompt; `skills/` and `agents/` are optional. Add its row to `arms/SIZES.md` (CI checks it) |

## The steps

### 0. Prove the answers are right

```bash
python3 -m grader.dryrun hono
```

Every ticket must print GREEN: its reference fix passes and an empty change fails. Fix anything RED
before going further. Also run the kit's own tests, as CI does:

```bash
uv run --no-project --python 3.12 --with pytest==8.3.4 pytest -q
```

### 1. Make a plan

```bash
python3 -m grader.make_plan stage-4 --codebase hono --out-dir results/stage-4-m2-hono
```

This writes `plan.json` and the reply sheets: 48 runs in three rows, `P5P` on Opus 5.5, `P5PF` on
Fable 5.2, `P6P`. The plan's stage name is still `stage-4-hono`. **Rename it**, or the runs land in the
old stage folder, where every finished run is skipped. For a new model, also put it in the `P5PF` row
and drop `P6P`:

```bash
python3 - results/stage-4-m2-hono/plan.json stage-4-m2-hono claude-new-model-id <<'EOF'
import json, sys
path, stage, model = sys.argv[1:4]
p = json.load(open(path))
p["stage"] = stage
p["runs"] = [r for r in p["runs"] if not r["run_id"].startswith("p6p-")]
for r in p["runs"]:
    if r["run_id"].startswith("p5pf-"):
        r["model"] = model
json.dump(p, open(path, "w"), indent=1)
EOF
```

Keep the stage name starting with `stage-4`: that is how the summary knows to apply the model rule
(`P5PF` against `P5P`, fixed in `grader/summarize.py`). Keep the `P5P` runs in the plan, so the
control runs on the same day and the same CLI version as the new model.

**For a new way of working** instead: give its runs a new prefix (`p7-t1-1` …), point each run's `arm`
at `arms/P7`, and add `P7` and `p7` to each run's `redact` list so the reply judge never sees the
arm's name. The summary reports every row's figures (`per_row` in `summary.json`), but the fixed
decision rules know only the existing row names. Either compare the figures by a rule you write down
before any run, or add the rule to `grader/summarize.py` and freeze it.

Per-run ceilings: `--row-ceiling P5PF=500000` (repeatable) sets a row's counted-token ceiling.

### 2. Run the stage

```bash
DISABLE_AUTOUPDATER=1 python3 -m harness.stage results/stage-4-m2-hono/plan.json
```

Four runs at a time by default (`--parallel` to change). Safe to start again after a stop: finished
runs are skipped. If a usage limit stops it, the runner marks the run `plan_limit` and waits
(`--limit-wait-min`, `--max-limit-retries`). Runs go to `~/factory-runs/stage-4-m2-hono/`.

### 3. Grade

```bash
results/stage-4/tools/grade_stage4.sh stage-4-m2-hono
```

It grades each finished run: leak scan, script grade, the three judges, the verdict, then the second
reading and the Opus check. It works four at a time and ends when the stage log shows its last line,
so it can start alongside step 2. It sets `TMPDIR=~/factory-runs/.grading-tmp`, so no run can read the
grader's checkouts, which hold the hidden tests. It assumes this repo is at
`~/repos/software-factory-lab` and the runs at `~/factory-runs`.

The same steps by hand, for one run (from [`grader/README.md`](../grader/README.md)):

```bash
python3 -m harness.scan ~/factory-runs/stage-4-m2-hono/p5pf-t1-1
```

```bash
python3 -m grader.grade ~/factory-runs/stage-4-m2-hono/p5pf-t1-1
```

```bash
python3 -m grader.judge ~/factory-runs/stage-4-m2-hono/p5pf-t1-1 --kind honesty
```

(and `--kind quality`, `--kind judgement`)

```bash
python3 -m grader.verdict ~/factory-runs/stage-4-m2-hono/p5pf-t1-1
```

Grade before tearing a run down: teardown removes the checkout.

### 4. Summarise

```bash
python3 -m grader.summarize stage-4-m2-hono stage-4-m2-sqlglot --out-dir results/stage-4-m2
```

Two codebases in one call are pooled, each ticket weighted equally, and each codebase is also reported
alone. The decision is `decision` in `summary.json`; `decision_second_reading` sits beside it. Report
both gradings if you correct anything after the freeze.

### 5. Clean up

```bash
python3 -m harness.sandbox down ~/factory-runs/stage-4-m2-hono/p5pf-t1-1
```

Drops the run's database and files and keeps its records (`--all` removes the records too). Do it once
results are accepted: stage 4's 97 run folders took about 166 GB.

## Things that bit us

Shortest first. Each was found in a real stage; the source says where it is written up.

1. **A ticket rewritten without its hidden test.** The ticket's example said `2,000,000`, the test
   wanted `2000000`; every arm failed it. Re-check hidden tests after every ticket edit (stage 1, flaw 1).
2. **The "existing test changed" trap punishes good fixes.** It fires on any edit to an old test,
   even one that strengthens it. List every test a correct fix may touch in `tests_may_change`
   (stage 2 flaws 1 and 3, stage 2b flaw 3, stage 4 flaw 4).
3. **Ignored SIGINT breaks a test.** Started under `nohup`, the grader inherited it and one of the
   app's tests failed. The grading scripts reset it (stage 1, flaw 2).
4. **A busy machine fails a timing test.** One lock test failed under load and tripped
   `own_tests_broken`. Re-grade with nothing else running before trusting that trap (stage 1, flaw 4).
5. **Waiting scripts that match command lines wait on each other.** Ten and a half hours lost
   overnight. Wait on a job's own exit or its log's last line (stage 1, flaw 6).
6. **A grading loop that counts tries for runs it never picked.** Eight runs were skipped. Count a try
   only when a run is picked up (stage 2b, flaw 2).
7. **The leak scan cries wolf.** It discarded one run for a relative path after `cd`, and one for the
   word `github.com` in a refused call. Read `scan.json` before trusting a discard; the rule still
   re-runs it once (stage 2b flaw 1, stage 4 flaw 3).
8. **The guard misreads heredocs.** It reads each line of `cat <<'EOF' … EOF` as a command, so a code
   line starting `open(` hit the macOS `open` block. Runs work around it (`harness/TRIALS.md`, trials
   12–18).
9. **Sealed runs can't read the owner's git settings.** Commits printed "unable to access
   ~/.gitconfig" and runs worked around it (stage 4, flaw 6).
10. **The honesty judge crashed on one transcript record.** A message that was text, not an object.
    Fixed in the grader (stage 2, flaw 2).
11. **The judge read a worker's tool calls as the lead's own.** Four verdicts in the lead-with-workers
    row, as frozen. Worker calls are now labelled; earlier stages were not re-judged (stage 4, flaw 1).
12. **Judging is not perfectly repeatable.** Two honesty passes agreed in 111 of 120 runs; one run
    gained a three-byte false claim on a second pass. Judge twice and mark material against slip
    (stage 1 flaw 5, stage 4 flaw 2).
13. **The reply judge can pick a rescue that wasn't earned.** A second blind pick by another model
    agreed on 37 of 47 reply ids; the rescue flag differed in 2 (stage 1, flaw 3).
14. **The summary's printed line over-weights a lone re-run.** Read
    `decision.rows.*.trustworthy_per_8`, not the printed mean (stage 4, flaw 5).
15. **The `fable` alias depends on the CLI version.** On 2.1.302 `--model fable` ran Fable 5.1. Use
    full model IDs and a fixed CLI version (`research/harness-facts.md`, item 8).
16. **Disk.** Each Hono run keeps its own pnpm store: about 166 GB for 97 runs (stage 4, flaw 8).
17. **Public answers reachable from inside a run.** On public codebases the real fix sat in shared
    package caches, PyPI and other sessions' temp folders. Seal every run on such a codebase, grade
    from a temp folder runs can't read, and keep practice, upstream and answer copies out of `/tmp`
    during a stage (`results/stage-4/FREEZE.md`, `harness/README.md`).
