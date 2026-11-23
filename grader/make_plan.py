"""Write the plan files that `python -m harness.stage` runs.

    python -m grader.make_plan stage-1 [--codebase gct] [--best-process P3] [--tickets-root ...]
                                       [--answers-root ...] [--out-dir results/stage-1]
    python -m grader.make_plan stage-2 [--ticket-ceiling T9=900000 ...] [--budget N] [--out-dir ...]

Stage 4 (`make_plan stage-4 --codebase hono|sqlglot`, gate 5): rows P5P (arms/P5P on Opus 5.5, run
ids p5p-...), P5PF (arms/P5P on Fable 5.2, p5pf-...) and P6 (arms/P6, lead on Fable 5.2, p6-...), on the
codebase's eight tickets at S1, repeats 1 and 2: 48 runs into results/stage-4-<codebase>/, stage folder
stage-4-<codebase>, the model set per run. Ceilings: P1's for P5P and P5PF, 1.2M for P6;
`--row-ceiling P6=...` sets a row's ceiling, `--ticket-ceiling` raises every row on a ticket (never lowers).

Stage 2b (`make_plan stage-2b`, same options): on the same eight tickets, repeat 3 of P5P and of P1A
(16 runs) and repeats 1 and 2 of P5PA, the pointed skills plus the architecture brief (16 runs).

Stage 2 (gate 3): the five add-on arms P1T, P1L, P1A, P5 and P5P on T2, T5, T6, T7, T9, T10, T11 and
T12 at S1, repeats 1 and 2 (80 runs), plus P1 on T9 to T12, repeats 1 and 2 (8 runs; P1's runs on the
other four come from stage 1 and the confirm round). Ceilings are P1's for every add-on;
`--ticket-ceiling` sets one ticket's ceiling for every arm on it, P1 included. Writes `plan.json` and
`sheets/`, and nothing at all if a ticket, its answers or an arm folder is missing.

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
from grader.common import (
    ADDON_ARMS,
    ANSWERS_ROOT,
    ARM_ORDER,
    LAB_ROOT,
    STAGE2_TICKETS,
    STAGE2B_ARMS,
    STAGE4_ROWS,
    TICKETS_ROOT,
    load_config,
    now_iso,
    read_json,
    write_json,
)

STAGE_BUDGET = 24_000_000
CEILINGS = {"P0": 400_000, "P1": 500_000, "P1R": 600_000, "P2": 700_000, "P3": 700_000, "P4": 1_600_000}
CEILINGS.update({arm: CEILINGS["P1"] for arm in ADDON_ARMS})  # stage 2: the same as P1 (gate 3)
STAGE2_P1_TICKETS = ["T9", "T10", "T11", "T12"]  # P1 has three runs of the others from stage 1 and the confirm round
STAGE2_REPEATS = (1, 2)
CEILINGS.update({arm: CEILINGS["P1"] for arm in STAGE2B_ARMS})  # stage 2b: the same as P1
# Each round on the stage 2 tickets: its parts (name, arms, tickets, repeats) and the arms it needs.
ROUNDS = {
    "stage-2": {
        "parts": [
            ("addons", ADDON_ARMS, STAGE2_TICKETS, STAGE2_REPEATS),
            ("p1", ["P1"], STAGE2_P1_TICKETS, STAGE2_REPEATS),
        ],
        "arms": ["P1", *ADDON_ARMS],
    },
    "stage-2b": {
        "parts": [("repeat3", ["P5P", "P1A"], STAGE2_TICKETS, (3,)), ("p5pa", ["P5PA"], STAGE2_TICKETS, (1, 2))],
        "arms": ["P5P", "P1A", "P5PA"],
    },
}
TICKETS = [f"T{i}" for i in range(1, 9)]
STAGE4_CEILINGS = {"P5P": CEILINGS["P1"], "P5PF": CEILINGS["P1"], "P6": 1_200_000}
STAGE4_REPEATS = (1, 2)
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


def codebase_run_extras(codebase: str) -> dict:
    """What a codebase's config adds to every run of it, as run-plan keys.

    `run_env` -> `env` (KEY=VALUE), `run_allow_domains` -> `allow_domain` (hosts the run's sandbox may
    reach beyond PyPI), `run_allow_write` -> `allow_write` (folders outside the run, such as a
    toolchain's cache, the sandbox may write), `run_setup` -> `setup` (shell commands the harness runs in
    the checkout before the session, with network, such as installing dependencies). A codebase without
    them adds nothing.
    """
    try:
        cfg = load_config(codebase)
    except SystemExit:
        return {}
    out = {}
    if cfg.get("run_env"):
        out["env"] = [f"{k}={v}" for k, v in sorted(cfg["run_env"].items())]
    if cfg.get("run_allow_domains"):
        out["allow_domain"] = list(cfg["run_allow_domains"])
    if cfg.get("run_allow_write"):
        out["allow_write"] = list(cfg["run_allow_write"])
    if cfg.get("run_setup"):
        out["setup"] = list(cfg["run_setup"])
    return out


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

    extras = codebase_run_extras(codebase)

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
        r.update(extras)
        return r

    meter = [one(arm, METER_TICKET, "S1") for arm in ARM_ORDER]
    wave1 = [one(arm, t, "S1") for t in TICKETS if t != METER_TICKET for arm in ARM_ORDER]
    wave1 += [one("P0", t, spec) for spec in SPEC_LEVELS for t in TICKETS if spec_ok(t, spec)]
    if best:
        wave2 = [one(best, t, "S3") for t in TICKETS if spec_ok(t, "S3")]
    else:
        wave2 = [{"run_id": f"<best>s3-{t.lower()}-1", "to_fill": True} for t in TICKETS if spec_ok(t, "S3")]
    return meter, wave1, wave2, problems


def parse_ticket_ceilings(items) -> dict[str, int]:
    out = {}
    for item in items or []:
        t, _, n = item.partition("=")
        if not t.strip().upper().startswith("T") or not n.strip().isdigit():
            raise SystemExit(f"--ticket-ceiling wants T<n>=<tokens>, got {item!r}")
        out[t.strip().upper()] = int(n)
    return out


def write_sheets(codebase: str, tickets, answers_root: Path, out_dir: Path) -> tuple[dict, dict, list[str]]:
    """Each ticket's reply sheet text and the path it will be written to; nothing is written here."""
    texts, paths, problems = {}, {}, []
    for t in tickets:
        path = out_dir / "sheets" / f"{codebase}-{t}.md"
        try:
            texts[t] = build_sheet(codebase, t, answers_root)
        except (OSError, ValueError) as e:
            problems.append(f"{t}: reply sheet: {e}")
            continue
        try:
            paths[t] = str(path.relative_to(LAB_ROOT))
        except ValueError:
            paths[t] = str(path)
        if not (answers_root / codebase / t / "replies.md").is_file():
            problems.append(f"{t}: no replies.md; its sheet has only the common replies")
    return texts, paths, problems


