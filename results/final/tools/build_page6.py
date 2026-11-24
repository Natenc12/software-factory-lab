"""build_page6.py: the final results page. Every charted number is read from results/final/questions.json
(made by `python3 -m grader.questions`) by its label, or from results/final/profiles.json; the text
lives in page6_body.html. Run from anywhere: `python3 build_page6.py <repo root>` writes
factory-lab-final.html next to this file."""

import html
import json
import sys
from pathlib import Path

S = Path(__file__).parent
REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
Q = {q["id"]: q for q in json.loads((REPO / "results/final/questions.json").read_text())["questions"]}
e = html.escape


def num(qid, label, reading="current", grading="corrected"):
    for n in Q[qid]["numbers"]:
        if n["label"] == label and n["reading"] == reading and n["grading"] == grading:
            return n["value"]
    raise KeyError((qid, label, reading, grading))


def bars(items, fmt, mx=None):
    mx = mx or max(x for _, x, _ in items) or 1
    out = []
    for label, x, tip in items:
        out.append(
            f'<div class="bar" tabindex="0" data-tip="{e(tip, quote=True)}"><span class="bl">{e(label)}</span>'
            f'<span class="bt"><span class="bf" style="width:{100 * x / mx:.1f}%"></span></span>'
            f'<span class="bv">{fmt(x)}</span></div>'
        )
    return '<div class="bars">' + "".join(out) + "</div>"


def trust(pairs, qid, suffix=" trustworthy per 8", mx=8):
    items = []
    for name, key in pairs:
        cur = num(qid, key + suffix)
        try:
            sec = num(qid, key + suffix, "second")
            tip = f"{name}: {cur:.2f} of 8 by the current rules, {sec:.2f} on the second reading"
        except KeyError:
            tip = f"{name}: {cur:.2f} of 8 by the current rules"
        items.append((name, cur, tip))
    return bars(items, lambda x: f"{x:.1f}", mx)


def one(v):
    return f"{v:.1f}"


