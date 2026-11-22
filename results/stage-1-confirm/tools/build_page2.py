"""build_page2.py: the confirm-round page (three repeats per cell, two readings) and the stage 2 plan.
Reads the graded records under ~/factory-runs-variants/combined (stage-1 with the corrections, and the
confirm round). `python3 build_page2.py facts` prints the figures; with no argument it writes the page."""

import html
import json
import statistics
import sys
from pathlib import Path

S = Path(__file__).parent
ROOT = Path.home() / "factory-runs-variants/combined"
ARMS = [("P0", "Bare"), ("P1", "Loose"), ("P1R", "Loose + reviewer"), ("P3", "Contract"), ("P2", "Checklist")]
ARM_NAME = dict(ARMS)
TICKETS = [
    ("T1", "Stale status row", "bug replay"),
    ("T2", "Error reply echo", "bug replay"),
    ("T3", "Id spelling", "bug replay"),
    ("T4", "Delete a file", "feature"),
    ("T5", "Duplicate class names", "vague ask"),
    ("T6", "Over-long upload", "wrong ask"),
    ("T7", "Page numbers", "migration"),
    ("T8", "Review a change", "review"),
]
WORD = {
    "hidden_tests_pass": "tests",
    "no_trap_tripped": "trap",
    "no_false_claim": "claim",
    "no_rescue": "rescue",
    "all_planted_bugs_caught": "missed bug",
    "no_false_blocking_alarm": "false alarm",
    "no_material_false_claim": "material claim",
    "no_agreed_rescue": "rescue",
}
e = html.escape


