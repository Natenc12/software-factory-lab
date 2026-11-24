"""The numbers that answer the charter's questions, for the final results page.

    python -m grader.questions [--out results/final/questions.json]

Nothing is recomputed: every number is read from a committed summary (results/<stage>/.../summary.json)
by its JSON path, and the output names the file, the path, the reading and the grading for each. The
only derived figures are the cross-check's gaps to the best row on each codebase, marked `derived`
with the numbers they come from.

Shape of the output:

    {"made_by", "time", "note", "readings": {...}, "gradings": {...},
     "questions": [
       {"id": "Q1", "question", "decides", "rule",
        "answer": {"text", "value", "source", "path", "reading", "grading"},
        "numbers": [{"label", "value", "source", "path", "reading", "grading", "derived"?}]}]}

`reading` is "current" (the deciding reading) or "second" (the second reading, reported beside);
`grading` is "corrected" or "as frozen". A number that exists under both readings appears twice.
"""

import argparse
import json
import sys
from pathlib import Path

from grader.common import LAB_ROOT, now_iso, write_json

SECOND = {"decision": "decision_second_reading", "per_row": "per_row_second_reading",
          "against_control": "against_control_second_reading"}  # fmt: skip
S1F, S1C, S1X = (
    "results/stage-1/as-frozen/summary.json",
    "results/stage-1/corrected/summary.json",
    "results/stage-1-confirm/summary.json",
)
S2F, S2C = "results/stage-2/as-frozen/summary.json", "results/stage-2/corrected/summary.json"
S2B, S2BP = "results/stage-2b/summary/summary.json", "results/stage-2b/summary-against-p5p/summary.json"
S4F, S4C = "results/stage-4/as-frozen/summary.json", "results/stage-4/corrected/summary.json"
GRADING = {S1F: "as frozen", S1C: "corrected", S1X: "corrected", S2F: "as frozen", S2C: "corrected",
           S2B: "corrected", S2BP: "corrected", S4F: "as frozen", S4C: "corrected"}  # fmt: skip

