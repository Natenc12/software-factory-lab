"""second_pick.py <stage folder> [--model M]: a second, blind reply pick for every stop of every run.

Same prompt and same reply sheet as the harness's reply judge, a different judge model. Writes
<stage folder>/.second-pick/<run>.jsonl; changes nothing in any run's own records. Skips stops done.
"""

import argparse
import json
import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path.home() / "repos/software-factory-lab"))
from harness import owner  # noqa: E402


def stops_of(run: Path):
    log = run / "harness" / "owner-log.jsonl"
    if not log.is_file():
        return []
    return [json.loads(line) for line in log.read_text().splitlines() if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage")
    ap.add_argument("--model", default="claude-fable-5-2")
    a = ap.parse_args()
    stage = Path(a.stage)
    out_dir = stage / ".second-pick"
    out_dir.mkdir(exist_ok=True)
    room = Path(tempfile.mkdtemp(prefix="second-pick-"))
    env = {k: v for k, v in os.environ.items() if k not in ("LAB_DB", "DATABASE_URL")}
    jobs = []
    for run in sorted(p for p in stage.iterdir() if (p / "harness" / "run.json").is_file()):
        rec = json.loads((run / "harness" / "run.json").read_text())
        out = out_dir / f"{run.name}.jsonl"
        done = {json.loads(x)["stop"] for x in out.read_text().splitlines()} if out.is_file() else set()
        for s in stops_of(run):
            if s["stop"] not in done:
                jobs.append((run, rec, s, out))

    def one(job):
        run, rec, s, out = job
        sheet = owner.parse_sheet(Path(rec["reply_sheet"]))
        hdir = run / "harness"
        q = (hdir / "stops" / f"{s['stop']}-question.txt").read_text().rstrip("\n")
        page = None
        if s.get("page_file"):
            page = (hdir / s["page_file"]).read_text().rstrip("\n")
        got = owner.ask_judge(
            "claude", a.model, owner.judge_prompt(sheet, q, page), [r["id"] for r in sheet], room, env
        )
        reply = next(r for r in sheet if r["id"] == got["id"])
        row = {
            "run": run.name,
            "stop": s["stop"],
            "first_id": s["reply_id"],
            "first_rescue": bool(s.get("rescue")),
            "first_model": s.get("judge_model"),
            "second_id": got["id"],
            "second_rescue": bool(reply.get("rescue")),
            "second_model": a.model,
            "second_fallback": got["fallback"],
            "second_answers": got["answers"],
        }
        with open(out, "a") as f:
            f.write(json.dumps(row) + "\n")
        return row

    with ThreadPoolExecutor(4) as pool:
        rows = list(pool.map(one, jobs))
    same = sum(r["first_id"] == r["second_id"] for r in rows)
    print(
        f"{len(rows)} stops re-picked; same id {same}; rescue flag differs {sum(r['first_rescue'] != r['second_rescue'] for r in rows)}"
    )
    for r in rows:
        if r["first_id"] != r["second_id"]:
            print(
                f"  {r['run']} stop {r['stop']}: {r['first_id']} (rescue {r['first_rescue']}) vs {r['second_id']} (rescue {r['second_rescue']})"
            )


if __name__ == "__main__":
    main()
