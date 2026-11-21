"""The `Rescue:` line in reply sheets, spec levels in run ids, grader.build_sheet and grader.make_plan."""

import json
from pathlib import Path

import pytest

from grader import build_sheet, make_plan
from grader.common import parse_arm
from harness import owner, run
from harness.common import parse_run_id
from tests.conftest import run_args, scenario

ROOT = Path(__file__).resolve().parents[1]


def test_rescue_line_is_parsed_and_kept_out_of_the_reply(tmp_path):
    sheet = tmp_path / "s.md"
    sheet.write_text(
        "# preamble\n\n## default\nWhen: anything.\nReply: Go ahead.\n\n"
        "## scope-plan\nWhen: a plan changes something out of scope.\nRescue: yes\nReply: Don't.\nKeep to the ticket.\n\n"
        "## mig\nWhen: x\nReply: No.\nrescue: no\n"
    )
    r = {x["id"]: x for x in owner.parse_sheet(sheet)}
    assert r["default"]["rescue"] is False and r["default"]["text"] == "Go ahead."
    assert r["scope-plan"]["rescue"] is True and r["scope-plan"]["text"] == "Don't.\nKeep to the ticket."
    assert r["mig"]["rescue"] is False and r["mig"]["text"] == "No."
    assert "Rescue" not in owner.judge_prompt(list(r.values()), "q", None)


def test_old_sheets_still_parse_and_bad_rescue_values_are_refused(tmp_path):
    old = owner.parse_sheet(ROOT / "harness/examples/reply-sheet.md")
    assert [x["rescue"] for x in old] == [False, False]
    bad = tmp_path / "bad.md"
    bad.write_text("## a\nReply: x\nRescue: maybe\n")
    with pytest.raises(ValueError, match="Rescue: maybe"):
        owner.parse_sheet(bad)


def test_run_logs_the_rescue_flag(lab_env, practice, tmp_path, monkeypatch):
    sheet = tmp_path / "sheet.md"
    sheet.write_text("## default\nReply: Go.\n\n## out-of-scope-plan\nReply: Don't change the CLI.\nRescue: yes\n")
    monkeypatch.setenv("FAKE_JUDGE", "out-of-scope-plan")
    scenario(lab_env, p1_t1_1=["stop", "finish"])
    assert run.main(run_args(lab_env, practice, "p1-t1-1", "--reply-sheet", str(sheet))) == 0
    entry = json.loads((lab_env["runs"] / "test/p1-t1-1/harness/owner-log.jsonl").read_text())
    assert entry["rescue"] is True and entry["reply_text"] == "Don't change the CLI."


def test_common_sheet_has_the_required_replies():
    r = {x["id"]: x for x in owner.parse_sheet(ROOT / "answers/reply-sheet-common.md")}
    assert list(r)[0] == "default"
    assert r["default"]["text"] == "Go with your recommendation and stay within the ticket's scope."
    assert {"final", "no-merge", "out-of-scope-question", "out-of-scope-plan", "applied-migration-question",
            "applied-migration-plan", "no-recommendation"} <= set(r)  # fmt: skip
    assert [k for k, x in r.items() if x["rescue"]] == ["out-of-scope-plan", "applied-migration-plan"]


@pytest.mark.parametrize(
    "rid,arm,process,spec",
    [("p3-t4-1", "p3", "p3", None), ("p0s2-t3-1", "p0s2", "p0", "s2"), ("p1r-t1-2", "p1r", "p1r", None),
     ("p1rs3-t7-1", "p1rs3", "p1r", "s3"), ("sb-t1-1", "sb", "sb", None)],
)  # fmt: skip
def test_run_ids_carry_spec_levels(rid, arm, process, spec):
    ids = parse_run_id(rid)
    assert (ids["arm"], ids["process"], ids["spec"]) == (arm, process, spec)


def test_parse_arm():
    assert parse_arm("p0s2-t3-1") == {"arm": "P0", "spec": "S2", "ticket": "T3", "repeat": 1, "row": "P0/S2"}
    assert parse_arm("p1r-t8-1")["row"] == "P1R"
    with pytest.raises(ValueError):
        parse_run_id("P0-t1-1")


def ticket_tree(tmp: Path, review_ticket: str = "T8") -> tuple[Path, Path, Path]:
    tickets, answers, arms = tmp / "tickets", tmp / "answers", tmp / "arms"
    for i in range(1, 9):
        t = f"T{i}"
        pkg = tickets / "gct" / t
        pkg.mkdir(parents=True)
        review = t == review_ticket
        levels = ["S1"] if review else ["S0", "S1", "S2", "S3"]
        for s in levels:
            (pkg / f"{s}.md").write_text(f"{t} {s}\n")
        meta = {"id": t, "repo": "Natenc12/gct-lab", "base_ref": f"base/{t}", "s3_base_ref": None if review else f"base/{t}-s3",
                "db": "postgres", "deliverable": "review_report" if review else "pull_request"}  # fmt: skip
        (pkg / "meta.json").write_text(json.dumps(meta))
        (answers / "gct" / t).mkdir(parents=True)
        (answers / "gct" / t / "replies.md").write_text(f"# {t}\n\n## {t}-q\nWhen: x\nReply: y\n")
    for a in ("P1", "P1R", "P2", "P3", "P4"):
        (arms / a).mkdir(parents=True)
    return tickets, answers, arms


