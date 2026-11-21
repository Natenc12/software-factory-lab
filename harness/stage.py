"""Run a stage: every run in a plan file, N at a time, inside a token budget.

    python -m harness.stage results/stage-1/plan.json [--parallel 4]

Plan file (JSON; relative paths are taken from the root of this repo):

    {"stage": "stage-1", "budget_tokens": 24000000, "parallel": 4,
     "defaults": {"repo": "Natenc12/gct-lab", "model": "claude-opus-5-5", "db": "postgres",
                  "reply_sheet": "answers/reply-sheet.md"},
     "runs": [{"run_id": "p0-t1-1", "ticket": "tickets/gct/T1.md", "base": "t1-start", "ceiling": 400000},
              {"run_id": "p3-t1-1", "arm": "arms/P3", "ticket": "tickets/gct/T1.md", "base": "t1-start",
               "ceiling": 700000}]}

Each run is `python -m harness.run` in its own process. Finished runs are skipped, so the command is safe
to re-invoke. A run that stops on a plan or rate limit pauses new starts until the limit resets, then is
continued. New starts halt once counted tokens (runs plus reply judge) reach 80% of the budget.
Exit codes: 0 all runs done, 3 halted at the budget line, 1 some runs need attention.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

from harness.common import FINAL, LAB_ROOT, check_stage, read_json, run_dir, runs_root, write_json

FLAGS = {
    "arm": "--arm",
    "ticket": "--ticket",
    "repo": "--repo",
    "base": "--base",
    "pr_base": "--pr-base",
    "repo_url": "--repo-url",
    "model": "--model",
    "ceiling": "--ceiling",
    "reply_sheet": "--reply-sheet",
    "judge_model": "--judge-model",
    "max_stops": "--max-stops",
    "db": "--db",
    "effort": "--effort",
    "prompt_file": "--prompt-file",
    "redact": "--redact",
    "forbid": "--forbid",
    "max_wall_min": "--max-wall-min",
    "claude_bin": "--claude-bin",
    "gh_bin": "--gh-bin",
}
PATH_KEYS = ("arm", "ticket", "reply_sheet", "prompt_file")
HALT_AT = 0.8


def run_args(stage: str, spec: dict, root: str | None) -> list[str]:
    args = [spec["run_id"], "--stage", stage]
    if root:
        args += ["--runs-root", root]
    for key, flag in FLAGS.items():
        val = spec.get(key)
        if val is None:
            continue
        for v in val if isinstance(val, list) else [val]:
            if key in PATH_KEYS and not Path(str(v)).is_absolute():
                v = LAB_ROOT / str(v)
            args += [flag, str(v)]
    return args


def counted(stage: str, run_ids: list[str], root: str | None) -> int:
    total = 0
    for rid in run_ids:
        rec = read_json(run_dir(stage, rid, root) / "harness" / "run.json") or {}
        total += (rec.get("tokens") or {}).get("counted", 0) + (rec.get("judge_tokens") or {}).get("counted", 0)
    return total


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m harness.stage", description=__doc__.split("\n\n")[0])
    ap.add_argument("plan")
    ap.add_argument("--parallel", type=int, help="runs at a time (default: plan's value, else 4)")
    ap.add_argument("--runs-root", help="default $FACTORY_RUNS_ROOT or ~/factory-runs")
    ap.add_argument("--limit-wait-min", type=float, default=15, help="pause after a limit with no reset time")
    ap.add_argument("--max-limit-retries", type=int, default=8)
    ap.add_argument("--poll-seconds", type=float, default=5)
    a = ap.parse_args(argv)
    plan = read_json(Path(a.plan))
    if not plan:
        ap.error(f"cannot read plan {a.plan}")
    stage = check_stage(plan["stage"])
    budget = int(plan["budget_tokens"])
    parallel = a.parallel or int(plan.get("parallel", 4))
    specs = [{**plan.get("defaults", {}), **r} for r in plan["runs"]]
    ids = [s["run_id"] for s in specs]
    if len(set(ids)) != len(ids):
        ap.error("run ids in the plan must be unique")
    sroot = runs_root(a.runs_root) / stage
    (sroot / "logs").mkdir(parents=True, exist_ok=True)

    def status(rid: str) -> str | None:
        return (read_json(run_dir(stage, rid, a.runs_root) / "harness" / "run.json") or {}).get("status")

    queue = [s for s in specs if status(s["run_id"]) not in (*FINAL, "harness_fault")]
    skipped = len(specs) - len(queue)
    print(f"stage {stage}: {len(specs)} runs, {skipped} already done or faulted, budget {budget:,} counted tokens")
    running: dict[str, subprocess.Popen] = {}
    retries: dict[str, int] = {}
    paused_until, halted, attention = 0.0, False, []
    while queue or running:
        for rid, proc in list(running.items()):
            if proc.poll() is None:
                continue
            del running[rid]
            rec = read_json(run_dir(stage, rid, a.runs_root) / "harness" / "run.json") or {}
            st = rec.get("status")
            if st == "plan_limit":
                retries[rid] = retries.get(rid, 0) + 1
                resets = rec.get("resets_at")
                paused_until = max(paused_until, resets + 30 if resets else time.time() + a.limit_wait_min * 60)
                if retries[rid] <= a.max_limit_retries:
                    queue.insert(0, next(s for s in specs if s["run_id"] == rid))
                    print(f"{rid}: plan or rate limit; pausing new starts until {time.ctime(paused_until)}")
                else:
                    attention.append(f"{rid}: still limited after {retries[rid]} tries")
            elif st in FINAL:
                print(f"{rid}: {st}, {rec.get('tokens', {}).get('counted', 0):,} counted tokens")
            else:
                attention.append(f"{rid}: {st or 'no record'} ({rec.get('reason') or f'exit {proc.returncode}'})")
                print(attention[-1])
                if "not logged in" in str(rec.get("reason")):
                    halted = True
                    print("HALT: the claude command is not logged in. No new runs will start.")
        total = counted(stage, ids, a.runs_root)
        if not halted and total >= HALT_AT * budget:
            halted = True
            print(
                f"HALT: stage {stage} has used {total:,} counted tokens, {total / budget:.0%} of its "
                f"{budget:,} budget. No new runs will start; {len(running)} running runs will finish. "
                f"{len(queue)} runs not started."
            )
        if halted:
            queue = []
        while queue and len(running) < parallel and time.time() >= paused_until:
            spec = queue.pop(0)
            rid = spec["run_id"]
            log = open(sroot / "logs" / f"{rid}.log", "a")
            running[rid] = subprocess.Popen(
                [sys.executable, "-m", "harness.run", *run_args(stage, spec, a.runs_root)],
                cwd=LAB_ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            print(f"{rid}: started")
        if queue or running:
            time.sleep(a.poll_seconds)
    total = counted(stage, ids, a.runs_root)
    summary = {
        "stage": stage,
        "budget_tokens": budget,
        "counted_tokens": total,
        "halted": halted,
        "runs": {rid: status(rid) for rid in ids},
        "attention": attention,
    }
    write_json(sroot / "stage.json", summary)
    print(f"stage {stage}: {total:,} counted tokens used of {budget:,}; summary in {sroot / 'stage.json'}")
    if halted:
        return 3
    return 1 if attention or any(v not in FINAL for v in summary["runs"].values()) else 0


if __name__ == "__main__":
    sys.exit(main())
