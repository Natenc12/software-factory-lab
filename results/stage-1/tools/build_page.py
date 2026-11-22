"""build_page.py: builds the stage 1 results page from the graded records. Every number on the page is
computed here from rows-frozen.json / rows-corrected.json (pagedata.py), the two summary.json files
(grader.summarize), the second reply picks and pairs.json. Prose lives in page_text.py."""

import html
import json
import statistics
from pathlib import Path

S = Path(__file__).parent
F = json.loads((S / "rows-frozen.json").read_text())
C = json.loads((S / "rows-corrected.json").read_text())
SUM = {
    "frozen": json.loads((S / "sum-frozen/summary.json").read_text()),
    "corrected": json.loads((S / "sum-corrected/summary.json").read_text()),
}
PAIRS = json.loads((S / "pairs.json").read_text())
ROWS = {"frozen": F, "corrected": C}
VARIANTS = [("frozen", "As frozen"), ("corrected", "With the corrections")]

ARMS = [
    ("P0", "Bare"),
    ("P1", "Loose"),
    ("P1R", "Loose + reviewer"),
    ("P3", "Contract"),
    ("P2", "Checklist"),
    ("P4", "Team"),
]
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
}
e = html.escape


def cell(v, row, ticket):
    for r in ROWS[v]:
        if r["row"] == row and r["ticket"] == ticket:
            return r
    return None


def arm_rows(v, row):
    return [r for r in ROWS[v] if r["row"] == row]


def tip(r):
    bits = [f"{r['run']}"]
    if r.get("hidden"):
        h = r["hidden"]
        bits.append(f"hidden tests {h['passed']} of {h['passed'] + h['failed'] + h['errors']} passed")
    if r.get("traps"):
        bits.append("traps: " + ", ".join(r["traps"]))
    if r.get("false_claims"):
        bits.append("false claim: “" + (r["false_claims"][0].get("claim") or "")[:150] + "”")
    if r.get("rescues"):
        bits.append(f"rescued by the owner's reply ({r['rescues']})")
    if r.get("review"):
        d = r["review"].get("all_planted_bugs_caught") or {}
        if d:
            bits.append(f"planted bugs caught {d.get('caught')} of {d.get('planted')}")
    bits.append(f"{round((r['counted_tokens'] or 0) / 1000)}k tokens, {r['stops_total'] or 0} stops")
    return e(" · ".join(bits), quote=True)


