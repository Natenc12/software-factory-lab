"""Write the stage-1 plan files that `python -m harness.stage` runs.

    python -m grader.make_plan stage-1 [--codebase gct] [--best-process P3] [--tickets-root ...]
                                       [--answers-root ...] [--out-dir results/stage-1]

Stage 1 (gate 1): six arms on the eight tickets at S1, P0 on S0, S2 and S3 for the seven tickets that
are not the review ticket, and later the best process arm on S3 for the same seven. Three parts:

1. `meter`: each arm on T1 at S1, six runs. They go first; if they point past the budget, stop.
2. `wave1`: the rest of the first wave (42 arm runs on T2 to T8, and the 21 spec-level runs).
3. `wave2`: the best process arm on S3, seven runs, left to be filled in after the first wave is graded
   (`--best-process P3` fills it; `grader.summarize` names the arm).

Files written:
- `plan-meter.json`: the meter runs only. Run it first.
- `plan.json`: meter + wave 1 (+ wave 2 once filled). Finished runs are skipped, so running it after the
  meter is safe, and its token budget counts the meter runs too. `parts` lists the three parts.
- `sheets/<ticket>.md`: each ticket's reply sheet (common replies + the ticket's own), from build_sheet.

Run ids are `<arm>-<ticket>-<repeat>`, lowercase, with the spec level in the arm part for spec rows
(`p0s2-t3-1`, `p3s3-t1-1`). Every run uses Opus 5.5 at medium effort (Claude Code's default for it,
set explicitly so it cannot drift), and the reply judge is Opus 5.5.
"""

import argparse
import sys
from pathlib import Path

from grader.build_sheet import build as build_sheet
from grader.common import ANSWERS_ROOT, ARM_ORDER, LAB_ROOT, TICKETS_ROOT, now_iso, read_json, write_json

STAGE_BUDGET = 24_000_000
CEILINGS = {"P0": 400_000, "P1": 500_000, "P1R": 600_000, "P2": 700_000, "P3": 700_000, "P4": 1_600_000}
TICKETS = [f"T{i}" for i in range(1, 9)]
METER_TICKET = "T1"
SPEC_LEVELS = ("S0", "S2", "S3")
MODEL = "claude-opus-5-5"
REPLY_JUDGE = "claude-opus-5-5"
EFFORT = "medium"


def run_id(arm: str, ticket: str, spec: str = "S1", repeat: int = 1) -> str:
    part = arm.lower() + ("" if spec == "S1" else spec.lower())
    return f"{part}-{ticket.lower()}-{repeat}"


def arm_dir(arm: str, arms_root: Path) -> str | None:
    """The arm's folder relative to this repo, or None for the bare arm (P0 without its own folder)."""
    folder = arms_root / arm
    if folder.exists():
        try:
            return str(folder.relative_to(LAB_ROOT))
        except ValueError:
            return str(folder)
    return None


