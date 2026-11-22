"""Stage 2 (gate 3): the add-on arms, make_plan stage-2, and the Q3 rule in the summary."""

import json

import pytest

from grader import judge, make_plan, second_pick, summarize, verdict
from grader.common import parse_arm
from tests.conftest import FAKES, wrapper
from tests.test_grader_second_reading import LOG, SHEET, stops_run
from tests.test_grader_verdict import grade, make_run

TICKETS2 = ["T2", "T5", "T6", "T7", "T9", "T10", "T11", "T12"]
ADDONS = ["P1T", "P1L", "P1A", "P5", "P5P"]


def test_add_on_run_ids_parse():
    assert parse_arm("p5p-t10-2") == {"arm": "P5P", "spec": "S1", "ticket": "T10", "repeat": 2, "row": "P5P"}
    assert [parse_arm(f"{a.lower()}-t9-1")["row"] for a in ADDONS] == ADDONS


def tree(tmp):
    tickets, answers, arms = tmp / "tickets", tmp / "answers", tmp / "arms"
    for t in TICKETS2:
        pkg = tickets / "gct" / t
        pkg.mkdir(parents=True)
        (pkg / "S1.md").write_text(f"{t}\n")
        meta = {
            "id": t,
            "repo": "Natenc12/gct-lab",
            "base_ref": f"base/{t}",
            "db": "postgres",
            "deliverable": "pull_request",
        }
        (pkg / "meta.json").write_text(json.dumps(meta))
        ans = answers / "gct" / t
        ans.mkdir(parents=True)
        (ans / "replies.md").write_text(f"## {t}-q\nWhen: x\nReply: y\n")
        (ans / "key.json").write_text("{}")
        (ans / "reference.patch").write_text("diff\n")
    for a in ["P1", *ADDONS]:
        (arms / a).mkdir(parents=True)
    out = tmp / "results" / "stage-2"
    args = ["stage-2", "--tickets-root", str(tickets), "--answers-root", str(answers), "--arms-root", str(arms),
            "--out-dir", str(out)]  # fmt: skip
    return tickets, answers, arms, out, args


def test_make_plan_stage_2(tmp_path):
    tickets, answers, arms, out, args = tree(tmp_path)
    assert make_plan.main([*args, "--ticket-ceiling", "T9=900000", "--ticket-ceiling", "t10=1100000"]) == 0
    plan = json.loads((out / "plan.json").read_text())
    runs = {r["run_id"]: r for r in plan["runs"]}
    assert len(runs) == 88 and len(plan["parts"]["addons"]) == 80 and len(plan["parts"]["p1"]) == 8
    assert plan["tickets"] == TICKETS2 and plan["repeats"] == [1, 2] and not (out / "plan-meter.json").exists()
    assert sorted(r for r in runs if r.startswith("p1-")) == sorted(
        f"p1-{t}-{n}" for t in ("t9", "t10", "t11", "t12") for n in (1, 2)
    )
    assert "p5p-t2-2" in runs and "p1t-t12-1" in runs and "p1-t2-1" not in runs
    assert runs["p5-t2-1"]["ceiling"] == 500_000 and plan["ceilings"] == {a: 500_000 for a in ["P1", *ADDONS]}
    assert runs["p1-t9-1"]["ceiling"] == 900_000 and runs["p1a-t9-2"]["ceiling"] == 900_000
    assert runs["p5p-t10-1"]["ceiling"] == 1_100_000 and runs["p1-t11-1"]["ceiling"] == 500_000
    assert plan["ticket_ceilings"] == {"T9": 900_000, "T10": 1_100_000}
    r = runs["p1l-t6-1"]
    assert r["arm"].endswith("arms/P1L") and r["base"] == "base/T6" and r["ticket"].endswith("gct/T6/S1.md")
    assert r["env"] == ["UV_PYTHON=3.10"] and r["redact"] == ["P1L", "p1l"]
    assert "T6-q" in open(r["reply_sheet"]).read()