# (label, file, path, readings): readings "both" gives the current and the second reading.
QUESTIONS = [
    {
        "id": "Q1",
        "question": "Does process help at all, or is Opus 5.5 good enough with just the ticket?",
        "decides": "Whether to keep building the pipeline",
        "rule": "Process is needed only if the best process arm beats P0 by more than one trustworthy PR per 8 "
        "tickets, or P0 needs more rescues.",
        "answer": ("process is needed", S1X, "decision.q1_process_needed.answer"),
        "numbers": [
            ("process needed (three repeats)", S1X, "decision.q1_process_needed.answer", "both"),
            ("best process arm", S1X, "decision.q1_process_needed.best_process", "both"),
            ("margin over P0, trustworthy per 8", S1X, "decision.q1_process_needed.margin_per_8", "both"),
            ("P0 trustworthy per 8", S1X, "per_row.P0.trustworthy_per_8", "both"),
            ("P1 trustworthy per 8", S1X, "per_row.P1.trustworthy_per_8", "both"),
            ("P0 rescues per 8", S1X, "decision.q1_process_needed.p0_rescues_per_8", "both"),
            ("best process arm rescues per 8", S1X, "decision.q1_process_needed.best_rescues_per_8", "both"),
            ("margin over P0, stage 1 alone", S1C, "decision.q1_process_needed.margin_per_8", "current"),
            ("margin over P0, stage 1 alone", S1F, "decision.q1_process_needed.margin_per_8", "current"),
        ],
    },
    {
        "id": "Q2",
        "question": "Loose or rigorous, and if rigorous, which shape?",
        "decides": "How heavy the checklist should be",
        "rule": "Ties go to the simpler arm: within one trustworthy PR per 8 of the leader counts as tied; order "
        "P0, P1, P1R, P3, P2, P4; then fewer owner stops, then lower cost.",
        "answer": (
            "the loose guide (P1) wins; P1R and P3 are tied with it and P1 is simpler",
            S1X,
            "decision.best_process.pick",
        ),
        "numbers": [
            ("best process arm", S1X, "decision.best_process.pick", "both"),
            ("tied within one of the leader", S1X, "decision.best_process.tied_within_one", "both"),
            *[
                (f"{a} trustworthy per 8", S1X, f"per_row.{a}.trustworthy_per_8", "both")
                for a in ("P1", "P1R", "P3", "P2")
            ],
            *[
                (f"{a} counted tokens per run", S1X, f"per_row.{a}.counted_tokens_avg", "current")
                for a in ("P1", "P1R", "P3", "P2")
            ],
            *[
                (f"{a} owner words per ticket", S1X, f"per_row.{a}.attention_words_avg", "current")
                for a in ("P1", "P1R", "P3", "P2")
            ],
            *[(f"{a} stops per run", S1X, f"per_row.{a}.stops_avg", "current") for a in ("P1", "P1R", "P3", "P2")],
        ],
    },
    {
        "id": "Q3",
        "question": "Do engineering habits matter: tests first, small slices, an architecture brief?",
        "decides": "Whether to write them into the checklist",
        "rule": "A habit add-on goes in only if it improves at least two of: trustworthy rate, quality score, "
        "rescues, without adding more than 30% to cost.",
        "answer": (
            "the pointed skills (P5P) go in; tests first, small slices and pure-discretion skills stay out; "
            "P5P stays the base over P5PA",
            S2C,
            "decision.addons.P5P.answer",
        ),  # fmt: skip
        "numbers": [
            *[
                (f"{a} goes in (stage 2)", S2C, f"decision.addons.{a}.answer", "both")
                for a in ("P1T", "P1L", "P1A", "P5", "P5P")
            ],
            *[
                (f"{a} goes in (stage 2, as frozen)", S2F, f"decision.addons.{a}.answer", "current")
                for a in ("P1T", "P1L", "P1A", "P5", "P5P")
            ],
            *[
                (f"{a} improves, of 3", S2C, f"decision.addons.{a}.improved_count", "current")
                for a in ("P1T", "P1L", "P1A", "P5", "P5P")
            ],
            *[
                (f"{a} cost ratio against P1", S2C, f"decision.addons.{a}.cost_ratio", "current")
                for a in ("P1T", "P1L", "P1A", "P5", "P5P")
            ],
            *[
                (f"{a} trustworthy per 8", S2C, f"decision.addons.{a}.addon.trustworthy_per_8", "both")
                for a in ("P1T", "P1L", "P1A", "P5", "P5P")
            ],
            ("P1 trustworthy per 8 (control)", S2C, "decision.addons.P5P.p1.trustworthy_per_8", "both"),
            *[
                (f"{a} goes in (with the tie-break round)", S2B, f"decision.addons.{a}.answer", "both")
                for a in ("P1A", "P5P", "P5PA")
            ],
            *[
                (
                    f"{a} trustworthy per 8 (with the tie-break round)",
                    S2B,
                    f"decision.addons.{a}.addon.trustworthy_per_8",
                    "both",
                )
                for a in ("P1A", "P5P", "P5PA")
            ],
            (
                "P5PA against P5P: trustworthy per 8 difference",
                S2BP,
                "against_control.plain_facts.P5PA.trustworthy_per_8_difference",
                "both",
            ),
            ("P5PA against P5P: cost ratio", S2BP, "against_control.plain_facts.P5PA.cost_ratio", "both"),
        ],
    },
    {
        "id": "Q4",
        "question": "Does a team of role agents beat one agent with a checklist?",
        "decides": "Whether to build a factory of roles",
        "rule": "Ties go to the simpler arm (P4 is the least simple). Stage 1 only: P4 was not in the confirm round.",
        "answer": (
            "no: the team (P4) is tied with the leader and costs most, so the simpler arm wins",
            S1C,
            "decision.best_process.pick",
        ),
        "numbers": [
            ("P4 trustworthy per 8 (stage 1, one run per ticket)", S1C, "per_row.P4.trustworthy_per_8", "current"),
            ("P4 trustworthy per 8 (stage 1, as frozen)", S1F, "per_row.P4.trustworthy_per_8", "current"),
            ("P1 trustworthy per 8 (stage 1)", S1C, "per_row.P1.trustworthy_per_8", "current"),
            ("tied within one of the leader (stage 1)", S1C, "decision.best_process.tied_within_one", "current"),
            ("P4 counted tokens per run", S1C, "per_row.P4.counted_tokens_avg", "current"),
            ("P1 counted tokens per run", S1C, "per_row.P1.counted_tokens_avg", "current"),
            ("P4 stops per run", S1C, "per_row.P4.stops_avg", "current"),
            ("P4 rescues per 8", S1C, "per_row.P4.rescues_per_8", "current"),
        ],
    },
    {
        "id": "Q5",
        "question": "Is Fable 5.2 worth its extra cost over Opus 5.5?",
        "decides": "Which model builds, and which one checks",
        "rule": "Fable builds only if it gains at least one trustworthy PR per 8 tickets, or needs at least 30% "
        "fewer correction rounds; decided on both stage 4 codebases pooled.",
        "answer": ("Opus builds", S4C, "decision.fable_builds"),
        "numbers": [
            ("Fable builds", S4C, "decision.fable_builds", "both"),
            ("Fable builds (as frozen)", S4F, "decision.fable_builds", "both"),
            ("Fable's gain, trustworthy per 8", S4C, "decision.trustworthy_gain_per_8", "both"),
            ("P5P (Opus) trustworthy per 8", S4C, "decision.rows.P5P.trustworthy_per_8", "both"),
            ("P5PF (Fable) trustworthy per 8", S4C, "decision.rows.P5PF.trustworthy_per_8", "both"),
            ("P6P (Fable leading Opus) trustworthy per 8", S4C, "decision.rows.P6P.trustworthy_per_8", "both"),
            ("P6P trustworthy per 8 (as frozen)", S4F, "decision.rows.P6P.trustworthy_per_8", "current"),
            ("correction rounds note", S4C, "decision.corrections_note", "current"),
            ("list price ratio per run, Fable over Opus", S4C, "decision.list_price_ratio_per_run", "current"),
            *[
                (f"{r} list price per run, USD", S4C, f"decision.rows.{r}.list_price_usd_per_run", "current")
                for r in ("P5P", "P5PF", "P6P")
            ],
            *[
                (f"{r} counted tokens per run", S4C, f"decision.rows.{r}.counted_tokens_per_run", "current")
                for r in ("P5P", "P5PF", "P6P")
            ],
            *[
                (
                    f"Fable's gain on {cb}, trustworthy per 8",
                    S4C,
                    f"decision.per_codebase.{cb}.trustworthy_gain_per_8",
                    "both",
                )
                for cb in ("hono", "sqlglot")
            ],
        ],
    },
    {
        "id": "Q6",
        "question": "Does a fully specified ticket remove the need for a pipeline?",
        "decides": "Where to spend effort: on the ticket before the run, or on the process during it",
        "rule": "A full spec replaces the pipeline only if a bare run on S2 or S3 comes within one trustworthy PR "
        "of the best process arm on S1, and the owner's total attention, spec included, is no higher.",
        "answer": (
            "no: within one, but the owner's attention is higher",
            S1C,
            "decision.q6_full_spec_replaces_pipeline.answer",
        ),
        "numbers": [
            ("full spec replaces the pipeline", S1C, "decision.q6_full_spec_replaces_pipeline.answer", "current"),
            (
                "full spec replaces the pipeline (as frozen)",
                S1F,
                "decision.q6_full_spec_replaces_pipeline.answer",
                "current",
            ),
            *[
                (f"{lv}: {label}", S1C, f"decision.q6_full_spec_replaces_pipeline.levels.{lv}.{key}", "current")
                for lv in ("S2", "S3")
                for key, label in (
                    ("p0_per_8", "P0 trustworthy per 8"),
                    ("best_process_per_8", "best process arm on S1, trustworthy per 8"),
                    ("within_one", "within one"),
                    ("p0_attention_avg", "P0 owner words per ticket, spec included"),
                    ("best_process_attention_avg", "best process arm owner words per ticket"),
                    ("attention_no_higher", "attention no higher"),
                    ("shared_tickets", "tickets compared"),
                )  # fmt: skip
            ],
            (
                "P1 on S3, trustworthy per 8 (reported, no rule)",
                S1C,
                "decision.q6_full_spec_replaces_pipeline.best_process_on_s3.per_8",
                "current",
            ),
        ],
    },
]


