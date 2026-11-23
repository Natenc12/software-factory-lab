"""build_page3.py: the stage 2 results page. Reads graded records from two roots: `combined` (as frozen)
and `combined2` (with the post-freeze corrections), plus the two summary.json files from
grader.summarize. `python3 build_page3.py facts` prints the figures; no argument writes the page."""

import collections
import html
import json
import statistics
import sys
from pathlib import Path

S = Path(__file__).parent
ROOTS = {"corrected": Path.home() / "factory-runs-variants/combined2"}
SUMS = {"corrected": S / "sum-s2b/summary.json", "vs_p5p": S / "sum-s2b-p5p/summary.json"}
ARMS = [
    ("P1", "One-page guide"),
    ("P1A", "+ Architecture brief"),
    ("P5P", "+ Skills, pointed"),
    ("P5PA", "+ Skills, pointed, and the brief"),
]
ARM_NAME = dict(ARMS)
TICKETS = [
    ("T6", "Over-long upload", "wrong ask: breaks a written decision"),
    ("T11", "Retry loop", "wrong ask: false premise"),
    ("T12", "Whose file", "wrong ask: breaks a rule in the code"),
    ("T9", "File versions", "long chain, 12 files"),
    ("T10", "Class to course", "long chain, 15 files"),
    ("T2", "Error reply echo", "bug replay"),
    ("T5", "Duplicate class names", "vague ask"),
    ("T7", "Page numbers", "migration"),
]
TIDS = [t for t, _, _ in TICKETS]
WORD = {
    "hidden_tests_pass": "tests",
    "no_trap_tripped": "trap",
    "no_false_claim": "claim",
    "no_rescue": "rescue",
    "no_material_false_claim": "material claim",
    "no_agreed_rescue": "rescue",
}
SKILLS = [
    "check-the-ask",
    "prove-each-claim",
    "test-that-bites",
    "find-the-cause",
    "stay-in-scope",
    "fresh-eyes-review",
]
e = html.escape


