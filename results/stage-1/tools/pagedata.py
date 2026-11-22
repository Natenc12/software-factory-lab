"""pagedata.py <runs stage folder> <out.json>: one flat record per run, straight from verdict.json and the judge files."""

import json
import sys
from pathlib import Path

stage, out = Path(sys.argv[1]), Path(sys.argv[2])
rows = []
for run in sorted(p for p in stage.iterdir() if (p / "harness" / "verdict.json").is_file()):
    h = run / "harness"
    v = json.loads((h / "verdict.json").read_text())
    m = v.get("measures") or {}
    c = v.get("checks") or {}
    g = json.loads((h / "grade.json").read_text()) if (h / "grade.json").is_file() else {}
    row = {
        "run": run.name,
        "arm": v["arm"],
        "spec": v["spec"],
        "ticket": v["ticket"],
        "row": v["row"],
        "status": v["status"],
        "trustworthy": v["trustworthy"],
        "discarded": v.get("discarded"),
        "deliverable": v.get("deliverable"),
        "failed_checks": [k for k, x in c.items() if not x["pass"]],
        "hidden": (c.get("hidden_tests_pass") or {}).get("detail"),
        "traps": ((c.get("no_trap_tripped") or {}).get("detail") or {}).get("tripped"),
        "false_claims": (c.get("no_false_claim") or {}).get("detail"),
        "review": {k: c[k]["detail"] for k in ("all_planted_bugs_caught", "no_false_blocking_alarm") if k in c},
        "rescues": m.get("rescues"),
        "stops": m.get("stops"),
        "stops_total": m.get("stops_total"),
        "stops_routine": m.get("stops_routine"),
        "stops_warranted": m.get("stops_warranted"),
        "correction_rounds": m.get("correction_rounds"),
        "attention_words": m.get("attention_words"),
        "attention_detail": m.get("attention_detail"),
        "counted_tokens": m.get("counted_tokens"),
        "list_price_usd": m.get("list_price_usd"),
        "judge_tokens": m.get("grading_judge_tokens"),
        "judge_usd": m.get("grading_judge_list_price_usd"),
        "reply_judge_tokens": m.get("reply_judge_tokens"),
        "wall_seconds": m.get("wall_seconds"),
        "quality": m.get("quality"),
        "judgement": m.get("judgement"),
        "merge_decidable": m.get("merge_decidable_from_brief"),
        "behaviour_tags": m.get("behaviour_tags"),
        "pr": (g.get("pull_request") or {}).get("number"),
        "pr_checks": (g.get("pull_request") or {}).get("checks_summary"),
        "files_changed": len(g.get("files_changed") or []),
    }
    rows.append(row)
out.write_text(json.dumps(rows, indent=1))
print(len(rows), "runs ->", out)
