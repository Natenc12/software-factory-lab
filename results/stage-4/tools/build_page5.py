"""build_page5.py: the stage 4 results page. Reads graded records from two roots: the runs as graded
at the freeze (`~/factory-runs`) and the copy re-judged with post-freeze correction 4
(`~/factory-runs-variants/corrected4`), plus the two summary.json files from grader.summarize.
`python3 build_page5.py facts` prints the figures; no argument writes the page next to this file.
Environment: SUM_FROZEN and SUM_CORRECTED point at the two summary.json files."""

import collections
import html
import json
import os
import sys
from pathlib import Path

S = Path(__file__).parent
ROOTS = {"frozen": Path.home() / "factory-runs", "corrected": Path.home() / "factory-runs-variants/corrected4"}
SUMS = {"frozen": Path(os.environ["SUM_FROZEN"]), "corrected": Path(os.environ["SUM_CORRECTED"])}
ROWS = [
    ("P5P", "Opus alone", "Opus 5.5, guide and pointed skills"),
    ("P5PF", "Fable alone", "Fable 5.2, same files"),
    ("P6P", "Fable leading Opus", "Fable 5.2 lead, Opus 5.5 workers"),
]
ROW_NAME = {r: n for r, n, _ in ROWS}
CODEBASES = [("hono", "Hono", "TypeScript web framework"), ("sqlglot", "sqlglot", "Python SQL parser")]
TICKETS = {
    "hono": [
        ("T1", "Repeated path parameter", "replay"),
        ("T2", "Login header escaping", "replay"),
        ("T3", "WebSocket errors", "replay"),
        ("T4", "Async components", "replay"),
        ("T5", "Client objects", "replay"),
        ("T6", "Request id", "feature"),
        ("T7", "Wildcard subdomains", "vague"),
        ("T8", "Static files and POST", "wrong request"),
    ],
    "sqlglot": [
        ("T1", "Column named top", "replay"),
        ("T2", "Stage paths", "replay"),
        ("T3", "Optimizer rewrite", "replay"),
        ("T4", "Array check lambda", "replay"),
        ("T5", "UPDATE OR REPLACE", "replay"),
        ("T6", "Cosine similarity", "feature"),
        ("T7", "COALESCE tidy-up", "vague"),
        ("T8", "Required dependency", "wrong request"),
    ],
}
WORD = {
    "hidden_tests_pass": "hidden tests",
    "no_trap_tripped": "trap",
    "no_false_claim": "false claim",
    "no_rescue": "rescue",
    "no_material_false_claim": "false claim that matters",
    "no_agreed_rescue": "rescue",
}
e = html.escape


