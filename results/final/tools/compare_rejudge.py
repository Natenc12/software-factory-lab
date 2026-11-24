"""compare_rejudge.py: before and after the re-judging under post-freeze correction 4 in
~/factory-runs-variants/final. Writes results/final/rejudged/changes.json and prints a markdown summary.

    python3 results/final/tools/compare_rejudge.py

Per re-judged run (harness/.rejudged): the stored verdict (before-correction-4/verdict.json), the verdict
rebuilt from the old judges with the current code (verdict.rebuilt.json: shows the rebuild alone changes
nothing) and the new one; the false claims each honesty pass found, before and after; and the counted
tokens and list price of the new judge calls. Per stage: each row's trustworthy per 8 and the rule's
outcome, from results/final/rejudged/<stage>/before/ and results/final/rejudged/<stage>/.
"""

import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[3]
ROOT = Path.home() / "factory-runs-variants" / "final"
OUT = LAB / "results" / "final" / "rejudged"
STAGES = ["stage-1", "stage-1-confirm", "stage-2", "stage-2b"]
SUMMARIES = {
    "stage-1": ["summary.json"],
    "stage-1-confirm": ["summary.json"],
    "stage-2": ["summary.json"],
    "stage-2b": ["summary/summary.json", "summary-against-p5p/summary.json"],
}


def load(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def claims(j) -> list[str]:
    return [c.get("claim", "") for c in ((j or {}).get("result") or {}).get("false_claims") or []]


def readings(v) -> dict:
    sr = v.get("second_reading") or {}
    return {"current": v.get("trustworthy"), "second": sr.get("trustworthy_second_reading")}


def failing(v) -> list[str]:
    return sorted(k for k, c in (v.get("checks") or {}).items() if not c.get("pass"))


def runs() -> list[dict]:
    out = []
    for st in STAGES:
        for h in sorted((ROOT / st).glob("*/harness")):
            if not (h / ".rejudged").exists():
                continue
            b = h / "before-correction-4"
            old, rebuilt, new = load(b / "verdict.json"), load(b / "verdict.rebuilt.json"), load(h / "verdict.json")
            spend = {"counted_tokens": 0, "list_price_usd": 0.0, "calls": 0}
            for f in ("judge-honesty.json", "judge-honesty-2.json", "judge-claim-severity.json"):
                j = load(h / f) or {}
                u = j.get("usage") or {}
                if u.get("counted"):
                    spend["calls"] += 1
                    spend["counted_tokens"] += int(u["counted"])
                    spend["list_price_usd"] += float(j.get("list_price_usd") or 0)
            out.append(
                {
                    "stage": st,
                    "run_id": old["run_id"],
                    "arm": old["arm"],
                    "ticket": old["ticket"],
                    "before": readings(old),
                    "rebuilt_from_old_judges": readings(rebuilt),
                    "after": readings(new),
                    "failing_before": failing(old),
                    "failing_after": failing(new),
                    "claims_before": {
                        "pass 1": claims(load(b / "judge-honesty.json")),
                        "pass 2": claims(load(b / "judge-honesty-2.json")),
                    },
                    "claims_after": {
                        "pass 1": claims(load(h / "judge-honesty.json")),
                        "pass 2": claims(load(h / "judge-honesty-2.json")),
                    },
                    "spend": spend,
                }
            )
    return out


def stage_table(st: str) -> list[dict]:
    out = []
    for rel in SUMMARIES[st]:
        b, a = load(OUT / st / "before" / rel), load(OUT / st / rel)
        if not (a and b):
            continue
        rows = {}
        for key in ("per_row", "per_row_second_reading"):
            for r in a[key]:
                rows.setdefault(r, {})[key] = (
                    b[key].get(r, {}).get("trustworthy_per_8"),
                    a[key][r]["trustworthy_per_8"],
                )
        out.append(
            {
                "summary": f"{st}/{rel}",
                "rows": rows,
                "decision_same": b["decision"] == a["decision"],
                "decision_second_reading_same": b.get("decision_second_reading") == a.get("decision_second_reading"),
                "against_control_same": b.get("against_control") == a.get("against_control"),
            }
        )
    return out


def main() -> int:
    rs = runs()
    changed = [r for r in rs if r["before"] != r["after"]]
    rebuild_drift = [r for r in rs if r["before"] != r["rebuilt_from_old_judges"]]
    spend = {
        "runs": len(rs),
        "calls": sum(r["spend"]["calls"] for r in rs),
        "counted_tokens": sum(r["spend"]["counted_tokens"] for r in rs),
        "list_price_usd": round(sum(r["spend"]["list_price_usd"] for r in rs), 2),
    }
    d = {
        "spend": spend,
        "changed": changed,
        "rebuild_drift": rebuild_drift,
        "stages": {st: stage_table(st) for st in STAGES},
        "runs": rs,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "changes.json").write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")
    print(
        f"re-judged {spend['runs']} runs, {spend['calls']} calls, {spend['counted_tokens']:,} counted tokens, ${spend['list_price_usd']}"
    )
    print(f"verdicts changed: {len(changed)}; rebuild alone changed: {len(rebuild_drift)}")
    for r in changed:
        print(
            f"- {r['stage']}/{r['run_id']}: current {r['before']['current']} -> {r['after']['current']}, second {r['before']['second']} -> {r['after']['second']}; "
            f"failing {r['failing_before']} -> {r['failing_after']}; claims before {r['claims_before']}; after {r['claims_after']}"
        )
    for tables in d["stages"].values():
        for t in tables:
            moved = {r: v for r, v in t["rows"].items() if any(x[0] != x[1] for x in v.values())}
            print(
                f"{t['summary']}: decision same {t['decision_same']}, second-reading decision same {t['decision_second_reading_same']}, against control same {t['against_control_same']}; rows moved {moved}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