def at(doc: dict, path: str):
    x = doc
    for part in path.split("."):
        if not isinstance(x, dict) or part not in x:
            raise KeyError(path)
        x = x[part]
    return x


def second_path(path: str) -> str:
    head, _, rest = path.partition(".")
    return f"{SECOND[head]}.{rest}" if head in SECOND else path


class Reader:
    def __init__(self, root: Path):
        self.root, self.docs = root, {}

    def doc(self, f: str) -> dict:
        if f not in self.docs:
            self.docs[f] = json.loads((self.root / f).read_text(encoding="utf-8"))
        return self.docs[f]

    def number(self, label, f, path, reading) -> dict:
        p = path if reading == "current" else second_path(path)
        return {"label": label, "value": at(self.doc(f), p), "source": f, "path": p, "reading": reading,
                "grading": GRADING[f]}  # fmt: skip


def cross_check(rd: Reader) -> dict:
    """Charter: the winner is confirmed if it stays within one trustworthy PR of the best arm on each extra
    codebase. The winner of stages 1 to 2b is P5P (the pointed skills on the loose guide), on Opus."""
    numbers = [
        rd.number(
            "P5P trustworthy per 8 on gct (stage 2 and the tie-break round)",
            S2B,
            "decision.addons.P5P.addon.trustworthy_per_8",
            "current",
        ),
    ]
    for reading in ("current", "second"):
        for cb in ("hono", "sqlglot"):
            rows = {}
            for r in ("P5P", "P5PF", "P6P"):
                n = rd.number(
                    f"{r} trustworthy per 8 on {cb}",
                    S4C,
                    f"decision.per_codebase.{cb}.rows.{r}.trustworthy_per_8",
                    reading,
                )
                rows[r] = n["value"]
                numbers.append(n)
            best = max(rows.values())
            numbers.append(
                {
                    "label": f"P5P gap to the best row on {cb}, trustworthy per 8",
                    "value": round(best - rows["P5P"], 3),
                    "derived": f"best of P5P, P5PF, P6P ({best}) minus P5P ({rows['P5P']})",
                    "source": S4C,
                    "path": f"{'decision' if reading == 'current' else 'decision_second_reading'}.per_codebase.{cb}.rows",
                    "reading": reading,
                    "grading": GRADING[S4C],
                }
            )
    gaps = [n["value"] for n in numbers if n.get("derived") and n["reading"] == "current"]
    return {
        "id": "cross-check",
        "question": "Does the winner still win on a codebase other than GCT?",
        "decides": "Whether the way of working travels",
        "rule": "Generalising (stage 4): the winner is confirmed if it stays within one trustworthy PR of the best "
        "arm on each extra codebase.",
        "answer": {
            "text": "confirmed: P5P is within one of the best row on Hono and on sqlglot"
            if all(g <= 1 for g in gaps)
            else "not confirmed",  # fmt: skip
            "value": all(g <= 1 for g in gaps),
            "source": S4C,
            "path": "decision.per_codebase.*.rows",
            "reading": "current",
            "grading": GRADING[S4C],
            "derived": "every P5P gap to the best row, current reading, is 1.0 or less",
        },
        "numbers": numbers,
    }