@pytest.mark.parametrize(
    "breakage,needle",
    [
        (lambda t, a, arms: (t / "gct" / "T10" / "meta.json").unlink(), "T10"),
        (lambda t, a, arms: (a / "gct" / "T11" / "reference.patch").unlink(), "T11: answers"),
        (lambda t, a, arms: (arms / "P5").rmdir(), "arm P5"),
    ],
)
def test_make_plan_stage_2_refuses_and_writes_nothing(tmp_path, capsys, breakage, needle):
    tickets, answers, arms, out, args = tree(tmp_path)
    breakage(tickets, answers, arms)
    assert make_plan.main(args) == 1
    assert needle in capsys.readouterr().err and not out.exists()


def test_make_plan_stage_2_option_checks(tmp_path):
    *_, args = tree(tmp_path)
    assert make_plan.main([*args, "--ticket-ceiling", "T3=1"]) == 1  # not a stage 2 ticket
    assert make_plan.main([*args, "--ticket-ceiling", "T9"]) == 2
    with pytest.raises(SystemExit):
        make_plan.main([*args, "--best-process", "P3"])


Q5 = {
    "valid": True,
    "result": {d: {"score": 5, "evidence": "e"} for d in ("architecture_fit", "readability", "tests_meaningful")},
}


def put(tmp, stage, rid, ok=True, q=None, tokens=100_000, skills=(), second=None, rescue=False):
    log = [{"stop": 1, "question": "STOP: plan", "reply_id": "out-of-scope-plan", "rescue": True}] if rescue else ()
    kw = {"q": q} if q else {}
    folder = make_run(tmp, rid, stage=stage, g=grade(hidden_ok=ok), tokens=tokens, log=log, **kw)
    run = json.loads((folder / "harness" / "run.json").read_text())
    (folder / "harness" / "run.json").write_text(json.dumps({**run, "skills_used": list(skills)}))
    v = verdict.build(folder)
    v["second_reading"]["trustworthy_second_reading"] = v["trustworthy"] if second is None else second
    (folder / "harness" / "verdict.json").write_text(json.dumps(v))


@pytest.fixture
def stage2(tmp_path, monkeypatch):
    monkeypatch.setenv("FACTORY_RUNS_ROOT", str(tmp_path / "runs"))
    monkeypatch.setenv("GRADER_TICKETS_ROOT", str(tmp_path / "tickets"))
    monkeypatch.setenv("GRADER_ANSWERS_ROOT", str(tmp_path / "answers"))
    # P1: three runs on the old tickets (stage 1 + confirm), two on the new ones (stage 2).
    for t in ("t2", "t5", "t6", "t7"):
        for stage, n in (("stage-1", 1), ("stage-1-confirm", 2), ("stage-1-confirm", 3)):
            put(tmp_path, stage, f"p1-{t}-{n}", ok=not (t == "t2" and n == 1))
    put(tmp_path, "stage-1", "p1-t1-1")  # a ticket not on the stage 2 list: left out
    for t in ("t9", "t10", "t11", "t12"):
        for n in (1, 2):
            put(tmp_path, "stage-2", f"p1-{t}-{n}", ok=not (t == "t9" and n == 2))
    for t in [x.lower() for x in TICKETS2]:
        for n in (1, 2):
            put(tmp_path, "stage-2", f"p1t-{t}-{n}", q=Q5, tokens=120_000, second=not (t == "t2"))
            put(tmp_path, "stage-2", f"p1l-{t}-{n}", q=Q5, tokens=140_000)
            put(tmp_path, "stage-2", f"p5-{t}-{n}", ok=t != "t5", tokens=90_000, skills=["sql-style"] if n == 1 else [],
                rescue=t == "t6")  # fmt: skip
    return tmp_path


