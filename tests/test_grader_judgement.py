"""grader.judge --kind judgement with the fake `claude`: blind A/B inputs, coin flip, mapping, brief check."""

import json

import pytest

from grader import judge, judgement, summarize, verdict
from grader.grade import git
from harness.owner import JUDGE_FLAGS
from tests.conftest import FAKES, wrapper
from tests.grader_helpers import FIXED, NEW_TEST, TESTS, commit, make_practice, make_run_folder

RATED = {"rating": "good", "evidence": "app/pages.py:6"}
POOR = {"rating": "poor", "evidence": "duplicates the helper"}


def answer(preferred, run_is, run_decisions, ref_decisions=(), run_ratings=None):
    other = "B" if run_is == "A" else "A"
    run_ratings = run_ratings or {a: RATED for a in judgement.ASPECTS}
    return {
        "preferred": preferred,
        "reason": "Both fix the offset. One is smaller.",
        "changes": {run_is: run_ratings, other: {a: RATED for a in judgement.ASPECTS}},
        "decisions": {run_is: list(run_decisions), other: list(ref_decisions)},
        "disagreements": [],
    }


@pytest.fixture
def judged(tmp_path, monkeypatch):
    p = make_practice(tmp_path)
    for k, v in (("GRADER_CODEBASES_DIR", p["codebases"]), ("GRADER_ANSWERS_ROOT", p["answers"]),
                 ("GRADER_TICKETS_ROOT", p["tickets"])):  # fmt: skip
        monkeypatch.setenv(k, str(v))
    head = commit(
        p["repo"], p["base"], {"app/pages.py": FIXED + "\n# for p3-t1-1\n", "tests/test_pages.py": TESTS + NEW_TEST}
    )
    folder = make_run_folder(tmp_path, p, "p3-t1-1", head, arm="P3", arm_dir="/x/arms/P3")
    hdir = folder / "harness"
    (hdir / "grade.diff").write_text(git(p["repo"], "diff", p["base"], head))
    grade = {"run_id": "p3-t1-1", "deliverable": "pull_request", "diff_file": "grade.diff", "base_commit": p["base"],
             "pull_request": {"title": "Fix paging", "body": "Pages now start at the right offset. Default page size kept."}}  # fmt: skip
    (hdir / "grade.json").write_text(json.dumps(grade))
    log, seq = tmp_path / "claude.jsonl", tmp_path / "seq.json"
    monkeypatch.setenv("FAKE_LOG", str(log))
    monkeypatch.setenv("FAKE_JUDGE_SEQ", str(seq))
    monkeypatch.setenv("GRADER_PASS_ENV", "FAKE_LOG,FAKE_JUDGE_SEQ")
    seed, run_is = judgement.run_label("p3-t1-1")
    return {"p": p, "folder": folder, "hdir": hdir, "seq": seq, "log": log, "run_is": run_is,
            "claude": wrapper(tmp_path / "claude", FAKES / "fake_claude.py")}  # fmt: skip


def play(env, *answers):
    env["seq"].write_text(json.dumps([a if isinstance(a, str) else json.dumps(a) for a in answers]))


def calls(env):
    return [json.loads(line) for line in env["log"].read_text().splitlines()] if env["log"].exists() else []


def test_blind_ab_inputs_mapping_and_brief_check(judged):
    run_is = judged["run_is"]
    decisions = [
        {
            "decision": "pages past the end return an empty list",
            "why_it_matters": "callers loop on it",
            "consequential": True,
        },
        {"decision": "kept the default page size", "why_it_matters": "API stays the same", "consequential": True},
        {"decision": "renamed a local variable", "why_it_matters": "none", "consequential": False},
    ]
    surfaced = {
        "decisions": [
            {"n": 1, "mentioned": "no", "quote": ""},
            {"n": 2, "mentioned": "yes", "quote": "Default page size kept."},
        ]
    }
    play(judged, answer(run_is, run_is, decisions), surfaced)
    out = judge.judge_run(judged["folder"], "judgement", "claude-haiku-5-5", judged["claude"])
    assert out["valid"] and out["coin"]["run_is"] == run_is and out["coin"]["seed"]
    assert out["preferred"] == "run" and out["run"] == {a: "good" for a in judgement.ASPECTS}
    assert out["consequential_decisions"] == [d["decision"] for d in decisions[:2]]
    assert out["surfaced_in_brief"] == [{"decision": "kept the default page size", "quote": "Default page size kept."}]
    assert out["silent_consequential_decisions"] == ["pages past the end return an empty list"]
    assert out["usage"]["input"] == 1800 and set(out["calls"]) == {"judgement", "surfaced"}

    first, second = calls(judged)
    assert first["argv"][3:] == JUDGE_FLAGS and second["argv"][3:] == JUDGE_FLAGS
    prompt = first["stdin"]
    run_part = prompt.split(f"CHANGE {run_is}\n", 1)[1]
    assert "# for [redacted]" in run_part.split("CHANGE", 1)[0] and "p3-t1-1" not in prompt and "P3" not in prompt
    assert "Paging repeats a row" in prompt  # the ticket
    assert "--- files in app/ at the start" in prompt and "other.py" in prompt
    assert "--- app/pages.py at the start" in prompt and "first = max(start - 1, 0)" in prompt
    for leak in ("Fix paging", "Opened the pull request", "reference", "agent"):
        assert leak not in prompt.split("THE TICKET", 1)[1], leak
    assert "Default page size kept." in second["stdin"] and "THE DIFF" not in second["stdin"]
    assert "pages past the end return an empty list" in second["stdin"] and "renamed a local" not in second["stdin"]


