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

`down` removes the clone, scratch and database and keeps `harness/` (records). Add `--all` to remove
the whole folder. The pull request and its branch on GitHub are left as they are.

## What to expect

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