K = 1000
FILL = {
    "q1": trust([("Ticket only, no guide", "P0"), ("One-page guide", "P1")], "Q1"),
    "q2_trust": trust(
        [
            ("One-page guide", "P1"),
            ("Guide + fresh reviewer", "P1R"),
            ("Contract first", "P3"),
            ("Long checklist", "P2"),
        ],
        "Q2",
    ),
    "q2_tokens": bars(
        [
            (
                n,
                num("Q2", k + " counted tokens per run") / K,
                f"{n}: {num('Q2', k + ' counted tokens per run'):,.0f} counted tokens a run",
            )
            for n, k in [
                ("One-page guide", "P1"),
                ("Guide + fresh reviewer", "P1R"),
                ("Contract first", "P3"),
                ("Long checklist", "P2"),
            ]
        ],
        lambda x: f"{x:.0f}k",
    ),
    "q2_stops": bars(
        [
            (
                n,
                num("Q2", k + " stops per run"),
                f"{n}: stopped for the owner {num('Q2', k + ' stops per run'):.2f} times a run; the owner read {num('Q2', k + ' owner words per ticket'):,.0f} words a ticket",
            )
            for n, k in [
                ("One-page guide", "P1"),
                ("Guide + fresh reviewer", "P1R"),
                ("Contract first", "P3"),
                ("Long checklist", "P2"),
            ]
        ],
        lambda x: f"{x:.2f}",
    ),
    "q3": bars(
        [
            (
                "One-page guide (control)",
                num("Q3", "P1 trustworthy per 8 (control)"),
                "The guide alone on the eight stage 2 tickets",
            )
        ]
        + [
            (
                n,
                num("Q3", k + " trustworthy per 8"),
                f"{n}: improves {num('Q3', k + ' improves, of 3')} of the 3 measures at {num('Q3', k + ' cost ratio against P1'):.2f} times the guide's cost; goes in: {'yes' if num('Q3', k + ' goes in (stage 2)') else 'no'}",
            )
            for n, k in [
                ("+ Tests first", "P1T"),
                ("+ Small slices", "P1L"),
                ("+ Architecture brief", "P1A"),
                ("+ Skills, left to choose", "P5"),
                ("+ Skills, two pointed to", "P5P"),
            ]
        ],
        one,
        8,
    ),
    "q3b": bars(
        [
            (
                n,
                num("Q3", k + " trustworthy per 8 (with the tie-break round)"),
                f"{n}: over all its runs on the eight tickets, tie-break round included",
            )
            for n, k in [("Architecture brief", "P1A"), ("Skills, two pointed to", "P5P"), ("Both together", "P5PA")]
        ],
        one,
        8,
    ),
    "q4_trust": bars(
        [
            ("One-page guide", num("Q4", "P1 trustworthy per 8 (stage 1)"), "Stage 1, one run per ticket, corrected"),
            (
                "Team of five roles",
                num("Q4", "P4 trustworthy per 8 (stage 1, one run per ticket)"),
                f"Stage 1, one run per ticket, corrected; as frozen {num('Q4', 'P4 trustworthy per 8 (stage 1, as frozen)', grading='as frozen'):.0f}",
            ),
        ],
        one,
        8,
    ),
    "q4_tokens": bars(
        [
            (
                "One-page guide",
                num("Q4", "P1 counted tokens per run") / K,
                f"{num('Q4', 'P1 counted tokens per run'):,.0f} counted tokens a run",
            ),
            (
                "Team of five roles",
                num("Q4", "P4 counted tokens per run") / K,
                f"{num('Q4', 'P4 counted tokens per run'):,.0f} counted tokens a run",
            ),
        ],
        lambda x: f"{x:.0f}k",
    ),
    "q4_ratio": f"{num('Q4', 'P4 counted tokens per run') / num('Q4', 'P1 counted tokens per run'):.1f}",
    "q5_trust": bars(
        [
            (
                "Opus alone",
                num("Q5", "P5P (Opus) trustworthy per 8"),
                "Opus 5.5 with the guide and pointed skills; 7.0 on the second reading",
            ),
            (
                "Fable alone",
                num("Q5", "P5PF (Fable) trustworthy per 8"),
                "Fable 5.2 with the same files; 7.0 on the second reading",
            ),
            (
                "Fable leading Opus",
                num("Q5", "P6P (Fable leading Opus) trustworthy per 8"),
                f"Corrected; as frozen {num('Q5', 'P6P trustworthy per 8 (as frozen)', grading='as frozen'):.1f}. Reported, decides nothing",
            ),
        ],
        lambda x: f"{x:g}",
        8,
    ),
    "q5_usd": bars(
        [
            (
                n,
                num("Q5", k + " list price per run, USD"),
                f"{n}: ${num('Q5', k + ' list price per run, USD'):.2f} a run at list price, {num('Q5', k + ' counted tokens per run'):,.0f} counted tokens",
            )
            for n, k in [("Opus alone", "P5P"), ("Fable alone", "P5PF"), ("Fable leading Opus", "P6P")]
        ],
        lambda x: f"${x:.2f}",
    ),
    "q6_words": bars(
        [
            (
                "Guide, standard ticket",
                num("Q6", "S2: best process arm owner words per ticket"),
                "The best process arm on the standard ticket: words the owner reads per ticket, ticket included",
            ),
            (
                "No guide, full spec",
                num("Q6", "S2: P0 owner words per ticket, spec included"),
                "A bare run on the full spec: words the owner reads per ticket, spec included",
            ),
        ],
        lambda x: f"{x:,.0f}",
    ),
    "q6_p0": one(num("Q6", "S2: P0 trustworthy per 8")),
    "q6_best": one(num("Q6", "S2: best process arm on S1, trustworthy per 8")),
    "x": bars(
        [
            (
                "Your app (gct)",
                num("cross-check", "P5P trustworthy per 8 on gct (stage 2 and the tie-break round)"),
                "Stage 2 and the tie-break round, eight tickets, three runs each",
            ),
            (
                "Hono",
                num("cross-check", "P5P trustworthy per 8 on hono"),
                "Stage 4, eight tickets, two runs each; the best row there was also 7.5",
            ),
            (
                "sqlglot",
                num("cross-check", "P5P trustworthy per 8 on sqlglot"),
                "Stage 4, eight tickets, two runs each; the best row there was also 6.0",
            ),
        ],
        one,
        8,
    ),
    "q1_margin": one(num("Q1", "margin over P0, trustworthy per 8")),
}

body = (S / "page6_body.html").read_text()
for k, v in FILL.items():
    body = body.replace("{{" + k + "}}", str(v))
assert "{{" not in body, body[body.index("{{") : body.index("{{") + 60]
head = '<title>Factory Lab Final Report</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
page = head + (S / "page-css.txt").read_text() + body + (S / "page-js.txt").read_text()
(S / "factory-lab-final.html").write_text(page)
print("wrote", S / "factory-lab-final.html", len(page))
