"""Summarise a stage: every run's verdict.json into results/<stage>/summary.json and summary.csv.

    python -m grader.summarize <stage> [--runs-root ~/factory-runs] [--out-dir results/<stage>]

One row per run, totals per row of the plan (an arm on S1 is its own name, `P0`; a spec-level row is
`P0/S2`), and the charter's decision rules applied literally:

- Leader: the most trustworthy pull requests per 8 tickets among the S1 arms. Arms within one of the
  leader (difference of 1.0 or less) are tied; a tie goes to the simpler arm (P0, P1, P1R, P3, P2, P4),
  then fewer owner stops, then lower cost.
- Best process arm: the same rule among P1, P1R, P3, P2, P4. It is the arm the second wave runs on S3.
- Q1, process needed: only if the best process arm beats P0 by more than one per 8, or P0 needs more
  rescues (per 8 graded runs).
- Q6, full spec replaces the pipeline: only if P0 on S2 or S3 comes within one per 8 of the best process
  arm on S1, and its owner attention (spec words included) is no higher. Compared on the tickets both
  have graded runs for (the spec rows skip the review ticket).
- Drop at stage 1: only an S1 arm that trails the leader by 3 or more per 8.

Discarded and incomplete runs are left out of the per-8 rates and listed. Stage 1 is labelled
provisional (plan page, change 1).
"""

import argparse
import csv
import sys
from pathlib import Path

from grader.common import ARM_ORDER, LAB_ROOT, PROCESS_ARMS, now_iso, read_json, write_json
from harness.common import runs_root

QUALITY = ("architecture_fit", "readability", "tests_meaningful")


def load_verdicts(stage: str, root: str | None = None) -> list[dict]:
    base = runs_root(root) / stage
    out = []
    for p in sorted(base.glob("*/harness/verdict.json")):
        v = read_json(p)
        if v:
            out.append(v)
    return out


def per8(n: int, graded: int) -> float | None:
    return round(8 * n / graded, 3) if graded else None


def totals(rows: list[dict], tickets: set[str] | None = None) -> dict:
    if tickets is not None:
        rows = [v for v in rows if v["ticket"] in tickets]
    graded = [v for v in rows if v.get("trustworthy") is not None]
    trusted = sum(1 for v in graded if v["trustworthy"])
    m = [v.get("measures") or {} for v in graded]

    def s(key):
        return sum((x.get(key) or 0) for x in m)

    def avg(key):
        vals = [x.get(key) for x in m if isinstance(x.get(key), int | float)]
        return round(sum(vals) / len(vals), 3) if vals else None

    quality = {}
    for d in QUALITY:
        vals = [x["quality"][d] for x in m if x.get("quality") and isinstance(x["quality"].get(d), int)]
        quality[d] = round(sum(vals) / len(vals), 3) if vals else None
    judged = [x["judgement"] for x in m if x.get("judgement")]
    comparable = [j for j in judged if j["preferred"] != "not comparable"]
    silent = [
        j["silent_consequential_decisions"] for j in judged if j.get("silent_consequential_decisions") is not None
    ]
    judgement = {
        "judged": len(judged),
        "not_comparable": len(judged) - len(comparable),
        "run_preferred": sum(j["preferred"] == "run" for j in comparable),
        "no_real_difference": sum(j["preferred"] == "no real difference" for j in comparable),
        "reference_preferred": sum(j["preferred"] == "reference" for j in comparable),
        "preferred_or_level_share": round(
            sum(j["preferred"] in ("run", "no real difference") for j in comparable) / len(comparable), 3
        )
        if comparable
        else None,
        "poor_share": {
            a: round(sum((j.get("run") or {}).get(a) == "poor" for j in judged) / len(judged), 3) if judged else None
            for a in ("fits_the_codebase", "cost_later", "proportion")
        },
        "silent_consequential_per_run": round(sum(silent) / len(silent), 3) if silent else None,
    }
    tags: dict[str, int] = {}
    for x in m:
        for t in x.get("behaviour_tags") or []:
            name = t.get("tag") + (f":{t['side']}" if t.get("side") else "")
            tags[name] = tags.get(name, 0) + 1
    return {
        "runs": len(rows),
        "graded": len(graded),
        "tickets_graded": sorted({v["ticket"] for v in graded}),
        "trustworthy": trusted,
        "trustworthy_per_8": per8(trusted, len(graded)),
        "discarded": [v["run_id"] for v in rows if v.get("discarded")],
        "incomplete": [v["run_id"] for v in rows if v.get("outcome") == "incomplete"],
        "ceiling_hit": sum(1 for v in rows if v.get("status") == "ceiling_hit"),
        "stops_total": s("stops_total"),
        "stops_routine": s("stops_routine"),
        "stops_warranted": s("stops_warranted"),
        "stops_avg": avg("stops_total"),
        "rescues": s("rescues"),
        "rescues_per_8": per8(s("rescues"), len(graded)),
        "correction_rounds": s("correction_rounds"),
        "attention_words_avg": avg("attention_words"),
        "counted_tokens": s("counted_tokens"),
        "counted_tokens_avg": avg("counted_tokens"),
        "list_price_usd": round(sum(float(x.get("list_price_usd") or 0) for x in m), 4),
        "list_price_usd_avg": avg("list_price_usd"),
        "wall_seconds": round(sum(float(x.get("wall_seconds") or 0) for x in m), 1),
        "quality_avg": quality,
        "merge_decidable_yes": sum(1 for x in m if x.get("merge_decidable_from_brief") == "yes"),
        "behaviour_tags": dict(sorted(tags.items())),
        "judgement": judgement,
    }


