# ruff: noqa: F821, B023
# (names come from build_page5.py's globals; the lambdas are called inside the same loop pass)
# page5_fill.py: the figures the stage 4 page body asks for. Executed by build_page5.py with its globals.
def _n(v, row, pred, cbs=("hono", "sqlglot")):
    return sum(1 for r in live(v) if r["row"] == row and r["cb"] in cbs and pred(r))


def _judges():
    out = []
    for row, name, _ in ROWS:
        ag = both(
            lambda v: "{} of {}".format(_n(v, row, lambda r: r["agree"]), _n(v, row, lambda r: r["agree"] is not None)),
            fmt=None,
        )
        out.append(
            f"<tr><th><b>{e(name)}</b></th>"
            f'<td class="num">{both(lambda v: per8(v, row))}</td>'
            f'<td class="num">{both(lambda v: per8(v, row, "tw2"))}</td>'
            f'<td class="num">{both(lambda v: per8(v, row, "twc"))}</td>'
            f'<td class="num">{ag}</td></tr>'
        )
    return "".join(out)


def _skills():
    names = [
        "check-the-ask",
        "prove-each-claim",
        "test-that-bites",
        "fresh-eyes-review",
        "stay-in-scope",
        "find-the-cause",
    ]
    out = []
    for s in names:
        tds = "".join(
            f'<td class="num">{_n("frozen", row, lambda r: s in r["skills"])} of {_n("frozen", row, lambda r: True)}</td>'
            for row, _, _ in ROWS
        )
        pointed = ' <span class="an">(pointed to)</span>' if s in names[:2] else ""
        out.append(f"<tr><th><code>{s}</code>{pointed}</th>{tds}</tr>")
    return "".join(out)


def _split():
    d = SUM["frozen"]["decision"]["rows"]["P6P"]
    n = d["runs"]
    f, o = d["by_model"]["claude-fable-5-2"], d["by_model"]["claude-opus-5-5"]
    return f["list_price_usd"] / n, o["list_price_usd"] / n, f["counted_tokens"] / n, o["counted_tokens"] / n


def _extra_judges():
    t = 0
    for r in DATA["corrected"]:
        if r["workers"]:
            h = ROOTS["corrected"] / f"stage-4-{r['cb']}" / r["run"] / "harness"
            for f in (
                "judge-honesty.json",
                "judge-honesty-2.json",
                "judge-claim-severity.json",
                "judge-honesty-check.json",
            ):
                t += ((jload(h / f) or {}).get("usage") or {}).get("counted", 0) or 0
    return t


_lead_usd, _work_usd, _lead_tok, _work_tok = _split()
_runs_tok = sum(r["tokens"] for r in DATA["frozen"])
_judge_tok = sum(r["judge_tokens"] for r in DATA["frozen"])
_reply_tok = sum(r["reply_tokens"] for r in DATA["frozen"])
_extra = _extra_judges()
_hidden_ok = sum(1 for r in live("frozen") if "hidden_tests_pass" not in r["failed"])
_ordinary = [r for r in live("frozen") if r["ticket"] not in ("T7", "T8")]

FILL = {
    "matrix_hono": matrix("hono"),
    "matrix_sqlglot": matrix("sqlglot"),
    "chart_trust": chart_trust(("hono", "sqlglot")),
    "chart_trust_hono": chart_trust(("hono",)),
    "chart_trust_sqlglot": chart_trust(("sqlglot",)),
    "chart_usd": chart_usd(),
    "chart_minutes": chart_cell(lambda r: r["secs"] / 60, lambda x: f"{x:.0f}", "minutes a run"),
    "chart_words": chart_cell(lambda r: r["words"], lambda x: f"{x:,.0f}", "words to read per ticket"),
    "chart_stops": chart_cell(lambda r: r["stops_total"], lambda x: f"{x:.2f}", "stops per ticket"),
    "judges": _judges(),
    "skills": _skills(),
    "p6p": both(lambda v: per8(v, "P6P")),
    "p6p_hono": both(lambda v: per8(v, "P6P", cbs=("hono",))),
    "p6p_sqlglot": both(lambda v: per8(v, "P6P", cbs=("sqlglot",))),
    "p6p_tw": both(lambda v: str(_n(v, "P6P", lambda r: r["tw"])), fmt=None),
    "usd_p5p": f"{usd('P5P'):.2f}",
    "usd_p5pf": f"{usd('P5PF'):.2f}",
    "usd_p6p": f"{usd('P6P'):.2f}",
    "ratio_f": f"{usd('P5PF') / usd('P5P'):.1f}",
    "ratio_l": f"{usd('P6P') / usd('P5P'):.1f}",
    "lead_usd": f"{_lead_usd:.2f}",
    "work_usd": f"{_work_usd:.2f}",
    "workers": str(sum(r["workers"] for r in live("frozen") if r["row"] == "P6P")),
    "min_p5p": f"{cellavg('frozen', 'P5P', lambda r: r['secs'] / 60):.0f}",
    "min_p5pf": f"{cellavg('frozen', 'P5PF', lambda r: r['secs'] / 60):.0f}",
    "min_p6p": f"{cellavg('frozen', 'P6P', lambda r: r['secs'] / 60):.0f}",
    "hidden_ok": str(_hidden_ok),
    "ordinary_n": str(len(_ordinary)),
    "ordinary_ok": str(sum(1 for r in _ordinary if "hidden_tests_pass" not in r["failed"])),
    "runs_m": f"{_runs_tok / 1e6:.1f}M",
    "reply_m": f"{_reply_tok / 1e6:.2f}M",
    "judge_m": f"{_judge_tok / 1e6:.1f}M",
    "extra_m": f"{_extra / 1e6:.1f}M",
    "total_m": f"{(_runs_tok + _reply_tok + _judge_tok + _extra + 197942) / 1e6:.0f}M",
    "usd_runs": f"{sum(r['usd'] for r in DATA['frozen'] if r['row'] != 'P6P') + SUM['frozen']['decision']['rows']['P6P']['by_model']['claude-fable-5-2']['list_price_usd'] + SUM['frozen']['decision']['rows']['P6P']['by_model']['claude-opus-5-5']['list_price_usd']:.0f}",
}