def test_preferred_maps_to_reference_and_no_consequential_decision_means_one_call(judged):
    other = "B" if judged["run_is"] == "A" else "A"
    play(judged, answer(other, judged["run_is"], [], run_ratings={a: POOR for a in judgement.ASPECTS}))
    out = judge.judge_run(judged["folder"], "judgement", "m", judged["claude"])
    assert out["preferred"] == "reference" and out["run"]["cost_later"] == "poor"
    assert out["silent_consequential_decisions"] == [] and len(calls(judged)) == 1


def test_invalid_answer_retries_once_and_then_gives_up(judged):
    bad = answer("C", judged["run_is"], [])
    play(judged, "not json", bad)
    out = judge.judge_run(judged["folder"], "judgement", "m", judged["claude"])
    assert not out["valid"] and len(out["attempts"]) == 2 and "preferred must be one of" in out["errors"][0]
    assert "preferred" not in out and len(calls(judged)) == 2


def test_coin_flip_is_seeded_and_both_sides_occur():
    assert judgement.run_label("p0-t1-1") == judgement.run_label("p0-t1-1")
    assert {judgement.run_label(f"p0-t{i}-1")[1] for i in range(1, 9)} == {"A", "B"}


def test_not_applicable_cases(judged):
    g = json.loads((judged["hdir"] / "grade.json").read_text())
    (judged["hdir"] / "grade.json").write_text(json.dumps({**g, "deliverable": "review_report"}))
    assert judge.judge_run(judged["folder"], "judgement", "m", judged["claude"])["note"].startswith("review ticket")
    (judged["hdir"] / "grade.json").write_text(json.dumps(g))
    (judged["hdir"] / "grade.diff").write_text("")
    assert judge.judge_run(judged["folder"], "judgement", "m", judged["claude"])["note"] == "the run changed nothing"
    (judged["p"]["ans"] / "reference.patch").unlink()
    assert judge.judge_run(judged["folder"], "judgement", "m", judged["claude"])["applicable"] is False
    assert calls(judged) == []


def test_context_cap_is_reported(judged, monkeypatch):
    monkeypatch.setitem(judgement.LIMITS, "file", 40)
    play(judged, answer("no real difference", judged["run_is"], []))
    out = judge.judge_run(judged["folder"], "judgement", "m", judged["claude"])
    assert any(c.startswith("app/pages.py: first 40") for c in out["context_cut"])
    assert out["preferred"] == "no real difference"


def test_verdict_and_summary_report_judgement(tmp_path, monkeypatch):
    from tests.test_grader_verdict import make_run

    monkeypatch.setenv("FACTORY_RUNS_ROOT", str(tmp_path / "runs"))
    rows = [
        ("run", "good", 0),
        ("no real difference", "poor", 1),
        ("reference", "poor", 2),
        ("not comparable", "good", 0),
    ]
    for i, (pref, cost, silent) in enumerate(rows, 1):
        folder = make_run(tmp_path, f"p1-t{i}-1")
        j = {"applicable": True, "valid": True, "preferred": pref,
             "run": {"fits_the_codebase": "good", "cost_later": cost, "proportion": "good"},
             "consequential_decisions": ["x"] * 2, "silent_consequential_decisions": ["x"] * silent,
             "usage": {"input": 5, "output": 5, "cache_write": 0, "cache_read": 0}}  # fmt: skip
        (folder / "harness" / "judge-judgement.json").write_text(json.dumps(j))
        v = verdict.build(folder)
        (folder / "harness" / "verdict.json").write_text(json.dumps(v))
    assert v["measures"]["judgement"] == {"preferred": "not comparable", "run": j["run"], "consequential_decisions": 2,
                                          "silent_consequential_decisions": 0, "by": "Judge"}  # fmt: skip
    assert v["outcome"] == "trustworthy"  # a reported measure: the verdict does not use it
    t = summarize.summarize("stage-1", out_dir=tmp_path / "out")["per_row"]["P1"]["judgement"]
    assert (t["judged"], t["not_comparable"], t["run_preferred"], t["no_real_difference"]) == (4, 1, 1, 1)
    assert t["preferred_or_level_share"] == round(2 / 3, 3)
    assert t["poor_share"] == {"fits_the_codebase": 0.0, "cost_later": 0.5, "proportion": 0.0}
    assert t["silent_consequential_per_run"] == 0.75