def tie_key(name: str, t: dict) -> tuple:
    rank = ARM_ORDER.index(name) if name in ARM_ORDER else len(ARM_ORDER)
    return (rank, t["stops_avg"] if t["stops_avg"] is not None else 1e9, t["list_price_usd_avg"] or 1e9)


def pick(candidates: dict[str, dict]) -> dict | None:
    """The leader by trustworthy per 8, and the arm the tie rule picks among those within one of it."""
    scored = {k: t for k, t in candidates.items() if t["trustworthy_per_8"] is not None}
    if not scored:
        return None
    top = max(t["trustworthy_per_8"] for t in scored.values())
    leaders = sorted(k for k, t in scored.items() if t["trustworthy_per_8"] == top)
    tied = sorted(
        (k for k, t in scored.items() if top - t["trustworthy_per_8"] <= 1.0), key=lambda k: tie_key(k, scored[k])
    )
    return {"top_score": top, "highest": leaders, "tied_within_one": tied, "pick": tied[0]}


def decide(by_row: dict[str, dict], verdicts: list[dict]) -> dict:
    s1 = {k: t for k, t in by_row.items() if k in ARM_ORDER}
    out: dict = {"rules_applied_literally": True}
    leader = pick(s1)
    out["leader"] = leader
    if leader:
        out["winner"] = leader["pick"]
        out["dropped"] = sorted(
            k
            for k, t in s1.items()
            if t["trustworthy_per_8"] is not None and leader["top_score"] - t["trustworthy_per_8"] >= 3.0
        )
    best = pick({k: t for k, t in s1.items() if k in PROCESS_ARMS})
    out["best_process"] = best
    p0 = s1.get("P0")
    if best and p0 and p0["trustworthy_per_8"] is not None:
        b = s1[best["pick"]]
        margin = round(b["trustworthy_per_8"] - p0["trustworthy_per_8"], 3)
        more_rescues = (p0["rescues_per_8"] or 0) > (b["rescues_per_8"] or 0)
        out["q1_process_needed"] = {
            "answer": margin > 1.0 or more_rescues,
            "best_process": best["pick"],
            "margin_per_8": margin,
            "p0_rescues_per_8": p0["rescues_per_8"],
            "best_rescues_per_8": b["rescues_per_8"],
        }
    else:
        out["q1_process_needed"] = {"answer": None, "why": "P0 or the process arms have no graded runs"}

    q6 = {"answer": None, "levels": {}}
    if best:
        rows_best = [v for v in verdicts if v.get("row") == best["pick"]]
        for level in ("S2", "S3"):
            name = f"P0/{level}"
            spec_runs = [v for v in verdicts if v.get("row") == name]
            if not spec_runs or by_row.get(name, {}).get("graded", 0) == 0:
                continue
            shared = set(by_row[name]["tickets_graded"]) & set(by_row[best["pick"]]["tickets_graded"])
            a, b = totals(spec_runs, shared), totals(rows_best, shared)
            if a["trustworthy_per_8"] is None or b["trustworthy_per_8"] is None:
                continue
            within = a["trustworthy_per_8"] >= b["trustworthy_per_8"] - 1.0
            attention_ok = (a["attention_words_avg"] or 0) <= (b["attention_words_avg"] or 0)
            q6["levels"][level] = {
                "shared_tickets": sorted(shared),
                "p0_per_8": a["trustworthy_per_8"],
                "best_process_per_8": b["trustworthy_per_8"],
                "within_one": within,
                "p0_attention_avg": a["attention_words_avg"],
                "best_process_attention_avg": b["attention_words_avg"],
                "attention_no_higher": attention_ok,
                "qualifies": within and attention_ok,
            }
        if q6["levels"]:
            q6["answer"] = any(x["qualifies"] for x in q6["levels"].values())
        s3 = f"{best['pick']}/S3"
        if by_row.get(s3, {}).get("graded"):
            q6["best_process_on_s3"] = {
                "row": s3,
                "per_8": by_row[s3]["trustworthy_per_8"],
                "note": "reported, no fixed rule",
            }
    out["q6_full_spec_replaces_pipeline"] = q6
    return out