def plan_runs(codebase: str, tickets_root: Path, arms_root: Path, sheets: dict, best: str | None):
    problems = []
    metas = {}
    for t in TICKETS:
        meta = read_json(tickets_root / codebase / t / "meta.json")
        if not meta:
            problems.append(f"{t}: {tickets_root / codebase / t / 'meta.json'} missing")
        metas[t] = meta or {}
    for arm in ARM_ORDER:
        if arm != "P0" and arm_dir(arm, arms_root) is None:
            problems.append(f"arm {arm}: folder {arms_root / arm} missing")

    def spec_ok(t: str, spec: str) -> bool:
        meta = metas[t]
        return meta.get("deliverable", "pull_request") == "pull_request" or spec == "S1"

    def one(arm: str, t: str, spec: str) -> dict:
        meta = metas[t]
        base = meta.get("s3_base_ref") if spec == "S3" else meta.get("base_ref")
        if spec == "S3" and not base:
            problems.append(f"{t}: s3_base_ref missing for an S3 run")
        rel_ticket = tickets_root / codebase / t / f"{spec}.md"
        if not rel_ticket.is_file():
            problems.append(f"{t}: {rel_ticket} missing")
        try:
            ticket_path = str(rel_ticket.relative_to(LAB_ROOT))
        except ValueError:
            ticket_path = str(rel_ticket)
        spec_arm = arm_dir(arm, arms_root)
        r = {
            "run_id": run_id(arm, t, spec),
            "ticket": ticket_path,
            "base": base,
            "repo": meta.get("repo"),
            "db": meta.get("db"),
            "ceiling": CEILINGS[arm],
            "reply_sheet": sheets.get(t),
            "redact": [arm, arm.lower()],
        }
        if spec_arm:
            r["arm"] = spec_arm
        return r

    meter = [one(arm, METER_TICKET, "S1") for arm in ARM_ORDER]
    wave1 = [one(arm, t, "S1") for t in TICKETS if t != METER_TICKET for arm in ARM_ORDER]
    wave1 += [one("P0", t, spec) for spec in SPEC_LEVELS for t in TICKETS if spec_ok(t, spec)]
    if best:
        wave2 = [one(best, t, "S3") for t in TICKETS if spec_ok(t, "S3")]
    else:
        wave2 = [{"run_id": f"<best>s3-{t.lower()}-1", "to_fill": True} for t in TICKETS if spec_ok(t, "S3")]
    return meter, wave1, wave2, problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m grader.make_plan", description=__doc__.split("\n\n")[0])
    ap.add_argument("stage", choices=["stage-1"], help="only stage 1 is planned so far")
    ap.add_argument("--codebase", default="gct")
    ap.add_argument("--best-process", choices=["P1", "P1R", "P3", "P2", "P4"], help="fill wave 2 with this arm on S3")
    ap.add_argument("--tickets-root", default=str(TICKETS_ROOT))
    ap.add_argument("--answers-root", default=str(ANSWERS_ROOT))
    ap.add_argument("--arms-root", default=str(LAB_ROOT / "arms"))
    ap.add_argument("--out-dir", help="default results/<stage> in this repo")
    ap.add_argument("--force", action="store_true", help="write the plan even when tickets or arms are missing")
    a = ap.parse_args(argv)
    out_dir = Path(a.out_dir or LAB_ROOT / "results" / a.stage)
    tickets_root, answers_root = Path(a.tickets_root), Path(a.answers_root)

    sheets, problems = {}, []
    for t in TICKETS:
        path = out_dir / "sheets" / f"{a.codebase}-{t}.md"
        try:
            text = build_sheet(a.codebase, t, answers_root)
        except (OSError, ValueError) as e:
            problems.append(f"{t}: reply sheet: {e}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        try:
            sheets[t] = str(path.relative_to(LAB_ROOT))
        except ValueError:
            sheets[t] = str(path)
        if not (answers_root / a.codebase / t / "replies.md").is_file():
            problems.append(f"{t}: no replies.md; its sheet has only the common replies")

    meter, wave1, wave2, more = plan_runs(a.codebase, tickets_root, Path(a.arms_root), sheets, a.best_process)
    problems += more
    defaults = {"model": MODEL, "judge_model": REPLY_JUDGE, "effort": EFFORT}
    runnable = meter + wave1 + (wave2 if a.best_process else [])
    plan = {
        "stage": a.stage,
        "budget_tokens": STAGE_BUDGET,
        "parallel": 4,
        "written": now_iso(),
        "codebase": a.codebase,
        "defaults": defaults,
        "ceilings": CEILINGS,
        "parts": {
            "meter": [r["run_id"] for r in meter],
            "wave1": [r["run_id"] for r in wave1],
            "wave2": [r["run_id"] for r in wave2],
            "wave2_arm": a.best_process,
        },
        "runs": runnable,
        "problems": problems,
    }
    meter_plan = {**plan, "runs": meter, "parts": {"meter": plan["parts"]["meter"]}}
    if problems and not a.force:
        for p in problems:
            print(f"problem: {p}", file=sys.stderr)
        print(f"{len(problems)} problems; nothing written (use --force to write anyway)", file=sys.stderr)
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "plan-meter.json", meter_plan)
    write_json(out_dir / "plan.json", plan)
    print(
        f"wrote {out_dir / 'plan-meter.json'} ({len(meter)} runs) and {out_dir / 'plan.json'} "
        f"({len(runnable)} runs: meter {len(meter)}, wave 1 {len(wave1)}, wave 2 "
        f"{len(wave2) if a.best_process else f'{len(wave2)} to fill'}); budget {STAGE_BUDGET:,} counted tokens"
        + (f"; {len(problems)} problems" if problems else "")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