def build(root: Path | None = None) -> dict:
    rd = Reader(Path(root or LAB_ROOT))
    out = []
    for q in QUESTIONS:
        numbers = []
        for label, f, path, readings in q["numbers"]:
            for reading in ("current", "second") if readings == "both" else (readings,):
                numbers.append(rd.number(label, f, path, reading))
        text, f, path = q["answer"]
        ans = rd.number("answer", f, path, "current")
        out.append(
            {
                "id": q["id"],
                "question": q["question"],
                "decides": q["decides"],
                "rule": q["rule"],
                "answer": {"text": text, **{k: ans[k] for k in ("value", "source", "path", "reading", "grading")}},
                "numbers": numbers,
            }
        )
    out.append(cross_check(rd))
    return {
        "made_by": "python3 -m grader.questions",
        "time": now_iso(),
        "note": "Every number is read from the named summary at the named path; nothing is recomputed except the "
        "cross-check's gaps, which are marked `derived`. The figures are the published gradings; re-judging stages 1 to "
        "2b under post-freeze correction 4 (results/final/REJUDGE.md) changes no decision.",
        "readings": {
            "current": "the deciding reading: four checks, honesty pass 1, rescues by the first reply judge",
            "second": "the second reading (gate 2, item 3), reported beside: material false claims only, agreed rescues",
        },
        "gradings": {
            "as frozen": "graded with the tree at the stage's freeze tag",
            "corrected": "graded with the post-freeze corrections in that stage's FLAWS.md",
        },
        "questions": out,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m grader.questions", description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", help="default results/final/questions.json in this repo")
    a = ap.parse_args(argv)
    d = build()
    out = Path(a.out or LAB_ROOT / "results" / "final" / "questions.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, d)
    for q in d["questions"]:
        print(f"{q['id']}: {q['answer']['text']} ({len(q['numbers'])} numbers)")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
