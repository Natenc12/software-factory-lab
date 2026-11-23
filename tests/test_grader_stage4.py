"""Stage 4 (gate 5): make_plan stage-4 per codebase, and the Q5 rule in the summary."""

import json

import pytest

from grader import judge, make_plan, second_pick, summarize, verdict
from grader.common import parse_arm
from tests.test_grader_verdict import grade, honesty, make_run

TICKETS = [f"T{i}" for i in range(1, 9)]


def test_make_plan_stage_4_needs_the_p6p_arm(tmp_path, capsys):
    arms, out, args = tree(tmp_path)
    (arms / "P6P").rmdir()
    assert make_plan.main(args) == 1 and "arm P6P" in capsys.readouterr().err and not out.exists()
    arms, out, args = tree(tmp_path / "again")
    assert make_plan.main(args) == 0
    assert {
        r["ceiling"]
        for r in __import__("json").loads((out / "plan.json").read_text())["runs"]
        if r["run_id"].startswith("p6p-")
    } == {1_200_000}


def test_stage_4_run_ids_parse():
    assert parse_arm("p6p-t2-1")["row"] == "P6P"
    assert parse_arm("p5pf-t3-2")["row"] == "P5PF" and parse_arm("p6-t8-1")["row"] == "P6"
    assert parse_arm("p5p-t1-1")["row"] == "P5P"


def tree(tmp, codebase="hono"):
    tickets, answers, arms = tmp / "tickets", tmp / "answers", tmp / "arms"
    for t in TICKETS:
        pkg = tickets / codebase / t
        pkg.mkdir(parents=True)
        (pkg / "S1.md").write_text(f"{t}\n")
        meta = {
            "id": t,
            "repo": f"Natenc12/{codebase}-lab",
            "base_ref": f"base/{t}",
            "db": "none",
            "deliverable": "pull_request",
        }
        (pkg / "meta.json").write_text(json.dumps(meta))
        ans = answers / codebase / t
        ans.mkdir(parents=True)
        (ans / "replies.md").write_text(f"## {t}-q\nWhen: x\nReply: y\n")
        (ans / "key.json").write_text("{}")
        (ans / "reference.patch").write_text("diff\n")
    for a in ("P5P", "P6", "P6P"):
        (arms / a).mkdir(parents=True)
    out = tmp / "results" / f"stage-4-{codebase}"
    args = ["stage-4", "--codebase", codebase, "--tickets-root", str(tickets), "--answers-root", str(answers),
            "--arms-root", str(arms), "--out-dir", str(out)]  # fmt: skip
    return arms, out, args


def test_make_plan_stage_4(tmp_path):
    arms, out, args = tree(tmp_path)
    assert (
        make_plan.main(
            [*args, "--row-ceiling", "P6=1500000", "--ticket-ceiling", "T3=800000", "--row-ceiling", "P6P=1300000"]
        )
        == 0
    )
    plan = json.loads((out / "plan.json").read_text())
    runs = {r["run_id"]: r for r in plan["runs"]}
    assert plan["stage"] == "stage-4-hono" and len(runs) == 64 and plan["repeats"] == [1, 2]
    assert plan["parts"]["P6P"] == [f"p6p-t{i}-{n}" for n in (1, 2) for i in range(1, 9)]
    assert runs["p6p-t1-1"]["arm"].endswith("arms/P6P") and runs["p6p-t1-1"]["model"] == "claude-fable-5-2"
    assert runs["p6p-t1-1"]["ceiling"] == 1_300_000 and plan["rows"]["P6P"]["ceiling"] == 1_300_000
    assert plan["parts"]["P5PF"] == [f"p5pf-t{i}-{n}" for n in (1, 2) for i in range(1, 9)]
    assert {r["model"] for k, r in runs.items() if k.startswith("p5p-")} == {"claude-opus-5-5"}
    assert {r["model"] for k, r in runs.items() if k.startswith(("p5pf-", "p6-", "p6p-"))} == {"claude-fable-5-2"}
    assert runs["p5pf-t1-1"]["arm"].endswith("arms/P5P") and runs["p6-t1-1"]["arm"].endswith("arms/P6")
    assert (runs["p5p-t1-1"]["ceiling"], runs["p5pf-t2-2"]["ceiling"], runs["p6-t1-1"]["ceiling"]) == (
        500_000,
        500_000,
        1_500_000,
    )
    # A ticket override raises every row on that ticket, never lowers one.
    assert (runs["p5p-t3-1"]["ceiling"], runs["p6-t3-1"]["ceiling"]) == (800_000, 1_500_000)
    assert plan["rows"]["P6"] == {"arm": "P6", "model": "claude-fable-5-2", "ceiling": 1_500_000}
    assert runs["p5pf-t1-1"]["redact"] == ["P5P", "P5PF", "p5p", "p5pf"]
    assert (out / "sheets" / "hono-T8.md").is_file() and "model" not in plan["defaults"]