CSV_FIELDS = [
    "run_id", "row", "arm", "spec", "ticket", "status", "outcome", "trustworthy", "discarded", "discard_reason",
    "hidden_tests_pass", "no_trap_tripped", "no_false_claim", "no_rescue",
    "all_planted_bugs_caught", "no_false_blocking_alarm",
    "stops_total", "stops_routine", "stops_warranted", "rescues", "correction_rounds", "attention_words",
    "quality_architecture_fit", "quality_readability", "quality_tests_meaningful", "merge_decidable_from_brief",
    "counted_tokens", "list_price_usd", "wall_seconds", "provisional",
]  # fmt: skip


def csv_row(v: dict) -> dict:
    m = v.get("measures") or {}
    q = m.get("quality") or {}
    row = {k: v.get(k) for k in ("run_id", "row", "arm", "spec", "ticket", "status", "outcome", "trustworthy",
                                  "discarded", "discard_reason", "provisional")}  # fmt: skip
    for name, c in (v.get("checks") or {}).items():
        row[name] = c.get("pass")
    for k in ("stops_total", "stops_routine", "stops_warranted", "rescues", "correction_rounds", "attention_words",
              "merge_decidable_from_brief", "counted_tokens", "list_price_usd", "wall_seconds"):  # fmt: skip
        row[k] = m.get(k)
    for d in QUALITY:
        row[f"quality_{d}"] = q.get(d)
    return row


def summarize(stage: str, root: str | None = None, out_dir: Path | None = None) -> dict:
    verdicts = load_verdicts(stage, root)
    rows = sorted({v["row"] for v in verdicts}, key=lambda r: (r.split("/")[0] not in ARM_ORDER, r))
    by_row = {r: totals([v for v in verdicts if v["row"] == r]) for r in rows}
    out_dir = Path(out_dir or LAB_ROOT / "results" / stage)
    plan = read_json(out_dir / "plan.json") or {}
    planned = [r["run_id"] for r in plan.get("runs", [])]
    have = {v["run_id"] for v in verdicts}
    summary = {
        "stage": stage,
        "time": now_iso(),
        "provisional": stage.startswith("stage-1"),
        "runs": len(verdicts),
        "planned_without_verdict": [r for r in planned if r not in have],
        "per_row": by_row,
        "decision": decide(by_row, verdicts),
        "run_rows": [csv_row(v) for v in sorted(verdicts, key=lambda v: v["run_id"])],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "summary.json", summary)
    with open(out_dir / "summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in summary["run_rows"]:
            w.writerow(r)
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m grader.summarize", description=__doc__.split("\n\n")[0])
    ap.add_argument("stage")
    ap.add_argument("--runs-root", help="default $FACTORY_RUNS_ROOT or ~/factory-runs")
    ap.add_argument("--out-dir", help="default results/<stage> in this repo")
    a = ap.parse_args(argv)
    s = summarize(a.stage, a.runs_root, Path(a.out_dir) if a.out_dir else None)
    d = s["decision"]
    label = " (provisional)" if s["provisional"] else ""
    print(f"stage {a.stage}{label}: {s['runs']} verdicts")
    for row, t in s["per_row"].items():
        print(f"  {row}: {t['trustworthy']}/{t['graded']} trustworthy ({t['trustworthy_per_8']} per 8), "
              f"{len(t['discarded'])} discarded, {len(t['incomplete'])} incomplete")  # fmt: skip
    if d.get("winner"):
        print(f"  winner by the tie rule: {d['winner']}; best process: {(d.get('best_process') or {}).get('pick')}; "
              f"dropped: {d.get('dropped')}; process needed: {d['q1_process_needed'].get('answer')}; "
              f"full spec replaces pipeline: {d['q6_full_spec_replaces_pipeline'].get('answer')}")  # fmt: skip
    return 0


if __name__ == "__main__":
    sys.exit(main())