def plan_stage2(a) -> int:
    """A round on the eight stage 2 tickets at S1: stage 2 (gate 3) or stage 2b. See ROUNDS."""
    rnd = ROUNDS[a.stage]
    out_dir = Path(a.out_dir or LAB_ROOT / "results" / a.stage)
    tickets_root, answers_root, arms_root = Path(a.tickets_root), Path(a.answers_root), Path(a.arms_root)
    overrides = parse_ticket_ceilings(a.ticket_ceiling)
    texts, sheets, problems = write_sheets(a.codebase, STAGE2_TICKETS, answers_root, out_dir)
    metas = {}
    for t in STAGE2_TICKETS:
        meta = read_json(tickets_root / a.codebase / t / "meta.json")
        if not meta:
            problems.append(f"{t}: {tickets_root / a.codebase / t / 'meta.json'} missing")
        if not (tickets_root / a.codebase / t / "S1.md").is_file():
            problems.append(f"{t}: {tickets_root / a.codebase / t / 'S1.md'} missing")
        for need in ("key.json", "reference.patch"):
            if not (answers_root / a.codebase / t / need).is_file():
                problems.append(f"{t}: answers: {answers_root / a.codebase / t / need} missing")
        metas[t] = meta or {}
    for arm in rnd["arms"]:
        if arm_dir(arm, arms_root) is None:
            problems.append(f"arm {arm}: folder {arms_root / arm} missing")
    extras = codebase_run_extras(a.codebase)
    unknown = sorted(set(overrides) - set(STAGE2_TICKETS))
    if unknown:
        problems.append(f"--ticket-ceiling names tickets not on the stage 2 plan: {unknown}")

    def one(arm: str, t: str, repeat: int) -> dict:
        meta = metas[t]
        ticket = tickets_root / a.codebase / t / "S1.md"
        try:
            ticket_path = str(ticket.relative_to(LAB_ROOT))
        except ValueError:
            ticket_path = str(ticket)
        r = {
            "run_id": run_id(arm, t, "S1", repeat),
            "ticket": ticket_path,
            "base": meta.get("base_ref"),
            "repo": meta.get("repo"),
            "db": meta.get("db"),
            "ceiling": overrides.get(t, CEILINGS[arm]),
            "reply_sheet": sheets.get(t),
            "redact": [arm, arm.lower()],
        }
        r.update(extras)
        if arm_dir(arm, arms_root):
            r["arm"] = arm_dir(arm, arms_root)
        return r

    parts = {
        name: [one(arm, t, n) for n in repeats for t in tickets for arm in arms]
        for name, arms, tickets, repeats in rnd["parts"]
    }
    if problems and not a.force:
        for p in problems:
            print(f"problem: {p}", file=sys.stderr)
        print(f"{len(problems)} problems; nothing written (use --force to write anyway)", file=sys.stderr)
        return 1
    for t, text in texts.items():
        path = out_dir / "sheets" / f"{a.codebase}-{t}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    plan = {
        "stage": a.stage,
        "budget_tokens": a.budget or STAGE_BUDGET,
        "parallel": 4,
        "written": now_iso(),
        "codebase": a.codebase,
        "defaults": {"model": MODEL, "judge_model": REPLY_JUDGE, "effort": EFFORT},
        "ceilings": {arm: CEILINGS[arm] for arm in rnd["arms"]},
        "ticket_ceilings": overrides,
        "tickets": STAGE2_TICKETS,
        "repeats": sorted({n for *_, repeats in rnd["parts"] for n in repeats}),
        "parts": {name: [r["run_id"] for r in runs] for name, runs in parts.items()},
        "runs": [r for runs in parts.values() for r in runs],
        "problems": problems,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "plan.json", plan)
    print(
        f"wrote {out_dir / 'plan.json'} ({len(plan['runs'])} runs: "
        + ", ".join(f"{name} {len(runs)}" for name, runs in parts.items())
        + "); "
        f"ticket ceilings {overrides or 'none'}" + (f"; {len(problems)} problems" if problems else "")
    )
    return 0