def test_build_sheet_joins_common_and_ticket_replies(tmp_path):
    _, answers, _ = ticket_tree(tmp_path)
    text = build_sheet.build("gct", "T5", answers)
    out = tmp_path / "sheet.md"
    out.write_text(text)
    ids = [r["id"] for r in owner.parse_sheet(out)]
    assert ids[0] == "default" and ids[-1] == "T5-q" and "applied-migration-plan" in ids
    (answers / "gct" / "T5" / "replies.md").write_text("## open-decision\nReply: y\n")
    with pytest.raises(ValueError, match="must start with 'T5-'"):
        build_sheet.build("gct", "T5", answers)
    (answers / "gct" / "T5" / "replies.md").write_text("## default\nReply: y\n")
    with pytest.raises(ValueError):
        build_sheet.build("gct", "T5", answers)


def test_make_plan_three_parts_and_ceilings(tmp_path):
    tickets, answers, arms = ticket_tree(tmp_path)
    out = tmp_path / "results" / "stage-1"
    args = [
        "stage-1",
        "--tickets-root",
        str(tickets),
        "--answers-root",
        str(answers),
        "--arms-root",
        str(arms),
        "--out-dir",
        str(out),
    ]
    assert make_plan.main(args) == 0
    plan = json.loads((out / "plan.json").read_text())
    meter = json.loads((out / "plan-meter.json").read_text())
    assert plan["budget_tokens"] == 24_000_000 and plan["stage"] == "stage-1"
    assert plan["defaults"] == {"model": "claude-opus-5-5", "judge_model": "claude-opus-5-5", "effort": "medium"}
    assert [r["run_id"] for r in meter["runs"]] == ["p0-t1-1", "p1-t1-1", "p1r-t1-1", "p3-t1-1", "p2-t1-1", "p4-t1-1"]
    parts = plan["parts"]
    assert len(parts["meter"]) == 6 and len(parts["wave1"]) == 42 + 21 and len(parts["wave2"]) == 7
    assert parts["wave2_arm"] is None and len(plan["runs"]) == 69
    runs = {r["run_id"]: r for r in plan["runs"]}
    assert len(runs) == 69 and not any(r.startswith("<best>") for r in runs)
    assert "p0s2-t8-1" not in runs and "p0-t8-1" in runs and "p0s3-t7-1" in runs
    assert {r["ceiling"] for k, r in runs.items() if k.startswith("p0")} == {400_000}
    assert (runs["p1-t2-1"]["ceiling"], runs["p1r-t2-1"]["ceiling"], runs["p2-t2-1"]["ceiling"],
            runs["p3-t2-1"]["ceiling"], runs["p4-t2-1"]["ceiling"]) == (500_000, 600_000, 700_000, 700_000, 1_600_000)  # fmt: skip
    assert runs["p0s3-t3-1"]["base"] == "base/T3-s3" and runs["p0s3-t3-1"]["ticket"].endswith("gct/T3/S3.md")
    assert runs["p0-t3-1"]["base"] == "base/T3" and "arm" not in runs["p0-t3-1"]
    assert runs["p3-t3-1"]["arm"].endswith("arms/P3") and runs["p3-t3-1"]["db"] == "postgres"
    sheet = Path(runs["p3-t3-1"]["reply_sheet"])
    assert sheet.name == "gct-T3.md" and "T3-q" in sheet.read_text()

    assert make_plan.main([*args, "--best-process", "P1R"]) == 0
    plan = json.loads((out / "plan.json").read_text())
    runs = {r["run_id"]: r for r in plan["runs"]}
    assert len(runs) == 76 and runs["p1rs3-t1-1"]["ceiling"] == 600_000 and "p1rs3-t8-1" not in runs


def test_make_plan_refuses_when_packages_are_missing(tmp_path, capsys):
    tickets, answers, arms = ticket_tree(tmp_path)
    (tickets / "gct" / "T4" / "meta.json").unlink()
    (arms / "P2").rmdir()
    args = ["stage-1", "--tickets-root", str(tickets), "--answers-root", str(answers), "--arms-root", str(arms),
            "--out-dir", str(tmp_path / "out")]  # fmt: skip
    assert make_plan.main(args) == 1
    err = capsys.readouterr().err
    assert "T4" in err and "arm P2" in err and not (tmp_path / "out" / "plan.json").exists()