def jload(p):
    try:
        return json.loads(Path(p).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def load(root):
    out = []
    for cb, _, _ in CODEBASES:
        stage = root / f"stage-4-{cb}"
        for run in sorted(p for p in stage.iterdir() if (p / "harness" / "verdict.json").is_file()):
            h = run / "harness"
            v = jload(h / "verdict.json")
            rj = jload(h / "run.json") or {}
            m, c = v["measures"], v["checks"]
            sr = v.get("second_reading") or {}
            ck = v.get("check_reading") or {}
            row = run.name.split("-")[0].upper()
            judge_tokens = 0
            for jf in h.glob("judge-*.json"):
                j = jload(jf) or {}
                judge_tokens += (j.get("usage") or {}).get("counted", 0) or 0
            sp = jload(h / "second-picks.json") or {}
            claims = [x.get("claim", "") for x in (c["no_false_claim"].get("detail") or []) if isinstance(x, dict)]
            bm = rj.get("by_model") or {}
            out.append(
                {
                    "run": run.name,
                    "cb": cb,
                    "row": row,
                    "ticket": v["ticket"],
                    "rep": int(run.name.rsplit("-", 1)[1]),
                    "discarded": bool(v.get("discarded")),
                    "discard_reason": v.get("discard_reason"),
                    "tw": bool(v.get("trustworthy")),
                    "tw2": bool(sr.get("trustworthy_second_reading")),
                    "twc": ck.get("trustworthy_check"),
                    "agree": ck.get("honesty_agree"),
                    "failed": [k for k, x in c.items() if x["pass"] is False],
                    "failed2": [k for k in ("hidden_tests_pass", "no_trap_tripped") if c[k]["pass"] is False]
                    + [k for k in ("no_material_false_claim", "no_agreed_rescue") if sr.get(k) is False],
                    "traps": c["no_trap_tripped"]["detail"].get("tripped") or [],
                    "claims": claims,
                    "hidden": c["hidden_tests_pass"]["detail"],
                    "stops": m.get("stops") or [],
                    "stops_total": m.get("stops_total", 0),
                    "rescues": m.get("rescues", 0),
                    "corr": m.get("correction_rounds", 0),
                    "words": m.get("attention_words", 0),
                    "tokens": m.get("counted_tokens", 0),
                    "usd": m.get("list_price_usd", 0.0),
                    "secs": m.get("wall_seconds", 0.0),
                    "quality": m.get("quality") or {},
                    "judgement": m.get("judgement") or {},
                    "tags": m.get("behaviour_tags") or [],
                    "workers": rj.get("workers_started") or 0,
                    "skills": rj.get("skills_used") or [],
                    "by_model": {k: (x.get("counted", 0), x.get("cost_usd", 0.0)) for k, x in bm.items()},
                    "reply_tokens": m.get("reply_judge_tokens", 0) or 0,
                    "judge_tokens": judge_tokens,
                    "second_pick_tokens": (sp.get("usage") or {}).get("counted", 0) if isinstance(sp, dict) else 0,
                }
            )
    return out


DATA = {k: load(r) for k, r in ROOTS.items()}
SUM = {k: jload(p) for k, p in SUMS.items()}
KEY = {"cur": "tw", "second": "tw2", "check": "twc"}


def live(v):
    return [r for r in DATA[v] if not r["discarded"]]


def cell(v, cb, row, ticket):
    return sorted((r for r in DATA[v] if (r["cb"], r["row"], r["ticket"]) == (cb, row, ticket)), key=lambda r: r["rep"])


def per8(v, row, key="tw", cbs=("hono", "sqlglot")):
    """Cell-weighted: mean over tickets of the cell's mean, times 8."""
    means = []
    for cb in cbs:
        for t, _, _ in TICKETS[cb]:
            runs = [r for r in cell(v, cb, row, t) if not r["discarded"] and r[key] is not None]
            if runs:
                means.append(sum(bool(r[key]) for r in runs) / len(runs))
    return 8 * sum(means) / len(means) if means else 0.0


def avg(v, row, f, cbs=("hono", "sqlglot")):
    xs = [f(r) for r in live(v) if r["row"] == row and r["cb"] in cbs]
    return sum(xs) / len(xs) if xs else 0.0


def cellavg(v, row, f, cbs=("hono", "sqlglot")):
    """Mean over tickets of the cell's mean: each ticket counts equally."""
    means = []
    for cb in cbs:
        for t, _, _ in TICKETS[cb]:
            runs = [r for r in cell(v, cb, row, t) if not r["discarded"]]
            if runs:
                means.append(sum(f(r) for r in runs) / len(runs))
    return sum(means) / len(means) if means else 0.0


def why(r, reading="cur"):
    f = r["failed"] if reading == "cur" else r["failed2"]
    parts = []
    for k in f:
        w = WORD.get(k, k)
        if k == "no_trap_tripped" and r["traps"]:
            w = "trap: " + ", ".join(t.replace("_", " ") for t in r["traps"])
        if k == "hidden_tests_pass":
            w = f"hidden tests {r['hidden'].get('passed', 0)} of {r['hidden'].get('passed', 0) + r['hidden'].get('failed', 0) + r['hidden'].get('errors', 0)}"
        parts.append(w)
    return "; ".join(parts)


def facts():
    for v in ("frozen", "corrected"):
        print("=====", v, "runs", len(DATA[v]), "discarded", [r["run"] for r in DATA[v] if r["discarded"]])
        for row, _, _ in ROWS:
            print(
                f"{row:5} pooled cur {per8(v, row):.2f} second {per8(v, row, 'tw2'):.2f} check {per8(v, row, 'twc'):.2f}"
                f" | hono {per8(v, row, cbs=('hono',)):.2f}/{per8(v, row, 'tw2', ('hono',)):.2f}/{per8(v, row, 'twc', ('hono',)):.2f}"
                f" sqlglot {per8(v, row, cbs=('sqlglot',)):.2f}/{per8(v, row, 'tw2', ('sqlglot',)):.2f}/{per8(v, row, 'twc', ('sqlglot',)):.2f}"
                f" | n {sum(1 for r in live(v) if r['row'] == row)} tw {sum(r['tw'] for r in live(v) if r['row'] == row)}"
                f" | tok {avg(v, row, lambda r: r['tokens']):,.0f} usd {avg(v, row, lambda r: r['usd']):.3f} min {avg(v, row, lambda r: r['secs']) / 60:.1f}"
                f" words {avg(v, row, lambda r: r['words']):.0f} stops {sum(r['stops_total'] for r in live(v) if r['row'] == row)}"
                f" rescues {sum(r['rescues'] for r in live(v) if r['row'] == row)} corr {sum(r['corr'] for r in live(v) if r['row'] == row)}"
                f" workers {sum(r['workers'] for r in live(v) if r['row'] == row)} agree {sum(bool(r['agree']) for r in live(v) if r['row'] == row)}"
            )
            for cb in ("hono", "sqlglot"):
                print(
                    f"      {cb}: usd {avg(v, row, lambda r: r['usd'], (cb,)):.3f} tok {avg(v, row, lambda r: r['tokens'], (cb,)):,.0f} min {avg(v, row, lambda r: r['secs'], (cb,)) / 60:.1f}"
                )
            bm = collections.Counter()
            for r in live(v):
                if r["row"] == row:
                    for k, (t, c) in r["by_model"].items():
                        bm[k + " tok"] += t
                        bm[k + " usd"] += c
            print("      by model", {k: round(x, 2) for k, x in bm.items()})
        print("losses (current reading):")
        for r in live(v):
            if not r["tw"]:
                print(
                    f"   {r['cb']:7} {r['run']:11} {why(r):50} second={r['tw2']} check={r['twc']} stops={r['stops_total']}"
                    f" | {(r['claims'][0][:110] if r['claims'] else '')}"
                )
        print("vague and wrong-request tickets:")
        for cb in ("hono", "sqlglot"):
            for t in ("T7", "T8"):
                for row, _, _ in ROWS:
                    rs = [r for r in cell(v, cb, row, t) if not r["discarded"]]
                    print(
                        f"   {cb:7} {t} {row:5} asked {sum(1 for r in rs if r['stops_total'])}/{len(rs)} trustworthy {sum(r['tw'] for r in rs)}/{len(rs)}"
                        f" replies {[s.get('reply_id') for r in rs for s in r['stops']]}"
                    )
    v = "frozen"
    print(
        "spend: runs",
        sum(r["tokens"] for r in DATA[v]),
        "reply judge",
        sum(r["reply_tokens"] for r in DATA[v]),
        "grading judges frozen",
        sum(r["judge_tokens"] for r in DATA[v]),
        "corrected extra judges",
        sum(r["judge_tokens"] for r in DATA["corrected"] if r["workers"]),
        "usd runs",
        round(sum(r["usd"] for r in DATA[v]), 2),
    )
    sk = collections.defaultdict(collections.Counter)
    for r in live(v):
        for s in r["skills"]:
            sk[r["row"]][s] += 1
    print("skills", {k: dict(x) for k, x in sk.items()})
    print(
        "quality",
        {
            row: {
                k: round(avg(v, row, lambda r, k=k: r["quality"].get(k, 0)), 2)
                for k in ("architecture_fit", "readability", "tests_meaningful")
            }
            for row, _, _ in ROWS
        },
    )
    print(
        "judgement preferred",
        {
            row: collections.Counter(r["judgement"].get("preferred") for r in live(v) if r["row"] == row)
            for row, _, _ in ROWS
        },
    )
    print(
        "workers per P6P run",
        collections.Counter(r["workers"] for r in live(v) if r["row"] == "P6P"),
        "P5P with workers",
        [r["run"] + "/" + r["cb"] for r in live(v) if r["row"] != "P6P" and r["workers"]],
    )
    for name in ("frozen", "corrected"):
        d = SUM[name]["decision"]
        print(
            name,
            "Q5 fable_builds",
            d["fable_builds"],
            {r: x["trustworthy_per_8"] for r, x in d["rows"].items()},
            "second",
            SUM[name]["decision_second_reading"]["fable_builds"],
            {r: x["trustworthy_per_8"] for r, x in SUM[name]["decision_second_reading"]["rows"].items()},
            "only_etc",
            SUM[name]["only_existing_tests_changed"],
        )
        print(
            "   check",
            {
                r: (x["trustworthy_per_8_check"], x["honesty_agree"])
                for r, x in SUM[name]["check_reading"]["pooled"].items()
            },
        )


def both(f, fmt="{:.1f}"):
    """A figure that differs between the two gradings: both are written, the switch shows one."""
    a, b = f("frozen"), f("corrected")
    a, b = (fmt.format(a), fmt.format(b)) if fmt else (a, b)
    if a == b:
        return a
    return f'<span class="v-frozen">{a}</span><span class="v-corrected">{b}</span>'


def tip(r):
    if r["discarded"]:
        return f"{r['run']}: thrown out ({r['discard_reason']}). Its re-run is the mark beside it."

    def yn(x):
        return "yes" if x else "no"

    head = f"{r['run']}: trustworthy" if r["tw"] else f"{r['run']}: lost on {why(r)}"
    if r["claims"] and not r["tw"] and "no_false_claim" in r["failed"]:
        head += f'. The claim: "{r["claims"][0][:150]}"'
    tail = f". Second reading: {yn(r['tw2'])}. Opus as judge: {yn(r['twc'])}."
    if r["stops_total"]:
        tail += f" Stopped for you {r['stops_total']} time{'s' if r['stops_total'] > 1 else ''}."
    return head + tail


def matrix1(v, cb):
    ts = TICKETS[cb]
    hd = "".join(
        f'<th class="c"><span class="tid">{t}</span><span class="tk">{e(n)}</span><span class="tkind">{e(k)}</span></th>'
        for t, n, k in ts
    )
    body = []
    for row, name, sub in ROWS:
        tds = []
        for t, _, _ in ts:
            marks = []
            for r in cell(v, cb, row, t):
                cls, ch = (
                    ("none", "&ndash;") if r["discarded"] else (("ok", "&#10003;") if r["tw"] else ("no", "&#10007;"))
                )
                marks.append(f'<span class="cell {cls}" tabindex="0" data-tip="{e(tip(r), quote=True)}">{ch}</span>')
            tds.append('<td class="c">' + " ".join(marks) + "</td>")
        body.append(
            f'<tr><th><b>{e(name)}</b><br><span class="small">{e(sub)}</span></th>{"".join(tds)}'
            f'<td class="num"><b>{per8(v, row, cbs=(cb,)):.1f}</b></td></tr>'
        )
    return (
        f'<table class="mx wide"><thead><tr><th>Setup</th>{hd}<th class="num">Of 8</th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table>'
    )


def matrix(cb):
    return "".join(f'<div class="v-{v} scroll">{matrix1(v, cb)}</div>' for v in ("frozen", "corrected"))


def bars(items, fmt, mx=None):
    mx = mx or max((x for _, x, _ in items), default=1) or 1
    out = []
    for label, x, t in items:
        out.append(
            f'<div class="bar" tabindex="0" data-tip="{e(t, quote=True)}"><span class="bl">{e(label)}</span>'
            f'<span class="bt"><span class="bf" style="width:{100 * x / mx:.1f}%"></span></span>'
            f'<span class="bv">{fmt(x)}</span></div>'
        )
    return '<div class="bars">' + "".join(out) + "</div>"


def chart_trust(cbs, key="tw"):
    def one(v):
        items = []
        for row, name, _ in ROWS:
            n = sum(1 for r in live(v) if r["row"] == row and r["cb"] in cbs)
            k = sum(1 for r in live(v) if r["row"] == row and r["cb"] in cbs and r[key])
            items.append(
                (
                    name,
                    per8(v, row, key, cbs),
                    f"{name}: {k} of {n} runs trustworthy; {per8(v, row, key, cbs):.2f} of 8 with each ticket counting equally",
                )
            )
        return bars(items, lambda x: f"{x:.1f}", 8)

    return "".join(f'<div class="v-{v}">{one(v)}</div>' for v in ("frozen", "corrected"))


def usd(row, cb=None):
    d = SUM["frozen"]["decision"]
    x = d["per_codebase"][cb]["rows"][row] if cb else d["rows"][row]
    return x["list_price_usd_per_run"]


def chart_usd(cb=None):
    items = []
    for row, name, _ in ROWS:
        t = f"{name}: ${usd(row, cb):.2f} a run at list price"
        if row == "P6P":
            bm = (
                SUM["frozen"]["decision"]["per_codebase"][cb]["rows"][row]
                if cb
                else SUM["frozen"]["decision"]["rows"][row]
            )["by_model"]
            n = (
                SUM["frozen"]["decision"]["per_codebase"][cb]["rows"][row]
                if cb
                else SUM["frozen"]["decision"]["rows"][row]
            )["runs"]
            f, o = bm["claude-fable-5-2"]["list_price_usd"] / n, bm["claude-opus-5-5"]["list_price_usd"] / n
            t += f"; about ${f:.2f} of it is the Fable lead and ${o:.2f} the Opus workers"
        items.append((name, usd(row, cb), t))
    return bars(items, lambda x: f"${x:.2f}")


def chart_cell(f, fmt, unit):
    items = [
        (
            name,
            cellavg("frozen", row, f),
            f"{name}: {fmt(cellavg('frozen', row, f))} {unit}; Hono {fmt(cellavg('frozen', row, f, ('hono',)))}, sqlglot {fmt(cellavg('frozen', row, f, ('sqlglot',)))}",
        )
        for row, name, _ in ROWS
    ]
    return bars(items, fmt)


def build():
    body = (S / "page5_body.html").read_text()
    fill = dict(globals())
    exec((S / "page5_fill.py").read_text(), fill)
    for k, val in fill["FILL"].items():
        body = body.replace("{{" + k + "}}", str(val))
    assert "{{" not in body, body[body.index("{{") : body.index("{{") + 60]
    head = '<title>Factory Lab Stage 4 Results</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
    page = head + (S / "page5-css.txt").read_text() + body + (S / "page5-js.txt").read_text()
    page = page.replace(chr(0xFFFD), "&#xFFFD;")
    (S / "factory-lab-stage4.html").write_text(page)
    print("wrote", S / "factory-lab-stage4.html", len(page))


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "facts":
    facts()
elif __name__ == "__main__":
    build()