def jload(p):
    try:
        return json.loads(Path(p).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def load():
    rows = []
    for stage in ("stage-1", "stage-1-confirm"):
        for run in sorted(p for p in (ROOT / stage).iterdir() if (p / "harness" / "verdict.json").is_file()):
            h = run / "harness"
            v = jload(h / "verdict.json")
            if v["arm"] not in ARM_NAME or v["spec"] != "S1":
                continue
            m, c = v["measures"], v["checks"]
            sr = v.get("second_reading") or {}
            h1, h2, sev, sp = (
                jload(h / "judge-honesty.json"),
                jload(h / "judge-honesty-2.json"),
                jload(h / "judge-claim-severity.json"),
                jload(h / "second-picks.json"),
            )
            rows.append(
                {
                    "run": run.name,
                    "stage": stage,
                    "arm": v["arm"],
                    "ticket": v["ticket"],
                    "rep": int(run.name.rsplit("-", 1)[1]),
                    "tw": v["trustworthy"],
                    "tw2": sr.get("trustworthy_second_reading"),
                    "missing2": sr.get("missing"),
                    "failed": [k for k, x in c.items() if not x["pass"]],
                    "failed2": [k for k, x in (sr.get("checks") or {}).items() if x["pass"] is False],
                    "hidden": (c.get("hidden_tests_pass") or {}).get("detail"),
                    "traps": ((c.get("no_trap_tripped") or {}).get("detail") or {}).get("tripped") or [],
                    "claims1": (c.get("no_false_claim") or {}).get("detail") or [],
                    "claims_sev": (sev or {}).get("claims") or [],
                    "pass1_any": bool((c.get("no_false_claim") or {}).get("detail")),
                    "pass2_any": None
                    if not h2 or not h2.get("valid")
                    else bool(((h2.get("result") or {}).get("false_claims")) or []),
                    "material": (sev or {}).get("material"),
                    "slip": (sev or {}).get("slip"),
                    "stops": m.get("stops") or [],
                    "rescues": m.get("rescues") or 0,
                    "agreed_rescues": sr.get("agreed_rescues"),
                    "second_picks": (sp or {}).get("picks") or [],
                    "tokens": m.get("counted_tokens") or 0,
                    "usd": m.get("list_price_usd") or 0,
                    "words": m.get("attention_words") or 0,
                    "stops_total": m.get("stops_total") or 0,
                    "routine": m.get("stops_routine") or 0,
                    "warranted": m.get("stops_warranted") or 0,
                    "minutes": (m.get("wall_seconds") or 0) / 60,
                    "judge_tokens": m.get("grading_judge_tokens") or 0,
                    "reply_judge_tokens": m.get("reply_judge_tokens") or 0,
                    "second_tokens": sum(((x or {}).get("usage") or {}).get("counted", 0) for x in (h2, sev, sp)),
                    "judgement": m.get("judgement"),
                    "quality": m.get("quality"),
                    "tags": m.get("behaviour_tags") or [],
                }
            )
    return rows


R = load()


def cellruns(arm, ticket):
    return sorted((r for r in R if r["arm"] == arm and r["ticket"] == ticket), key=lambda r: r["rep"])


def per8(arm, key):
    out = []
    for rep in (1, 2, 3):
        rs = [r for r in R if r["arm"] == arm and r["rep"] == rep]
        out.append(sum(1 for r in rs if r[key] is True))
    return out


def tip(r, reading):
    bits = [r["run"]]
    if r.get("hidden"):
        h = r["hidden"]
        bits.append(f"hidden tests {h['passed']} of {h['passed'] + h['failed'] + h['errors']}")
    if r["traps"]:
        bits.append("traps: " + ", ".join(r["traps"]))
    for c in r["claims_sev"][:2]:
        bits.append(f"{c.get('severity', 'unmarked')} claim: “{(c.get('claim') or '')[:110]}”")
    if not r["claims_sev"] and r["claims1"]:
        bits.append("false claim: “" + (r["claims1"][0].get("claim") or "")[:110] + "”")
    if r["rescues"]:
        bits.append(
            "rescued by the owner's reply"
            + (
                " (both judges agree)"
                if r["agreed_rescues"]
                else " (second judge disagrees)"
                if r["agreed_rescues"] == 0
                else ""
            )
        )
    bits.append(f"{round(r['tokens'] / 1000)}k tokens, {r['stops_total']} stops")
    return e(" · ".join(bits), quote=True)


def matrix(reading):
    key, fk = ("tw", "failed") if reading == "current" else ("tw2", "failed2")
    out = ['<div class="scroll"><table class="mx wide"><thead><tr><th>Arm</th>']
    for t, name, kind in TICKETS:
        out.append(
            f'<th class="c"><span class="tid">{t}</span><span class="tk">{e(name)}</span><span class="tkind">{e(kind)}</span></th>'
        )
    out.append('<th class="num">Per repeat</th><th class="num">Mean of 8</th></tr></thead><tbody>')
    for a, _ in ARMS:
        out.append(f'<tr><th scope="row"><b>{a}</b> <span class="an">{e(ARM_NAME[a])}</span></th>')
        for t, _, _ in TICKETS:
            marks = []
            for r in cellruns(a, t):
                if r[key] is True:
                    marks.append(f'<span class="m ok" tabindex="0" data-tip="{tip(r, reading)}">✓</span>')
                elif r[key] is False:
                    why = " + ".join(WORD.get(k, k) for k in r[fk])
                    marks.append(
                        f'<span class="m no" tabindex="0" data-tip="{e(why, quote=True)} · {tip(r, reading)}">✗</span>'
                    )
                else:
                    marks.append('<span class="m na" tabindex="0" data-tip="not decided">?</span>')
            out.append(f'<td class="c"><span class="trio">{"".join(marks)}</span></td>')
        p = per8(a, key)
        out.append(
            f'<td class="num">{p[0]}, {p[1]}, {p[2]}</td><td class="num"><b>{statistics.mean(p):.1f}</b></td></tr>'
        )
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


def chart_trust(reading):
    key = "tw" if reading == "current" else "tw2"
    items = []
    for a, _ in ARMS:
        p = per8(a, key)
        items.append(
            (
                lab(a),
                statistics.mean(p),
                f"{a}: {p[0]}, {p[1]} and {p[2]} of 8 in the three repeats",
                f' <span class="an">({p[0]}, {p[1]}, {p[2]})</span>',
            )
        )
    return bars(items, lambda x: f"{x:.1f}", mx=8)


def agg(a):
    rs = [r for r in R if r["arm"] == a]
    n = len(rs)
    return {
        "n": n,
        "tokens": sum(r["tokens"] for r in rs) / n,
        "usd": sum(r["usd"] for r in rs) / n,
        "words": sum(r["words"] for r in rs) / n,
        "stops": sum(r["stops_total"] for r in rs) / n,
        "routine": sum(r["routine"] for r in rs),
        "warranted": sum(r["warranted"] for r in rs),
        "minutes": sum(r["minutes"] for r in rs) / n,
        "rescues": sum(r["rescues"] for r in rs),
        "agreed": sum((r["agreed_rescues"] or 0) for r in rs),
        "p1": sum(r["pass1_any"] for r in rs),
        "p2": sum(bool(r["pass2_any"]) for r in rs),
        "either": sum(1 for r in rs if r["pass1_any"] or r["pass2_any"]),
        "both": sum(1 for r in rs if r["pass1_any"] and r["pass2_any"]),
        "material_runs": sum(1 for r in rs if (r["material"] or 0) > 0),
        "material": sum(r["material"] or 0 for r in rs),
        "slip": sum(r["slip"] or 0 for r in rs),
    }


def cost_chart(key, fmt, tipf):
    return bars([(lab(a), agg(a)[key], f"{a}: {tipf(agg(a))}", "") for a, _ in ARMS], fmt)


def honesty_table():
    out = [
        '<div class="scroll"><table class="wide"><thead><tr><th>Arm</th><th class="num">Runs</th><th class="num">Pass 1 found a claim</th><th class="num">Pass 2</th>'
        '<th class="num">Both</th><th class="num">Material claims</th><th class="num">Slips</th><th class="num">Runs with a material claim</th></tr></thead><tbody>'
    ]
    for a, _ in ARMS:
        g = agg(a)
        out.append(
            f'<tr><th scope="row">{lab(a)}</th><td class="num">{g["n"]}</td><td class="num">{g["p1"]}</td><td class="num">{g["p2"]}</td><td class="num">{g["both"]}</td>'
            f'<td class="num">{g["material"]}</td><td class="num">{g["slip"]}</td><td class="num"><b>{g["material_runs"]}</b></td></tr>'
        )
    out.append("</tbody></table></div>")
    return "".join(out)


def t6_kind(r):
    ids = [s["reply_id"] for s in r["stops"]]
    if "T6-flaw-raised" in ids:
        return "asked first"
    if "T6-built-as-asked" in ids or any(i.startswith("T6-") and "plan" in i for i in ids):
        return "turned round by your reply"
    if "key:flawed-ticket-built-as-asked" in r["traps"]:
        return "built the wrong thing"
    return "other"


def facts():
    print("runs", len(R), {a: sum(1 for r in R if r["arm"] == a) for a, _ in ARMS})
    for a, _ in ARMS:
        print(
            a,
            "current",
            per8(a, "tw"),
            "second",
            per8(a, "tw2"),
            {k: (round(v, 2) if isinstance(v, float) else v) for k, v in agg(a).items()},
        )
    print("undecided second", [(r["run"], r["missing2"]) for r in R if r["tw2"] is None])
    print("flips", [(r["run"], r["tw"], r["tw2"], r["failed"], r["failed2"]) for r in R if r["tw"] != r["tw2"]])
    both = sum(1 for r in R if r["pass2_any"] is not None)
    agree = sum(1 for r in R if r["pass2_any"] is not None and r["pass1_any"] == r["pass2_any"])
    print("honesty passes agree on any-claim:", agree, "of", both)
    stops = [(r, s) for r in R for s in r["stops"]]
    print(
        "stops",
        len(stops),
        "rescue first",
        sum(1 for _, s in stops if s["rescue"]),
        "agreed",
        sum((r["agreed_rescues"] or 0) for r in R),
    )
    import collections

    print("T6", collections.Counter((r["arm"], t6_kind(r)) for r in R if r["ticket"] == "T6"))
    print(
        "tokens runs",
        sum(r["tokens"] for r in R if r["stage"] == "stage-1-confirm"),
        "judges",
        sum(r["judge_tokens"] for r in R if r["stage"] == "stage-1-confirm"),
        "reply",
        sum(r["reply_judge_tokens"] for r in R if r["stage"] == "stage-1-confirm"),
        "second reading all",
        sum(r["second_tokens"] for r in R),
    )
    for r in R:
        for c in r["claims_sev"]:
            if c.get("severity") == "material":
                print("MATERIAL", r["run"], (c.get("claim") or "")[:120], "|", (c.get("reason") or "")[:140])
    miss = collections.Counter()
    for r in R:
        if r["tw"] is False:
            miss[(r["arm"], "+".join(WORD.get(k, k) for k in r["failed"]))] += 1
    print("misses current", sorted(miss.items()))


def build():
    import page_text as T

    body = (S / "page2_body.html").read_text()
    both = lambda fn: "".join(
        f'<div class="v v-{v}">{fn(r)}</div>' for v, r in (("frozen", "current"), ("corrected", "second"))
    )  # noqa: E731
    ctx = {
        "toggle": '<div class="toggle" role="group" aria-label="Reading"><button type="button" data-v="frozen" aria-pressed="true">Current rules</button>'
        '<button type="button" data-v="corrected" aria-pressed="false">Second reading</button></div>',
        "matrix": both(matrix),
        "chart_trust": both(chart_trust),
        "honesty_table": honesty_table(),
        "chart_tokens": cost_chart(
            "tokens",
            lambda x: f"{x / 1000:,.0f}k",
            lambda g: f"{g['tokens']:,.0f} tokens per run, ${g['usd']:.2f} at list price",
        ),
        "chart_words": cost_chart("words", lambda x: f"{x:,.0f}", lambda g: f"{g['words']:,.0f} words per ticket"),
        "chart_stops": cost_chart(
            "stops",
            lambda x: f"{x:.1f}",
            lambda g: f"{g['routine']} routine and {g['warranted']} warranted stops over {g['n']} runs",
        ),
        "chart_minutes": cost_chart(
            "minutes", lambda x: f"{x:.0f} min", lambda g: f"{g['minutes']:.1f} minutes per run"
        ),
    }
    for k, val in ctx.items():
        body = body.replace("{{" + k + "}}", val)
    import re

    assert not re.findall(r"\{\{(\w+)\}\}", body), re.findall(r"\{\{(\w+)\}\}", body)
    extra_css = """<style>
.trio{display:inline-flex;gap:3px}
.m{display:inline-block;width:19px;height:22px;line-height:22px;border-radius:5px;font-weight:700;font-size:13px;cursor:default}
.m.ok{background:var(--goodbg);color:var(--good)}.m.no{background:var(--critbg);color:var(--crit)}.m.na{background:var(--warnbg);color:var(--warn)}
.m:focus-visible{outline:2px solid var(--w1);outline-offset:2px}
.plan td:first-child{white-space:nowrap;font-weight:600}
</style>
"""
    out = (
        T.HEAD.replace("<title>Factory Lab Stage 1 Results</title>", "<title>Factory Lab Confirm Round</title>")
        + extra_css
        + body
        + T.SCRIPT
    ).replace("�", "&#xFFFD;")
    (S / "factory-lab-confirm.html").write_text(out)
    print("wrote", S / "factory-lab-confirm.html", len(out), "bytes")


if __name__ == "__main__":
    facts() if len(sys.argv) > 1 and sys.argv[1] == "facts" else build()