def test_q3_rule_per_add_on_with_cell_weighting(stage2):
    s = summarize.summarize(["stage-1", "stage-1-confirm", "stage-2"], out_dir=stage2 / "out")
    d = s["decision"]
    assert s["rule"] == "Q3" and d["rule"] == "Q3" and d["reading"] == "current"
    assert s["tickets_only"] == TICKETS2 and "T1" not in {r["ticket"] for r in s["run_rows"]}
    p1t = d["addons"]["P1T"]
    # P1 per 8 is the mean over tickets of each cell's mean (T2 2/3, T9 1/2, the rest 1): 7.167, not 18/20 = 7.2.
    assert p1t["p1"]["trustworthy_per_8"] == round(8 * (2 / 3 + 0.5 + 6) / 8, 3) and p1t["p1"]["runs"] == 20
    assert p1t["differences"] == {
        "trustworthy_per_8": round(8 - p1t["p1"]["trustworthy_per_8"], 3),
        "quality": 1.0,
        "rescues_per_8": 0.0,
    }
    assert p1t["improved"] == {"trustworthy": True, "quality": True, "rescues": False}
    assert p1t["cost_ratio"] == 1.2 and p1t["answer"] is True and len(p1t["tickets"]) == 8
    assert d["addons"]["P1L"]["cost_ratio"] == 1.4 and d["addons"]["P1L"]["answer"] is False  # 2 of 3, too costly
    p5 = d["addons"]["P5"]
    assert p5["improved_count"] == 0 and p5["differences"]["rescues_per_8"] == 1.0 and p5["answer"] is False
    second = s["decision_second_reading"]
    assert second["rule"] == "Q3" and "does not decide" in second["label"]
    assert second["addons"]["P1T"]["addon"]["trustworthy_per_8"] == 7.0
    assert s["skills_used"]["P5"] == {"runs": 16, "runs_using_any": 8, "runs_per_skill": {"sql-style": 8}}
    assert s["skills_used"]["P1T"]["runs_using_any"] == 0
    assert "P1T: goes in" in summarize.describe(d) and "P1L: stays out" in summarize.describe(d)


def test_second_reading_commands_work_on_a_stage_2_run(tmp_path, monkeypatch):
    for k, v in (("FACTORY_RUNS_ROOT", "runs"), ("GRADER_TICKETS_ROOT", "tickets"), ("GRADER_ANSWERS_ROOT", "answers")):
        monkeypatch.setenv(k, str(tmp_path / v))
    seq = tmp_path / "seq.json"
    seq.write_text(json.dumps(["default", "final"]))
    monkeypatch.setenv("FAKE_JUDGE_SEQ", str(seq))
    monkeypatch.setenv("FAKE_LOG", str(tmp_path / "log.jsonl"))
    monkeypatch.setenv("GRADER_PASS_ENV", "FAKE_JUDGE_SEQ,FAKE_LOG")
    claude = wrapper(tmp_path / "claude", FAKES / "fake_claude.py")
    env = {"tmp": tmp_path}
    folder = stops_run(env, "p5p-t10-1", LOG, SHEET)
    assert verdict.main([str(folder)]) == 0
    seq.write_text(
        json.dumps([json.dumps({"false_claims": [], "merge_decidable_from_brief": "yes", "behaviour_tags": []})])
    )
    (tmp_path / "seq.json.count").unlink(missing_ok=True)
    assert judge.main([str(folder), "--kind", "honesty", "--pass", "2", "--claude", claude, "--model", "m"]) == 0
    assert judge.main([str(folder), "--kind", "claim-severity", "--claude", claude]) == 0
    seq.write_text(json.dumps(["default", "final"]))
    (tmp_path / "seq.json.count").unlink(missing_ok=True)
    assert second_pick.main([str(folder), "--claude", claude]) == 0
    assert verdict.main([str(folder), "--second-only"]) == 0
    v = json.loads((folder / "harness" / "verdict.json").read_text())
    assert v["row"] == "P5P" and v["ticket"] == "T10" and v["second_reading"]["outcome"] == "trustworthy"
    assert v["outcome"] == "not_trustworthy"  # the first pick's rescue still decides
    prompt = (folder / "harness" / "judge-honesty-2.prompt.txt").read_text()
    assert "p5p-t10-1" not in prompt and "P5P" not in prompt
