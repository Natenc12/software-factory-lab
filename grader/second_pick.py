"""A second, blind reply pick for every owner stop of a run, by a different judge model.

    python -m grader.second_pick <run folder> [--model M] [--sheet S] [--claude claude]
    python -m grader.second_pick <run folder> --import results/stage-1/second-reply-picks.jsonl

For each stop in harness/owner-log.jsonl, the same prompt the harness's reply judge got (the stripped
question and page saved in harness/stops/, the run's own reply sheet) goes to another judge model:
claude-fable-5-2 when the first was claude-opus-5-5, and the reverse. Writes harness/second-picks.json;
changes no other file. Stops already picked by the same model are kept, so it is safe to re-run.
`--import` writes the same file from rows of the stage-1 sketch (`results/stage-1/tools/second_pick.py`)
without calling a model.

Second reading (gate 2): a rescue counts only if the first and the second pick both carry the rescue flag.
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from grader.common import now_iso, read_json, run_folder_info, write_json
from grader.verdict import owner_log, sheet_rescues
from harness import owner
from harness.stream import Usage

SWAP = {"claude-opus-5-5": "claude-fable-5-2", "claude-fable-5-2": "claude-opus-5-5"}


def other_model(first: str | None) -> str:
    return SWAP.get(first or "", "claude-fable-5-2")


def judge_env() -> dict:
    from grader.judge import judge_env as env

    return env()


def first_rescue(rec: dict, flags: dict) -> bool:
    return bool(rec["rescue"]) if "rescue" in rec else bool(flags.get(rec.get("reply_id"), False))


def pick_run(folder: Path, model: str | None = None, sheet: str | None = None, claude: str = "claude") -> dict:
    info = run_folder_info(folder)
    hdir, run = info["hdir"], info["run"]
    log = owner_log(hdir)
    first_model = next((r.get("judge_model") for r in log if r.get("judge_model")), run.get("judge_model"))
    model = model or other_model(first_model)
    out_path = hdir / "second-picks.json"
    old = read_json(out_path) or {}
    kept = {p["stop"]: p for p in old.get("picks") or []} if old.get("model") == model else {}
    out = {"run_id": run["run_id"], "model": model, "first_model": first_model, "time": now_iso(), "picks": []}
    usage, cost = Usage.from_dict(old.get("usage") if kept else None), float(old.get("cost_usd") or 0) if kept else 0.0
    todo = [r for r in log if r.get("stop") not in kept]
    replies = None
    if todo:
        path = Path(sheet or run.get("reply_sheet") or "")
        if not path.is_file():
            raise SystemExit(f"reply sheet {path} not found; pass --sheet")
        replies = owner.parse_sheet(path)
        out["sheet"] = str(path)
    flags = {r["id"]: r["rescue"] for r in replies} if replies else sheet_rescues(run)
    with tempfile.TemporaryDirectory(prefix="second-pick-") as room:
        for rec in log:
            n = rec.get("stop")
            if n in kept:
                out["picks"].append(kept[n])
                continue
            qfile = hdir / "stops" / f"{n}-question.txt"
            question = qfile.read_text(encoding="utf-8").rstrip("\n") if qfile.is_file() else rec.get("question", "")
            page = None
            if rec.get("page_file") and (hdir / rec["page_file"]).is_file():
                page = (hdir / rec["page_file"]).read_text(encoding="utf-8").rstrip("\n")
            ids = [r["id"] for r in replies]
            got = owner.ask_judge(
                claude, model, owner.judge_prompt(replies, question, page), ids, Path(room), judge_env()
            )
            usage, cost = usage + got["usage"], cost + got["cost_usd"]
            second = next(r for r in replies if r["id"] == got["id"])
            out["picks"].append(
                {
                    "stop": n,
                    "first_id": rec.get("reply_id"),
                    "first_rescue": first_rescue(rec, flags),
                    "second_id": second["id"],
                    "second_rescue": bool(second.get("rescue")),
                    "second_fallback": got["fallback"],
                    "second_answers": got["answers"],
                }
            )
    out.update(summary(out["picks"]), usage=usage.as_dict(), cost_usd=round(cost, 6))
    return out


def summary(picks: list[dict]) -> dict:
    return {
        "stops": len(picks),
        "same_reply": sum(p["first_id"] == p["second_id"] for p in picks),
        "rescue_flag_differs": [p["stop"] for p in picks if p["first_rescue"] != p["second_rescue"]],
        "agreed_rescues": [p["stop"] for p in picks if p["first_rescue"] and p["second_rescue"]],
    }


def import_rows(folder: Path, jsonl: Path) -> dict:
    """second-picks.json from the stage-1 sketch's rows for this run (no model call)."""
    info = run_folder_info(folder)
    rid = info["run"]["run_id"]
    rows = [json.loads(x) for x in jsonl.read_text(encoding="utf-8").splitlines() if x.strip()]
    rows = sorted((r for r in rows if r.get("run") == rid), key=lambda r: r["stop"])
    log = owner_log(info["hdir"])
    if sorted(r["stop"] for r in rows) != sorted(r.get("stop") for r in log):
        raise SystemExit(f"{jsonl} does not cover every stop of {rid}: rows {[r['stop'] for r in rows]}")
    keys = ("stop", "first_id", "first_rescue", "second_id", "second_rescue", "second_fallback", "second_answers")
    picks = [{k: r.get(k) for k in keys} for r in rows]
    models = {r.get("second_model") for r in rows} or {None}
    out = {"run_id": rid, "model": models.pop() if len(models) == 1 else None, "time": now_iso(),
           "first_model": next((r.get("first_model") for r in rows), None), "imported_from": str(jsonl), "picks": picks}  # fmt: skip
    out.update(summary(picks), usage=Usage().as_dict(), cost_usd=0.0)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m grader.second_pick", description=__doc__.split("\n\n")[0])
    ap.add_argument("run_folder")
    ap.add_argument("--model", help="default: the other of claude-opus-5-5 and claude-fable-5-2")
    ap.add_argument("--sheet", help="reply sheet (default: the one in run.json)")
    ap.add_argument("--claude", default=os.environ.get("GRADER_CLAUDE", "claude"))
    ap.add_argument("--import", dest="import_from", help="write the file from the stage-1 sketch's JSONL rows")
    a = ap.parse_args(argv)
    try:
        if a.import_from:
            out = import_rows(Path(a.run_folder), Path(a.import_from))
        else:
            out = pick_run(Path(a.run_folder), a.model, a.sheet, shutil.which(a.claude) or a.claude)
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 2
    path = Path(a.run_folder).resolve() / "harness" / "second-picks.json"
    write_json(path, out)
    print(
        f"{out['run_id']}: {out['stops']} stops, same reply {out['same_reply']}, rescue flag differs at "
        f"{out['rescue_flag_differs']}, agreed rescues {out['agreed_rescues']}; wrote {path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
