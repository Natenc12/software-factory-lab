"""grader.questions: the numbers that answer Q1 to Q6 and the cross-check, read from the committed summaries."""

import json

import pytest

from grader import questions


def test_every_number_resolves_on_the_committed_summaries():
    d = questions.build()
    assert [q["id"] for q in d["questions"]] == ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "cross-check"]
    for q in d["questions"]:
        assert q["answer"]["text"] and q["numbers"]
        for n in [q["answer"], *q["numbers"]]:
            assert n["reading"] in ("current", "second") and n["grading"] in ("corrected", "as frozen")
            assert n["source"].startswith("results/") and n["source"].endswith("summary.json")


def test_published_figures():
    d = {q["id"]: q for q in questions.build()["questions"]}
    get = lambda qid, label, reading="current": next(  # noqa: E731
        n["value"] for n in d[qid]["numbers"] if n["label"] == label and n["reading"] == reading
    )
    assert d["Q1"]["answer"]["value"] is True and get("Q1", "margin over P0, trustworthy per 8") == 1.333
    assert get("Q5", "P5P (Opus) trustworthy per 8") == 6.75 and get("Q5", "P5PF (Fable) trustworthy per 8") == 6.75
    assert get("Q5", "P6P trustworthy per 8 (as frozen)") == 6.0 and d["Q5"]["answer"]["value"] is False
    assert get("Q3", "P5P goes in (stage 2)") is True and get("Q3", "P1 trustworthy per 8 (control)", "second") == 6.167
    assert d["cross-check"]["answer"]["value"] is True


def test_second_reading_paths_and_missing_paths():
    assert questions.second_path("decision.rows.P5P") == "decision_second_reading.rows.P5P"
    assert questions.second_path("per_row.P0.trustworthy_per_8") == "per_row_second_reading.P0.trustworthy_per_8"
    assert questions.second_path("against_control.plain_facts") == "against_control_second_reading.plain_facts"
    with pytest.raises(KeyError):
        questions.at({"a": {"b": 1}}, "a.c")


def test_cross_check_flags_a_gap_over_one(tmp_path, monkeypatch):
    src = json.loads((questions.LAB_ROOT / questions.S4C).read_text())
    src["decision"]["per_codebase"]["sqlglot"]["rows"]["P5PF"]["trustworthy_per_8"] = 7.5
    for rel in (questions.S4C, questions.S2B):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / questions.S4C).write_text(json.dumps(src))
    (tmp_path / questions.S2B).write_text((questions.LAB_ROOT / questions.S2B).read_text())
    cc = questions.cross_check(questions.Reader(tmp_path))
    assert cc["answer"]["value"] is False and cc["answer"]["text"] == "not confirmed"
    gap = next(n for n in cc["numbers"] if n["label"] == "P5P gap to the best row on sqlglot, trustworthy per 8")
    assert gap["value"] == 1.5 and "derived" in gap