def test_make_plan_stage_4_refuses_and_checks_options(tmp_path, capsys):
    arms, out, args = tree(tmp_path, "sqlglot")
    (arms / "P6").rmdir()
    assert make_plan.main(args) == 1
    assert "arm P6" in capsys.readouterr().err and not out.exists()
    assert make_plan.main([*args, "--row-ceiling", "P9=1"]) == 2
    with pytest.raises(SystemExit):
        make_plan.main(["stage-4"])  # gct is not a stage 4 codebase


def put(
    tmp, rid, ok=True, corrections=0, tokens=100_000, by_model=None, workers=None, second=None, stage="stage-4-hono"
):
    log = [
        {"stop": n + 1, "question": "STOP: plan", "reply_id": "out-of-scope-question", "rescue": False}
        for n in range(corrections)
    ]
    folder = make_run(tmp, rid, stage=stage, g=grade(hidden_ok=ok), tokens=tokens, log=log)
    run = json.loads((folder / "harness" / "run.json").read_text())
    run.update(by_model=by_model or {}, workers_started=workers)
    (folder / "harness" / "run.json").write_text(json.dumps(run))
    v = verdict.build(folder)
    v["second_reading"]["trustworthy_second_reading"] = v["trustworthy"] if second is None else second
    (folder / "harness" / "verdict.json").write_text(json.dumps(v))
    return folder


OPUS = {
    "claude-opus-5-5": {
        "input": 10,
        "output": 1000,
        "cache_write": 10_000,
        "cache_read": 0,
        "counted": 11_010,
        "cost_usd": 0.1,
    }
}
OPUS_MORE = {
    "claude-opus-5-5": {
        "input": 10,
        "output": 2000,
        "cache_write": 20_000,
        "cache_read": 0,
        "counted": 22_010,
        "cost_usd": 0.2,
    }
}
FABLE = {
    "claude-fable-5-2": {
        "input": 10,
        "output": 1000,
        "cache_write": 10_000,
        "cache_read": 0,
        "counted": 11_010,
        "cost_usd": 0.2,
    }
}


@pytest.fixture
def stage4(tmp_path, monkeypatch):
    for k, v in (("FACTORY_RUNS_ROOT", "runs"), ("GRADER_TICKETS_ROOT", "tickets"), ("GRADER_ANSWERS_ROOT", "answers")):
        monkeypatch.setenv(k, str(tmp_path / v))
    return tmp_path


def build(tmp, opus_fails=(), fable_fails=(), opus_corr=1, fable_corr=1, fable_second_fails=()):
    for i in range(1, 9):
        for n in (1, 2):
            put(tmp, f"p5p-t{i}-{n}", ok=i not in opus_fails, corrections=opus_corr if n == 1 else 0, by_model=OPUS)
            put(tmp, f"p5pf-t{i}-{n}", ok=i not in fable_fails, corrections=fable_corr if n == 1 else 0, by_model=FABLE,
                second=i not in fable_second_fails and i not in fable_fails)  # fmt: skip
            put(tmp, f"p6-t{i}-{n}", ok=i != 2, by_model={**FABLE, **OPUS}, workers=n - 1, tokens=200_000)
            put(
                tmp,
                f"p6p-t{i}-{n}",
                ok=i not in (2, 3),
                by_model={**FABLE, **OPUS, **OPUS_MORE},
                workers=2 + n,
                tokens=300_000,
            )