def plan_stage4(a) -> int:
    """Stage 4 (gate 5): three rows on one codebase's eight tickets at S1, repeats 1 and 2 (48 runs)."""
    stage = f"stage-4-{a.codebase}"
    out_dir = Path(a.out_dir or LAB_ROOT / "results" / stage)
    tickets_root, answers_root, arms_root = Path(a.tickets_root), Path(a.answers_root), Path(a.arms_root)
    overrides = parse_ticket_ceilings(a.ticket_ceiling)
    rows = dict(STAGE4_CEILINGS)
    for item in a.row_ceiling or []:
        row, _, n = item.partition("=")
        if row.strip().upper() not in STAGE4_ROWS or not n.strip().isdigit():
            raise SystemExit(f"--row-ceiling wants <row>=<tokens> with a row of {', '.join(STAGE4_ROWS)}, got {item!r}")
        rows[row.strip().upper()] = int(n)
    texts, sheets, problems = write_sheets(a.codebase, TICKETS, answers_root, out_dir)
    metas = {}
    for t in TICKETS:
        meta = read_json(tickets_root / a.codebase / t / "meta.json")
        if not meta:
            problems.append(f"{t}: {tickets_root / a.codebase / t / 'meta.json'} missing")
        if not (tickets_root / a.codebase / t / "S1.md").is_file():
            problems.append(f"{t}: {tickets_root / a.codebase / t / 'S1.md'} missing")
        for need in ("key.json", "reference.patch"):
            if not (answers_root / a.codebase / t / need).is_file():
                problems.append(f"{t}: answers: {answers_root / a.codebase / t / need} missing")
        metas[t] = meta or {}
    for folder in sorted({arm for arm, _ in STAGE4_ROWS.values()}):
        if arm_dir(folder, arms_root) is None:
            problems.append(f"arm {folder}: folder {arms_root / folder} missing")
    unknown = sorted(set(overrides) - set(TICKETS))
    if unknown:
        problems.append(f"--ticket-ceiling names tickets not on the stage 4 plan: {unknown}")
    extras = codebase_run_extras(a.codebase)

    def one(row: str, t: str, repeat: int) -> dict:
        folder, model = STAGE4_ROWS[row]
        meta = metas[t]
        ticket = tickets_root / a.codebase / t / "S1.md"
        try:
            ticket_path = str(ticket.relative_to(LAB_ROOT))
        except ValueError:
            ticket_path = str(ticket)
        r = {
            "run_id": run_id(row, t, "S1", repeat),
            "ticket": ticket_path,
            "base": meta.get("base_ref"),
            "repo": meta.get("repo"),
            "db": meta.get("db"),
            "model": model,
            # A ticket's override raises every row on it, but never lowers a row's own ceiling.
            "ceiling": max(rows[row], overrides.get(t, 0)),
            "reply_sheet": sheets.get(t),
            "redact": sorted({row, row.lower(), folder, folder.lower()}),
        }
        r.update(extras)
        if arm_dir(folder, arms_root):
            r["arm"] = arm_dir(folder, arms_root)
        return r

    runs = [one(row, t, n) for n in STAGE4_REPEATS for t in TICKETS for row in STAGE4_ROWS]
    if problems and not a.force:
        for p in problems:
            print(f"problem: {p}", file=sys.stderr)
        print(f"{len(problems)} problems; nothing written (use --force to write anyway)", file=sys.stderr)
        return 1
    for t, text in texts.items():
        path = out_dir / "sheets" / f"{a.codebase}-{t}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    plan = {
        "stage": stage,
        "budget_tokens": a.budget or STAGE_BUDGET,
        "parallel": 4,
        "written": now_iso(),
        "codebase": a.codebase,
        "defaults": {"judge_model": REPLY_JUDGE, "effort": EFFORT},
        "rows": {
            row: {"arm": folder, "model": model, "ceiling": rows[row]} for row, (folder, model) in STAGE4_ROWS.items()
        },
        "ticket_ceilings": overrides,
        "tickets": TICKETS,
        "repeats": list(STAGE4_REPEATS),
        "parts": {row: [r["run_id"] for r in runs if r["run_id"].startswith(row.lower() + "-")] for row in STAGE4_ROWS},
        "runs": runs,
        "problems": problems,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "plan.json", plan)
    print(f"wrote {out_dir / 'plan.json'} ({len(runs)} runs, stage folder {stage}); ceilings "
          f"{ {r: x['ceiling'] for r, x in plan['rows'].items()} }; ticket ceilings {overrides or 'none'}")  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m grader.make_plan", description=__doc__.split("\n\n")[0])
    ap.add_argument("stage", choices=["stage-1", "stage-2", "stage-2b", "stage-4"])
    ap.add_argument("--codebase", default="gct")
    ap.add_argument("--best-process", choices=["P1", "P1R", "P3", "P2", "P4"], help="fill wave 2 with this arm on S3")
    ap.add_argument("--tickets-root", default=str(TICKETS_ROOT))
    ap.add_argument("--answers-root", default=str(ANSWERS_ROOT))
    ap.add_argument("--arms-root", default=str(LAB_ROOT / "arms"))
    ap.add_argument("--out-dir", help="default results/<stage> in this repo")
    ap.add_argument("--force", action="store_true", help="write the plan even when tickets or arms are missing")
    ap.add_argument("--ticket-ceiling", action="append", default=[], metavar="T9=900000",
                    help="stage 2 and 2b: ceiling for every arm on that ticket (repeatable)")  # fmt: skip
    ap.add_argument("--budget", type=int, help="stage 2: the stage's token figure (default 24,000,000)")
    ap.add_argument("--row-ceiling", action="append", default=[], metavar="P6=1500000",
                    help="stage 4: ceiling for one row (P5P, P5PF, P6) on every ticket (repeatable)")  # fmt: skip
    a = ap.parse_args(argv)
    if a.stage == "stage-4":
        if a.best_process:
            ap.error("--best-process is for stage 1")
        if a.codebase in ("gct", "pipeline-lab"):
            ap.error("stage 4 runs on the new codebases: pass --codebase hono or --codebase sqlglot")
        try:
            return plan_stage4(a)
        except SystemExit as e:
            print(str(e), file=sys.stderr)
            return 2
    if a.row_ceiling:
        ap.error("--row-ceiling is for stage 4")
    if a.stage in ROUNDS:
        if a.best_process:
            ap.error("--best-process is for stage 1")
        try:
            return plan_stage2(a)
        except SystemExit as e:
            print(str(e), file=sys.stderr)
            return 2
    if a.ticket_ceiling or a.budget:
        ap.error("--ticket-ceiling and --budget are for stage 2 and 2b")
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
        "ceilings": {arm: CEILINGS[arm] for arm in ARM_ORDER},
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