def jload(p):
    try:
        return json.loads(Path(p).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def load(root):
    rows = []
    for stage in ("stage-1", "stage-1-confirm", "stage-2", "stage-2b"):
        for run in sorted(p for p in (root / stage).iterdir() if (p / "harness" / "verdict.json").is_file()):
            h = run / "harness"
            v = jload(h / "verdict.json")
            if v["arm"] not in ARM_NAME or v["spec"] != "S1" or v["ticket"] not in TIDS:
                continue
            m, c = v["measures"], v["checks"]
            sr = v.get("second_reading") or {}
            rj = jload(h / "run.json") or {}
            sev = jload(h / "judge-claim-severity.json") or {}
            rows.append(
                {
                    "run": run.name,
                    "stage": stage,
                    "arm": v["arm"],
                    "ticket": v["ticket"],
                    "rep": int(run.name.rsplit("-", 1)[1]),
                    "tw": v["trustworthy"],
                    "tw2": sr.get("trustworthy_second_reading"),
                    "failed": [k for k, x in c.items() if x["pass"] is False],
                    "undecided": [k for k, x in c.items() if x["pass"] is None],
                    "failed2": [k for k, x in (sr.get("checks") or {}).items() if x["pass"] is False],
                    "hidden": (c.get("hidden_tests_pass") or {}).get("detail"),
                    "traps": ((c.get("no_trap_tripped") or {}).get("detail") or {}).get("tripped") or [],
                    "claims": (c.get("no_false_claim") or {}).get("detail") or [],
                    "claims_sev": sev.get("claims") or [],
                    "stops": m.get("stops") or [],
                    "rescues": m.get("rescues") or 0,
                    "tokens": m.get("counted_tokens") or 0,
                    "usd": m.get("list_price_usd") or 0,
                    "words": m.get("attention_words") or 0,
                    "stops_total": m.get("stops_total") or 0,
                    "minutes": (m.get("wall_seconds") or 0) / 60,
                    "judge_tokens": m.get("grading_judge_tokens") or 0,
                    "reply_judge_tokens": m.get("reply_judge_tokens") or 0,
                    "quality": m.get("quality"),
                    "skills": rj.get("skills_used") or [],
                    "discarded": bool(v.get("discarded")),
                }
            )
    return rows


DATA = {k: load(r) for k, r in ROOTS.items() if r.is_dir()}
SUM = {k: jload(p) for k, p in SUMS.items() if p.is_file()}


def cellruns(v, arm, ticket):
    return sorted(
        (r for r in DATA[v] if r["arm"] == arm and r["ticket"] == ticket), key=lambda r: (r["stage"], r["rep"])
    )


def per8(v, arm, key="tw"):
    """Mean over tickets of the cell's own mean, times 8 (the rule's weighting). Undecided runs are left out."""
    cells = []
    for t in TIDS:
        rs = [r for r in cellruns(v, arm, t) if r[key] is not None and not r["discarded"]]
        if rs:
            cells.append(sum(1 for r in rs if r[key]) / len(rs))
    return 8 * statistics.mean(cells) if cells else 0.0


def tip(r):
    bits = [r["run"]]
    if r.get("hidden"):
        h = r["hidden"]
        bits.append(f"hidden tests {h['passed']} of {h['passed'] + h['failed'] + h['errors']}")
    if r["traps"]:
        bits.append("traps: " + ", ".join(r["traps"]))
    if r["claims"]:
        bits.append("false claim: “" + (r["claims"][0].get("claim") or "")[:110] + "”")
    if r["stops"]:
        bits.append("stops: " + ", ".join(s["reply_id"] for s in r["stops"]))
    if r["skills"]:
        bits.append("skills used: " + ", ".join(r["skills"]))
    bits.append(f"{round(r['tokens'] / 1000)}k tokens")
    return e(" · ".join(bits), quote=True)


def matrix(v):
    out = ['<div class="scroll"><table class="mx wide"><thead><tr><th>Way of working</th>']
    for t, name, kind in TICKETS:
        out.append(
            f'<th class="c"><span class="tid">{t}</span><span class="tk">{e(name)}</span><span class="tkind">{e(kind)}</span></th>'
        )
    out.append('<th class="num">Of 8</th></tr></thead><tbody>')
    for a, name in ARMS:
        out.append(f'<tr><th scope="row"><b>{a}</b> <span class="an">{e(name)}</span></th>')
        for t in TIDS:
            marks = []
            for r in cellruns(v, a, t):
                if r["discarded"]:
                    marks.append(
                        f'<span class="m na" tabindex="0" data-tip="discarded by the leak scan, wrongly, and re-run once · {tip(r)}">–</span>'
                    )
                elif r["tw"] is True:
                    marks.append(f'<span class="m ok" tabindex="0" data-tip="{tip(r)}">✓</span>')
                elif r["tw"] is False:
                    why = " + ".join(WORD.get(k, k) for k in r["failed"])
                    marks.append(f'<span class="m no" tabindex="0" data-tip="{e(why, quote=True)} · {tip(r)}">✗</span>')
                else:
                    marks.append(
                        f'<span class="m na" tabindex="0" data-tip="not decided: the honesty judge crashed on this run · {tip(r)}">?</span>'
                    )
            out.append(f'<td class="c"><span class="trio">{"".join(marks)}</span></td>')
        out.append(f'<td class="num"><b>{per8(v, a):.1f}</b></td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


def bars(items, fmt, mx=None):
    mx = mx or max(x for _, x, _, _ in items) or 1
    out = ['<div class="bars">']
    for label, x, t, extra in items:
        w = max(0.0, min(100.0, 100.0 * x / mx))
        out.append(
            f'<div class="bar" tabindex="0" data-tip="{e(t, quote=True)}"><span class="bl">{label}</span>'
            f'<span class="bt"><span class="bf" style="width:{w:.1f}%"></span></span><span class="bv">{fmt(x)}{extra}</span></div>'
        )
    out.append("</div>")
    return "".join(out)


def lab(a):
    return f'<b>{a}</b> <span class="an">{e(ARM_NAME[a])}</span>'


def chart_trust(v):
    return bars(
        [(lab(a), per8(v, a), f"{a}: {per8(v, a):.2f} of 8, each ticket weighted equally", "") for a, _ in ARMS],
        lambda x: f"{x:.1f}",
        mx=8,
    )


def cellmean(v, arm, key):
    cells = []
    for t in TIDS:
        rs = [r for r in cellruns(v, arm, t) if not r["discarded"]]
        if rs:
            cells.append(statistics.mean(r[key] for r in rs))
    return statistics.mean(cells)


def chart_cost(key, fmt, unit):
    return bars(
        [
            (
                lab(a),
                cellmean("frozen", a, key),
                f"{a}: {cellmean('frozen', a, key):,.1f} {unit}, each ticket weighted equally",
                "",
            )
            for a, _ in ARMS
        ],
        fmt,
    )


def chart_cost2(key, fmt, unit):
    return bars(
        [
            (
                lab(a),
                cellmean("corrected", a, key),
                f"{a}: {cellmean('corrected', a, key):,.1f} {unit}, each ticket weighted equally",
                "",
            )
            for a, _ in ARMS
        ],
        fmt,
    )


def quality_row():
    out = []
    for a, _ in ARMS:
        cells = []
        for t in TIDS:
            qs = [
                statistics.mean(r["quality"].values())
                for r in cellruns("corrected", a, t)
                if r["quality"] and not r["discarded"]
            ]
            if qs:
                cells.append(statistics.mean(qs))
        out.append(f"{a} {statistics.mean(cells):.2f}")
    return ", ".join(out)


def rule_table():
    out = [
        '<div class="scroll"><table class="wide"><thead><tr><th>Addition</th><th class="num">Trustworthy, of 8</th><th class="num">Quality, 1 to 5</th>'
        '<th class="num">Rescues</th><th class="num">Cost against P1</th><th class="num">Improves</th><th>By the rule</th></tr></thead><tbody>'
    ]
    for v, vlab in (("frozen", "As frozen"), ("corrected", "With the corrections")):
        if v not in SUM:
            continue
        for key, rlab in (("decision", "current rules"), ("decision_second_reading", "second reading")):
            d = SUM[v][key]["addons"]
            p1 = next(iter(d.values()))["p1"]
            out.append(
                f'<tr class="grp v v-{v}"><th scope="row" colspan="7">{vlab}, {rlab}. P1: {p1["trustworthy_per_8"]:.1f} of 8, quality {p1["quality"]:.2f}, {p1["rescues_per_8"]:.0f} rescues</th></tr>'
            )
            for a, _ in ARMS[1:]:
                x = d[a]
                df = x["differences"]
                ans = '<span class="tag s">goes in</span>' if x["answer"] else '<span class="tag">stays out</span>'
                out.append(
                    f'<tr class="v v-{v}"><th scope="row">{lab(a)}</th><td class="num">{x["addon"]["trustworthy_per_8"]:.1f} ({df["trustworthy_per_8"]:+.1f})</td>'
                    f'<td class="num">{x["addon"]["quality"]:.2f} ({df["quality"]:+.2f})</td><td class="num">{x["addon"]["rescues_per_8"]:.0f} ({df["rescues_per_8"]:+.0f})</td>'
                    f'<td class="num">×{x["cost_ratio"]:.2f}</td><td class="num">{x["improved_count"]} of 3</td><td>{ans}</td></tr>'
                )
    out.append("</tbody></table></div>")
    return "".join(out)


def skills_table():
    arms = ("P5P", "P5PA")
    n_runs = {a: sum(1 for r in DATA["corrected"] if r["arm"] == a and not r["discarded"]) for a in arms}
    out = [
        f'<div class="scroll"><table class="wide"><thead><tr><th>Skill</th><th class="num">Pointed skills: runs that used it, of {n_runs["P5P"]}</th>'
        f'<th class="num">Combined: runs that used it, of {n_runs["P5PA"]}</th></tr></thead><tbody>'
    ]
    for s in SKILLS:
        n = {
            a: sum(1 for r in DATA["corrected"] if r["arm"] == a and not r["discarded"] and s in r["skills"])
            for a in arms
        }
        out.append(
            f'<tr><th scope="row"><code>{s}</code></th><td class="num">{n["P5P"]}</td><td class="num">{n["P5PA"]}</td></tr>'
        )
    out.append("</tbody></table></div>")
    return "".join(out)


def wrong_ask_kind(r):
    ids = [s["reply_id"] for s in r["stops"]]
    raised = [
        i
        for i in ids
        if any(x in i for x in ("flaw-raised", "premise-raised", "conflict-raised", "amend-adr-question"))
    ]
    if raised:
        return "raised it first"
    if any("built-as-asked" in i for i in ids):
        return "turned round by reply"
    if any(t.startswith("key:") for t in r["traps"]):
        return "built the wrong thing"
    return "other"


def facts():
    for v in DATA:
        print("==", v, len(DATA[v]), "runs")
        for a, _ in ARMS:
            rs = [r for r in DATA[v] if r["arm"] == a]
            print(
                a,
                f"per8 {per8(v, a):.2f} second {per8(v, a, 'tw2'):.2f}",
                "runs",
                len(rs),
                "tw",
                sum(1 for r in rs if r["tw"]),
                "undecided",
                [r["run"] for r in rs if r["tw"] is None],
                f"tokens {cellmean(v, a, 'tokens'):,.0f} words {cellmean(v, a, 'words'):,.0f} stops {cellmean(v, a, 'stops_total'):.2f} min {cellmean(v, a, 'minutes'):.1f}",
            )
        for t in ("T6", "T11", "T12"):
            print(
                t,
                sorted(collections.Counter((r["arm"], wrong_ask_kind(r)) for r in DATA[v] if r["ticket"] == t).items()),
            )
        miss = collections.Counter()
        for r in DATA[v]:
            if r["tw"] is False and r["stage"] in ("stage-2", "stage-2b"):
                miss[(r["arm"], r["ticket"], "+".join(WORD.get(k, k) for k in r["failed"]))] += 1
        print("misses stage-2", sorted(miss.items()))
        for sk in SUM:
            for key in ("decision", "decision_second_reading"):
                print(
                    sk,
                    key,
                    {
                        a: (x["answer"], x["improved_count"], x["differences"], x["cost_ratio"])
                        for a, x in SUM[sk][key]["addons"].items()
                    },
                )
    s2 = [r for r in DATA["corrected"] if r["stage"] == "stage-2b"]
    print(
        "stage-2 runs",
        len(s2),
        "tokens",
        sum(r["tokens"] for r in s2),
        "judges",
        sum(r["judge_tokens"] for r in s2),
        "reply",
        sum(r["reply_judge_tokens"] for r in s2),
    )
    for r in s2:
        if r["claims"]:
            print(
                "CLAIM",
                r["run"],
                [(c.get("severity"), (c.get("claim") or "")[:100]) for c in (r["claims_sev"] or r["claims"])][:2],
            )


def build():
    import page_text as T

    body = (S / "page4_body.html").read_text()

    def both(fn):
        return fn("corrected")

    ctx = {
        "matrix": both(matrix),
        "chart_trust": both(chart_trust),
        "skills_table": skills_table(),
        "quality_row": quality_row(),
        "chart_tokens": chart_cost2("tokens", lambda x: f"{x / 1000:,.0f}k", "tokens per run"),
        "chart_words": chart_cost2("words", lambda x: f"{x:,.0f}", "words per ticket"),
        "chart_stops": chart_cost2("stops_total", lambda x: f"{x:.1f}", "stops per ticket"),
        "chart_minutes": chart_cost2("minutes", lambda x: f"{x:.0f} min", "minutes per run"),
    }
    for k, val in ctx.items():
        body = body.replace("{{" + k + "}}", val)
    import re

    left = re.findall(r"\{\{(\w+)\}\}", body)
    assert not left, left
    css = """<style>
.trio{display:inline-flex;gap:3px}
.m{display:inline-block;width:19px;height:22px;line-height:22px;border-radius:5px;font-weight:700;font-size:13px;cursor:default}
.m.ok{background:var(--goodbg);color:var(--good)}.m.no{background:var(--critbg);color:var(--crit)}.m.na{background:var(--warnbg);color:var(--warn)}
.m:focus-visible{outline:2px solid var(--w1);outline-offset:2px}
tr.grp th{font-size:12px;font-weight:700;color:var(--ink2);background:var(--grid);text-transform:none;letter-spacing:0}
main[data-v="frozen"] tr.v-corrected,main[data-v="corrected"] tr.v-frozen{display:none}
.plan td:first-child{white-space:nowrap;font-weight:600}
</style>
"""
    out = (
        T.HEAD.replace("<title>Factory Lab Stage 1 Results</title>", "<title>Factory Lab Tie-Break Round</title>")
        + css
        + body
        + T.SCRIPT
    ).replace("�", "&#xFFFD;")
    (S / "factory-lab-stage2b.html").write_text(out)
    print("wrote", S / "factory-lab-stage2b.html", len(out), "bytes")


if __name__ == "__main__":
    facts() if len(sys.argv) > 1 and sys.argv[1] == "facts" else build()