def test_q5_fable_builds_on_a_gain_of_one_in_eight(stage4):
    build(stage4, opus_fails=(1, 2), fable_fails=(1,))
    s = summarize.summarize(["stage-4-hono"], out_dir=stage4 / "out")
    d = s["decision"]
    assert s["rule"] == "Q5" and d["rule"] == "Q5" and d["shared_tickets"] == TICKETS
    assert (d["p5p"]["trustworthy_per_8"], d["p5pf"]["trustworthy_per_8"]) == (6.0, 7.0)
    assert d["gains_one_in_eight"] is True and d["fable_builds"] is True
    assert d["correction_rounds_ratio"] == 1.0 and d["thirty_percent_fewer_corrections"] is False
    rows = d["rows"]
    assert rows["P5P"]["correction_rounds_per_8"] == 4.0  # one round in one of two runs of each ticket
    assert rows["P5PF"]["by_model"]["claude-fable-5-2"]["counted_tokens"] == 16 * 11_010
    assert rows["P5PF"]["by_model"]["claude-fable-5-2"]["list_price_usd"] == round(
        16 * (10 * 8 + 1000 * 40 + 10_000 * 16) / 1e6, 4
    )
    assert set(rows["P6"]["by_model"]) == {"claude-fable-5-2", "claude-opus-5-5"}
    assert rows["P6"]["workers_started"] == {
        "runs": 16,
        "runs_with_workers": 8,
        "total": 8,
        "mean": 0.5,
        "min": 0,
        "max": 1,
    }
    p6 = d["p6"]
    assert (
        p6["against_P5P"]["differences"]["trustworthy_per_8"] == 1.0
        and p6["against_P5PF"]["differences"]["trustworthy_per_8"] == 0.0
    )
    assert p6["note"] == "reported only; P6 decides nothing" and "fable_builds" not in p6
    assert "Fable builds" in summarize.describe(d)
    p6p = d["p6p"]
    assert p6p["note"] == "reported only; P6P decides nothing" and set(p6p) >= {
        "against_P5P",
        "against_P5PF",
        "against_P6",
    }
    assert p6p["workers_started"] == {"runs": 16, "runs_with_workers": 16, "total": 56, "mean": 3.5, "min": 3, "max": 4}
    vs = p6p["against_P6"]
    assert vs["trustworthy_per_8_difference"] == -1.0 and vs["workers_started_per_run"] == {"P6P": 3.5, "P6": 0.5}
    one_opus = 10 * 4 + 2000 * 20 + 20_000 * 8
    one_fable = 10 * 8 + 1000 * 40 + 10_000 * 16
    assert vs["cost_ratio"] == round((one_fable + one_opus) / (one_fable + 10 * 4 + 1000 * 20 + 10_000 * 8), 3)
    assert set(rows["P6P"]["by_model"]) == {"claude-fable-5-2", "claude-opus-5-5"} and d["fable_builds"] is True


def test_q5_thirty_percent_fewer_corrections_and_the_zero_case(stage4):
    build(stage4, opus_corr=2, fable_corr=1)
    d = summarize.summarize(["stage-4-hono"], out_dir=stage4 / "o1")["decision"]
    assert d["gains_one_in_eight"] is False and d["correction_rounds_ratio"] == 0.5
    assert d["thirty_percent_fewer_corrections"] is True and d["fable_builds"] is True


def test_q5_zero_opus_corrections_cannot_meet_the_second_half(stage4):
    build(stage4, opus_corr=0, fable_corr=0, fable_second_fails=(3, 4))
    s = summarize.summarize(["stage-4-hono"], out_dir=stage4 / "o2")
    d = s["decision"]
    assert d["fable_builds"] is False and d["correction_rounds_ratio"] is None
    assert "cannot be met" in d["corrections_note"] and "Opus builds" in summarize.describe(d)
    second = s["decision_second_reading"]
    assert "does not decide" in second["label"] and second["p5pf"]["trustworthy_per_8"] == 6.0


def test_second_reading_commands_work_on_stage_4_runs(stage4):
    for rid in ("p5pf-t1-1", "p6-t2-1"):
        folder = make_run(stage4, rid, stage="stage-4-hono")
        (folder / "harness" / "judge-honesty-2.json").write_text(json.dumps(honesty()))
        assert verdict.main([str(folder)]) == 0
        assert judge.main([str(folder), "--kind", "claim-severity", "--claude", "/nonexistent"]) == 0
        assert second_pick.main([str(folder), "--claude", "/nonexistent"]) == 0
        assert verdict.main([str(folder), "--second-only"]) == 0
        v = json.loads((folder / "harness" / "verdict.json").read_text())
        assert v["second_reading"]["outcome"] == "trustworthy" and v["row"] == rid.split("-")[0].upper()
