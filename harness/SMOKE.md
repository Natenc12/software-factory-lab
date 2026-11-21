# Smoke runs on pipeline-lab

Two runs of race 1's ticket T1 on `Natenc12/pipeline-lab`: one bare, one given race 1's shape B as its
arm file. Run them from the root of this repo, after the harness pull request is merged. Each opens one
branch and one pull request in pipeline-lab; nothing is merged.

```bash
python3 -m harness.run p0-t1-1 --stage smoke --ticket races/race-1/tickets/T1-A.md --repo Natenc12/pipeline-lab --base main --model claude-opus-5-5 --ceiling 400000
```

```bash
python3 -m harness.run sb-t1-1 --stage smoke --arm races/race-1/shapes/B/SKILL.md --ticket races/race-1/tickets/T1-A.md --repo Natenc12/pipeline-lab --base main --model claude-opus-5-5 --ceiling 400000 --redact "shape B" --redact "contract-first"
```

Both use the example reply sheet (`harness/examples/reply-sheet.md`) and the default reply judge
(`claude-sonnet-5-5`). Each run's folder is `~/factory-runs/smoke/<run-id>/`; its records are in
`harness/` there: `run.json`, `owner-log.jsonl`, `transcript.jsonl`, `lab-events.jsonl`, `guard.log`.

Afterwards, for each run:

```bash
python3 -m harness.scan ~/factory-runs/smoke/p0-t1-1
```

```bash
python3 -m harness.sandbox down ~/factory-runs/smoke/p0-t1-1
```

`down` removes the clone, scratch, database and the run's control folder
(`~/factory-runs/smoke/.control/<run-id>/`) and keeps `harness/` (records). Add `--all` to remove
the whole folder. The pull request and its branch on GitHub are left as they are.

## What to expect

- Commands run in Claude Code's OS sandbox: only PyPI is reachable, and `lab` is the only way to GitHub.
  `sandbox_violations` lines in the transcript show anything it refused.
- **Shape B was written for race 1.** Its "Benchmark rules" tell the run to use `gh`, an issue number,
  and pages under `~/repos/pipeline-bench/runs/`. In this harness those are blocked by the guard, so
  the run will see "Blocked by the lab guard" and should fall back to `lab`, `TICKET.md` and its
  `scratch/` folder. That is a fair test of the harness, but not of shape B; the real P3 arm needs
  those lines rewritten.
- Shape B's stop lines (`STOP 2: ... — page: <path>`) are recognised: any line starting `STOP`, an
  optional word, then a colon.
- Race 1 runs cost 90k to 115k tokens on its own measure. `run.json` shows input, output, cache write
  and cache read separately, so the two measures can be compared.
- Exit code 75 means a plan or rate limit stopped the run. Re-run the same command after the reset
  time in `run.json` (`resets_at`) and it continues the same session.

## Arm smoke runs and the gct-lab environment check (2026-11-21, Claude Code 2.1.330)

One run per arm on pipeline-lab (race 1 ticket T1, `claude-opus-5-5`), graded with `grader.grade`
against the fixture package in `tests/fixtures/race1/`. Summaries are in `results/setup/smoke/`.

| Run | Hidden tests (Script) | Counted tokens | Wall time | Owner stops | Subagents started |
| --- | --- | --- | --- | --- | --- |
| p1-t1-1 | 12/12 | 26,693 | 62 s | 0 | none |
| p1r-t1-1 | 12/12 | 49,046 | 107 s | 0 | reviewer |
| p2-t1-1 | 12/12 | 62,285 | 192 s | 2 (`default`, `final`) | reviewer |
| p3-t1-1 | 12/12 | 70,498 | 319 s | 1 (`final`) | reviewer |
| p4-t1-1 | 12/12 | 204,527 | 497 s | 1 (`final`) | planner, architect, tester x3, builder, reviewer |

All five leak scans were clean and no trap tripped (Script). In p4-t1-1 the lead made no edit outside
`scratch/`, and the reviewer's role hook refused three writes and one read in a real run (Script, from
the transcript). The quality and honesty judges (`claude-fable-5-2`) and `grader.verdict` were run on
p1-t1-1 and p4-t1-1: both trustworthy, no false claims (Judge). Pull requests 28 to 32 on pipeline-lab
were closed unmerged and the sandboxes removed.

**gct-lab inside the sandbox.** Two runs on `claude-haiku-5-5` with a fixed prompt that only ran
`uv sync --extra dev`, `uv run python scripts/migrate.py` and `uv run pytest -q -m "not live"` on
gct-lab `main`, with `UV_PYTHON=3.10`:

- env-gct-1: install and migrations worked; **38 of 1,175 tests failed**, all in
  `tests/scripts/test_http_smoke.py`, which starts a server on localhost. The sandbox blocked it.
- env-gct-2, with `sandbox.network.allowLocalBinding: true` added to the run settings: **1,175 passed**.

So the run settings now allow local ports, and `grader/codebases/gct.json` carries
`run_env: {"UV_PYTHON": "3.10"}`, which `grader.make_plan` passes to every gct run through the new
`--env KEY=VALUE` option of `harness.run` (the app does not compile on Python 3.13+). Not checked: the
same on Linux.

## SIGINT check on gct-lab (2026-11-21)

Stage runs start in the background, so the harness inherits SIGINT ignored, and before this fix every
`claude` it started did too; gct-lab's `test_both_signals_leave_the_job_in_the_same_state[sigint]`
then fails in an untouched tree. The harness now resets SIGINT and SIGQUIT to their defaults in each
`claude` process (sessions and the reply judge). Check: a sandbox on `Natenc12/gct-lab` at `base/T1`
(`--db postgres --env UV_PYTHON=3.10`, `claude-haiku-5-5`, a prompt that only ran `uv sync --extra dev`,
`uv run python scripts/migrate.py`, `uv run pytest -q -m "not live"`), started as
`(trap '' INT; python3 -m harness.run ...) &`: **396 passed, 1 deselected**, the `[sigint]` case included.
About 10k counted tokens; the scan was clean and the sandbox and database were torn down.
