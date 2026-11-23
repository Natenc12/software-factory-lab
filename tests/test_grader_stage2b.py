"""Stage 2b: the P5PA arm, make_plan stage-2b, and the summary with --control."""

import json

import pytest

from grader import judge, make_plan, second_pick, summarize, verdict
from grader.common import parse_arm
from tests.test_grader_stage2 import Q5, TICKETS2, put, tree
from tests.test_grader_verdict import honesty, make_run


def test_p5pa_run_ids_parse():
    assert parse_arm("p5pa-t12-2") == {"arm": "P5PA", "spec": "S1", "ticket": "T12", "repeat": 2, "row": "P5PA"}


def tree2b(tmp):
    tickets, answers, arms, out, args = tree(tmp)
    (arms / "P5PA").mkdir()
    out = tmp / "results" / "stage-2b"
    args = ["stage-2b", *args[1:-1], str(out)]
    return arms, out, args


def test_make_plan_stage_2b(tmp_path):
    arms, out, args = tree2b(tmp_path)
    assert make_plan.main([*args, "--ticket-ceiling", "T10=1100000"]) == 0
    plan = json.loads((out / "plan.json").read_text())
    runs = {r["run_id"]: r for r in plan["runs"]}
    assert (
        plan["stage"] == "stage-2b" and len(runs) == 32 and plan["tickets"] == TICKETS2 and plan["repeats"] == [1, 2, 3]
    )
    t = [x.lower() for x in TICKETS2]
    assert plan["parts"]["repeat3"] == [f"{a}-{x}-3" for x in t for a in ("p5p", "p1a")]
    assert plan["parts"]["p5pa"] == [f"p5pa-{x}-{n}" for n in (1, 2) for x in t]
    assert plan["ceilings"] == {"P5P": 500_000, "P1A": 500_000, "P5PA": 500_000}
    assert runs["p5pa-t10-2"]["ceiling"] == 1_100_000 and runs["p5p-t10-3"]["ceiling"] == 1_100_000
    assert runs["p1a-t2-3"]["ceiling"] == 500_000 and runs["p5pa-t9-1"]["arm"].endswith("arms/P5PA")
    assert (out / "sheets" / "gct-T12.md").is_file()


def test_make_plan_stage_2b_refuses_without_the_arm(tmp_path, capsys):
    arms, out, args = tree2b(tmp_path)
    (arms / "P5PA").rmdir()
    assert make_plan.main(args) == 1
    assert "arm P5PA" in capsys.readouterr().err and not out.exists()


@pytest.fixture
def rounds(tmp_path, monkeypatch):
    for k, v in (("FACTORY_RUNS_ROOT", "runs"), ("GRADER_TICKETS_ROOT", "tickets"), ("GRADER_ANSWERS_ROOT", "answers")):
        monkeypatch.setenv(k, str(tmp_path / v))
    for t in [x.lower() for x in TICKETS2]:
        for n in (1, 2, 3):
            put(tmp_path, "stage-1-confirm" if n > 1 else "stage-1", f"p1-{t}-{n}", tokens=100_000)
        for n in (1, 2):
            put(tmp_path, "stage-2", f"p5p-{t}-{n}", ok=t != "t2", tokens=150_000)
            put(tmp_path, "stage-2", f"p1a-{t}-{n}", tokens=110_000)
            put(tmp_path, "stage-2b", f"p5pa-{t}-{n}", q=Q5, tokens=165_000, second=t != "t5")
        put(tmp_path, "stage-2b", f"p5p-{t}-3", tokens=150_000)
        put(tmp_path, "stage-2b", f"p1a-{t}-3", ok=t != "t6", tokens=110_000)
    return tmp_path


STAGES = ["stage-1", "stage-1-confirm", "stage-2", "stage-2b"]


def test_stage_2b_joins_the_q3_table_against_p1(rounds):
    s = summarize.summarize(STAGES, out_dir=rounds / "out")
    d = s["decision"]
    assert s["rule"] == "Q3" and d["control"] == "P1" and "against_control" not in s
    assert set(d["addons"]) == {"P5P", "P1A", "P5PA"}
    assert d["addons"]["P5PA"]["p1"]["trustworthy_per_8"] == 8.0 and d["addons"]["P5PA"]["cost_ratio"] == 1.65
    # P5P on T2: two failures in stage 2, one pass in stage 2b -> the cell's mean is 1/3.
    assert d["addons"]["P5P"]["addon"]["trustworthy_per_8"] == round(8 * (1 / 3 + 7) / 8, 3)


def test_control_p5p_rereads_the_table_with_plain_facts(rounds):
    s = summarize.summarize(STAGES, out_dir=rounds / "out", control="P5P")
    assert s["decision"]["control"] == "P1"  # the decision itself stays against P1
    c = s["against_control"]
    assert c["control"] == "P5P" and "against P1" in c["rule"] and set(c["addons"]) == {"P1", "P1A", "P5PA"}
    p5p = round(8 * (1 / 3 + 7) / 8, 3)
    assert c["addons"]["P5PA"]["control"]["trustworthy_per_8"] == p5p and "p1" not in c["addons"]["P5PA"]
    assert c["plain_facts"]["P5PA"] == {"trustworthy_per_8_difference": round(8 - p5p, 3), "cost_ratio": 1.1}
    p1a_minus_p5p = (2 / 3 + 7) - (1 / 3 + 7)  # P1A fails once on T6 (repeat 3); P5P twice on T2
    assert c["plain_facts"]["P1A"] == {
        "trustworthy_per_8_difference": round(p1a_minus_p5p, 3),
        "cost_ratio": round(110 / 150, 3),
    }
    second = s["against_control_second_reading"]
    assert "does not decide" in second["label"] and second["plain_facts"]["P5PA"][
        "trustworthy_per_8_difference"
    ] == round(7 - p5p, 3)
    assert summarize.main([*STAGES, "--control", "p5p", "--out-dir", str(rounds / "o2")]) == 0
    with pytest.raises(SystemExit):
        summarize.main(["stage-1", "--control", "P5P"])


def test_second_reading_commands_work_on_a_stage_2b_run(tmp_path, monkeypatch):
    for k, v in (("FACTORY_RUNS_ROOT", "runs"), ("GRADER_TICKETS_ROOT", "tickets"), ("GRADER_ANSWERS_ROOT", "answers")):
        monkeypatch.setenv(k, str(tmp_path / v))
    folder = make_run(tmp_path, "p5pa-t9-1", stage="stage-2b")
    (folder / "harness" / "judge-honesty-2.json").write_text(json.dumps(honesty()))
    assert verdict.main([str(folder)]) == 0
    assert judge.main([str(folder), "--kind", "claim-severity", "--claude", "/nonexistent"]) == 0  # no claims: no call
    assert second_pick.main([str(folder), "--claude", "/nonexistent"]) == 0  # no stops: no call
    assert verdict.main([str(folder), "--second-only"]) == 0
    v = json.loads((folder / "harness" / "verdict.json").read_text())
    assert v["row"] == "P5PA" and v["outcome"] == "trustworthy" and v["second_reading"]["outcome"] == "trustworthy"