def matrix(v, rows_spec, tickets):
    out = ['<div class="scroll"><table class="mx wide"><thead><tr><th>Arm</th>']
    for t, name, kind in tickets:
        out.append(
            f'<th class="c"><span class="tid">{t}</span><span class="tk">{e(name)}</span><span class="tkind">{e(kind)}</span></th>'
        )
    out.append('<th class="num">Trustworthy</th></tr></thead><tbody>')
    for row, label in rows_spec:
        got = [cell(v, row, t) for t, _, _ in tickets]
        n = sum(1 for r in got if r and r["trustworthy"])
        d = sum(1 for r in got if r)
        out.append(f'<tr><th scope="row">{label}</th>')
        for r in got:
            if not r:
                out.append('<td class="c"><span class="cell none">not run</span></td>')
            elif r["trustworthy"]:
                out.append(f'<td class="c"><span class="cell ok" tabindex="0" data-tip="{tip(r)}">✓</span></td>')
            else:
                why = " + ".join(WORD.get(k, k) for k in r["failed_checks"])
                out.append(
                    f'<td class="c"><span class="cell no" tabindex="0" data-tip="{tip(r)}">✗ <small>{e(why)}</small></span></td>'
                )
        out.append(f'<td class="num"><b>{n}</b> of {d}</td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


def both(fn):
    """Render fn(variant) once per grading; the toggle shows one."""
    return "".join(f'<div class="v v-{v}">{fn(v)}</div>' for v, _ in VARIANTS)


def bars(items, unit="", fmt=lambda x: f"{x:g}", mx=None, note=None):
    mx = mx or max(x for _, x, _ in items) or 1
    out = ['<div class="bars">']
    for label, x, t in items:
        w = max(0.0, min(100.0, 100.0 * x / mx))
        out.append(
            f'<div class="bar" tabindex="0" data-tip="{e(t, quote=True)}"><span class="bl">{label}</span>'
            f'<span class="bt"><span class="bf" style="width:{w:.1f}%"></span></span>'
            f'<span class="bv">{fmt(x)}{unit}</span></div>'
        )
    out.append("</div>")
    if note:
        out.append(f'<p class="small">{note}</p>')
    return "".join(out)


def mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.mean(xs) if xs else 0.0


def agg(v, row):
    rs = arm_rows(v, row)
    return {
        "n": len(rs),
        "tw": sum(1 for r in rs if r["trustworthy"]),
        "tokens": mean([r["counted_tokens"] for r in rs]),
        "usd": mean([r["list_price_usd"] for r in rs]),
        "words": mean([r["attention_words"] for r in rs]),
        "spec_words": mean([(r["attention_detail"] or {}).get("spec_words") for r in rs]),
        "stops": mean([r["stops_total"] or 0 for r in rs]),
        "routine": sum(r["stops_routine"] or 0 for r in rs),
        "warranted": sum(r["stops_warranted"] or 0 for r in rs),
        "rescues": sum(r["rescues"] or 0 for r in rs),
        "corrections": sum(r["correction_rounds"] or 0 for r in rs),
        "minutes": mean([(r["wall_seconds"] or 0) / 60 for r in rs]),
        "claims": sum(1 for r in rs if "no_false_claim" in r["failed_checks"]),
        "total_tokens": sum(r["counted_tokens"] or 0 for r in rs),
        "judge_tokens": sum(r["judge_tokens"] or 0 for r in rs),
    }


def label(a):
    return f'<b>{a}</b> <span class="an">{e(ARM_NAME[a])}</span>'


def chart_trust(v):
    items = []
    for a, _ in ARMS:
        g = agg(v, a)
        items.append((label(a), g["tw"], f"{a} {ARM_NAME[a]}: {g['tw']} of {g['n']} trustworthy"))
    return bars(items, fmt=lambda x: f"{x:g} of 8", mx=8)


def chart_cost(key, fmt, tipfmt):
    items = []
    for a, _ in ARMS:
        g = agg("frozen", a)
        items.append((label(a), g[key], f"{a} {ARM_NAME[a]}: {tipfmt(g)}"))
    return bars(items, fmt=fmt)


SPEC_ROWS = [
    ("P0/S0", "<b>P0</b> Bare · rough ticket (S0)"),
    ("P0", "<b>P0</b> Bare · standard ticket (S1)"),
    ("P0/S2", "<b>P0</b> Bare · full spec (S2)"),
    ("P0/S3", "<b>P0</b> Bare · spec + acceptance tests (S3)"),
    ("P1", "<b>P1</b> Loose · standard ticket (S1)"),
    ("P1/S3", "<b>P1</b> Loose · spec + acceptance tests (S3)"),
]
BUILD = TICKETS[:7]


def spec_agg(v, row):
    rs = [r for r in arm_rows(v, row) if r["ticket"] != "T8"]
    return {
        "n": len(rs),
        "tw": sum(1 for r in rs if r["trustworthy"]),
        "words": mean([r["attention_words"] for r in rs]),
        "spec": mean([(r["attention_detail"] or {}).get("spec_words") for r in rs]),
        "tokens": mean([r["counted_tokens"] for r in rs]),
    }


def chart_spec(v):
    items = []
    for row, lab in SPEC_ROWS:
        g = spec_agg(v, row)
        if g["n"]:
            items.append((lab, g["tw"], f"{g['tw']} of {g['n']} trustworthy on the seven build tickets"))
    return bars(items, fmt=lambda x: f"{x:g} of 7", mx=7)


def chart_spec_words():
    items = []
    for row, lab in SPEC_ROWS:
        g = spec_agg("frozen", row)
        if g["n"]:
            items.append(
                (lab, g["words"], f"{g['words']:.0f} words per ticket, of which the ticket itself is {g['spec']:.0f}")
            )
    return bars(items, fmt=lambda x: f"{x:,.0f}")


def judgement_table():
    out = [
        '<div class="scroll"><table class="wide"><thead><tr><th>Arm</th><th class="num">Run preferred</th><th class="num">Reference preferred</th>'
        '<th class="num">Level or not comparable</th><th class="num">Runs with a “poor” rating</th><th class="num">Big decisions left out of the brief</th>'
        '<th class="num">Quality 1–5</th></tr></thead><tbody>'
    ]
    for a, _ in ARMS:
        rs = [r for r in arm_rows("frozen", a) if r.get("judgement")]
        pref = [r["judgement"].get("preferred") for r in rs]
        poor = sum(1 for r in rs if "poor" in (r["judgement"].get("run") or {}).values())
        silent = sum(r["judgement"].get("silent_consequential_decisions") or 0 for r in rs)
        cons = sum(r["judgement"].get("consequential_decisions") or 0 for r in rs)
        q = [statistics.mean(r["quality"].values()) for r in arm_rows("frozen", a) if r.get("quality")]
        out.append(
            f"<tr><th scope=\"row\">{label(a)}</th><td class=\"num\">{pref.count('run')} of {len(rs)}</td>"
            f"<td class=\"num\">{pref.count('reference')}</td><td class=\"num\">{len(rs) - pref.count('run') - pref.count('reference')}</td>"
            f"<td class=\"num\">{poor} of {len(rs)}</td><td class=\"num\">{silent} of {cons}</td><td class=\"num\">{mean(q):.1f}</td></tr>"
        )
    out.append("</tbody></table></div>")
    return "".join(out)


TAGS = [
    "asked-or-guessed",
    "trusted-wrong-fact",
    "needless-stop",
    "over-built",
    "claimed-more",
    "skipped-claimed-check",
]


def tag_counts():
    rows = {}
    for r in F:
        for t in r.get("behaviour_tags") or []:
            name = t["tag"] + (":" + t["side"] if t.get("side") else "")
            rows.setdefault(name, {}).setdefault(r["arm"], []).append((r["run"], t.get("quote", "")))
    return rows


TAG_WORDS = {
    "asked-or-guessed:asked": "Asked the owner when the ticket left a choice open",
    "asked-or-guessed:guessed": "Guessed when the ticket left a choice open",
    "trusted-wrong-fact": "Took a wrong statement in the ticket as true",
    "needless-stop": "Stopped for something it could have decided",
    "over-built": "Built more than was asked",
    "claimed-more": "Claimed more than it showed",
    "skipped-claimed-check": "Said it ran a check it did not run",
}


def tag_table():
    rows = tag_counts()
    out = ['<div class="scroll"><table class="wide"><thead><tr><th>Behaviour (Judge)</th>']
    out += [f'<th class="num">{a}</th>' for a, _ in ARMS]
    out.append('<th class="num">All runs</th></tr></thead><tbody>')
    for name in sorted(rows, key=lambda k: -sum(len(x) for x in rows[k].values())):
        total = sum(len(x) for x in rows[name].values())
        out.append(f'<tr><th scope="row">{e(TAG_WORDS.get(name, name))}</th>')
        for a, _ in ARMS:
            xs = rows[name].get(a, [])
            t = e(" · ".join(f"{run}: “{q[:90]}”" for run, q in xs[:3]), quote=True)
            out.append(
                f'<td class="num">{"<span tabindex=0 data-tip=" + chr(34) + t + chr(34) + ">" + str(len(xs)) + "</span>" if xs else "–"}</td>'
            )
        out.append(f'<td class="num"><b>{total}</b></td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


def pairs_html():
    out = []
    names = ["does", "approach", "choices", "beyond", "size"]
    heads = {
        "does": "What changes for users",
        "approach": "How",
        "choices": "Choices it made",
        "beyond": "Beyond the ticket",
        "size": "Size",
    }
    for i, (run, p) in enumerate(PAIRS.items(), 1):
        d = p["describe"]
        out.append(
            f'<section class="pair panel" data-pair="{i}" data-judge="{e(str(p["judge_preferred_side"]))}" data-run="{p["run_is"]}">'
        )
        out.append(f'<h3>Pair {i} · {e(p["ticket_title"])}</h3><div class="grid2 ab">')
        for side in "AB":
            out.append(f'<div class="side"><div class="sl">Change {side}</div><dl>')
            for k in names:
                out.append(f"<dt>{heads[k]}</dt><dd>{e(d[side].get(k, ''))}</dd>")
            out.append("</dl></div>")
        out.append("</div>")
        if d.get("differences"):
            out.append(
                '<div class="scroll"><table class="wide diffs"><thead><tr><th>Where they differ</th><th>A</th><th>B</th></tr></thead><tbody>'
            )
            for x in d["differences"]:
                out.append(
                    f"<tr><td>{e(x.get('point', ''))}</td><td>{e(x.get('A', ''))}</td><td>{e(x.get('B', ''))}</td></tr>"
                )
            out.append("</tbody></table></div>")
        out.append(
            f'<details class="code" data-diff="{i}"><summary>Read the two changes as code</summary><div class="grid2">'
            f'<pre id="diff-{i}-A">Loading…</pre><pre id="diff-{i}-B">Loading…</pre></div></details>'
        )
        out.append('<fieldset class="pick"><legend>Which would you rather merge?</legend>')
        for val, lab in (("A", "A"), ("B", "B"), ("no real difference", "No real difference")):
            out.append(f'<label><input type="radio" name="pair{i}" id="pair{i}-{val[0]}" value="{val}"> {lab}</label>')
        out.append("</fieldset>")
        who = {"A": "A", "B": "B"}.get(p["judge_preferred_side"], p["judge_preferred_side"])
        made = f'A was the {"run" if p["run_is"] == "A" else "reference fix"}; B was the {"run" if p["run_is"] == "B" else "reference fix"} ({run}).'
        out.append(
            f'<div class="reveal" hidden><p><b>The judge picked {e(str(who))}.</b> <span class="agree"></span></p>'
            f'<p class="small">Its reason: {e(p["judge_reason"] or "")}</p><p class="small">{made}</p></div>'
        )
        out.append("</section>")
    return "".join(out)


def build():
    import page_text as T

    ctx = {
        "matrix": both(lambda v: matrix(v, [(a, label(a)) for a, _ in ARMS], TICKETS)),
        "chart_trust": both(chart_trust),
        "matrix_spec": both(lambda v: matrix(v, SPEC_ROWS, BUILD)),
        "chart_spec": both(chart_spec),
        "chart_spec_words": chart_spec_words(),
        "chart_tokens": chart_cost(
            "tokens",
            lambda x: f"{x / 1000:,.0f}k",
            lambda g: f"{g['tokens']:,.0f} tokens per run, ${g['usd']:.2f} at list price",
        ),
        "chart_words": chart_cost(
            "words",
            lambda x: f"{x:,.0f}",
            lambda g: f"{g['words']:,.0f} words per ticket: ticket, stops, pull request text and final message",
        ),
        "chart_stops": chart_cost(
            "stops",
            lambda x: f"{x:.1f}",
            lambda g: f"{g['routine']} routine and {g['warranted']} warranted stops over 8 tickets",
        ),
        "chart_minutes": chart_cost(
            "minutes", lambda x: f"{x:.0f} min", lambda g: f"{g['minutes']:.1f} minutes per run"
        ),
        "judgement_table": judgement_table(),
        "tag_table": tag_table(),
        "pairs": pairs_html(),
        "toggle": '<div class="toggle" role="group" aria-label="Grading">'
        + "".join(
            f'<button type="button" data-v="{v}" aria-pressed="{"true" if i == 0 else "false"}">{lab}</button>'
            for i, (v, lab) in enumerate(VARIANTS)
        )
        + "</div>",
    }
    body = T.PAGE
    for k, val in ctx.items():
        body = body.replace("{{" + k + "}}", val)
    pj = {str(i): {"judge": p["judge_preferred_side"]} for i, p in enumerate(PAIRS.values(), 1)}
    body = body.replace("{{pairs_json}}", json.dumps(pj))
    prs = {r["run"]: r["pr"] for r in F}
    body = __import__("re").sub(
        r"\{\{pr:([\w-]+)\}\}",
        lambda m: f'<a href="https://github.com/Natenc12/gct-lab/pull/{prs[m.group(1)]}">pull request {prs[m.group(1)]}</a>',
        body,
    )
    missing = [m for m in __import__("re").findall(r"\{\{(\w+)\}\}", body)]
    assert not missing, missing
    (S / "factory-lab-stage1.html").write_text((T.HEAD + body + T.SCRIPT).replace("\ufffd", "&#xFFFD;"))
    (S / "pair-diffs.json").write_text(json.dumps({str(i): p["diff"] for i, p in enumerate(PAIRS.values(), 1)}))
    print("wrote", S / "factory-lab-stage1.html", (S / "factory-lab-stage1.html").stat().st_size, "bytes")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "facts":
        for v, _ in VARIANTS:
            print("==", v, json.dumps(SUM[v]["decision"])[:900])
            for a, _ in ARMS:
                print(a, {k: (round(x, 2) if isinstance(x, float) else x) for k, x in agg(v, a).items()})
            for row, _ in SPEC_ROWS:
                print(row, {k: (round(x, 1) if isinstance(x, float) else x) for k, x in spec_agg(v, row).items()})
    else:
        build()
