"""Usage counting, STOP lines, limits, reply sheets and stripping."""

import json

import pytest

from harness import owner
from harness.stream import StreamState, Usage, find_page, find_stop


def test_usage_counts_each_message_once_and_prefers_result_totals():
    s = StreamState()
    u = {"input_tokens": 2, "output_tokens": 5, "cache_creation_input_tokens": 100, "cache_read_input_tokens": 900}
    for _ in range(3):
        s.feed(json.dumps({"type": "assistant", "message": {"id": "m1", "content": [], "usage": u}}))
    assert s.live_usage() == Usage(2, 5, 100, 900)
    assert s.live_usage().counted == 107
    mu = {"a": {"inputTokens": 4, "outputTokens": 400, "cacheCreationInputTokens": 3000, "cacheReadInputTokens": 9}}
    s.feed(json.dumps({"type": "result", "is_error": False, "result": "ok", "modelUsage": mu, "total_cost_usd": 0.5}))
    assert s.final_usage() == Usage(4, 400, 3000, 9)
    assert s.cost_usd == 0.5


def test_turns_add_up_over_every_result_in_one_call():
    # A background subagent makes the CLI write a second result in the same call (real trial, 2026-11-21).
    s = StreamState()
    s.feed(json.dumps({"type": "result", "is_error": False, "num_turns": 7, "result": "waiting for the agent"}))
    s.feed(json.dumps({"type": "result", "is_error": False, "num_turns": 1, "result": "STOP: continue?"}))
    assert s.turns == 8 and find_stop(s.text) == "STOP: continue?"


def test_bad_lines_are_skipped():
    s = StreamState()
    s.feed("not json")
    s.feed("")
    assert s.bad_lines == 1


@pytest.mark.parametrize(
    "text,expected",
    [
        ("All done.", None),
        (
            "Plan ready.\nSTOP: approve the plan? page: scratch/plan.html",
            "STOP: approve the plan? page: scratch/plan.html",
        ),
        ("STOP 2: merge brief ready — page: runs/x/brief.html", "STOP 2: merge brief ready — page: runs/x/brief.html"),
        ("**STOP ask:** which format?", "STOP ask:** which format?"),
        ("Don't STOP: this is mid-line", None),
    ],
)
def test_find_stop(text, expected):
    assert find_stop(text) == expected


def test_find_page():
    assert find_page("STOP: ok? page: `scratch/brief.html`.") == "scratch/brief.html"
    assert find_page("STOP: ok?") is None


def test_plan_limit_detection():
    s = StreamState()
    s.feed(json.dumps({"type": "rate_limit_event", "rate_limit_info": {"status": "rejected", "resetsAt": 1795345200}}))
    s.feed(json.dumps({"type": "result", "is_error": True, "result": "Claude AI usage limit reached|1795345200"}))
    assert s.plan_limited() and s.resets_at() == 1795345200
    ok = StreamState()
    ok.feed(json.dumps({"type": "rate_limit_event", "rate_limit_info": {"status": "allowed"}}))
    ok.feed(json.dumps({"type": "result", "is_error": False, "result": "fine"}))
    assert not ok.plan_limited()
    session = StreamState()
    session.feed(
        json.dumps({"type": "result", "is_error": True, "result": "You've hit your session limit · resets 3:45pm"})
    )
    assert session.plan_limited()
    other = StreamState()
    other.feed(json.dumps({"type": "result", "is_error": True, "subtype": "error_during_execution", "result": ""}))
    assert not other.plan_limited()


def test_reply_sheet_and_judge_prompt(tmp_path):
    sheet = owner.parse_sheet(owner.Path(__file__).resolve().parents[1] / "harness/examples/reply-sheet.md")
    assert [r["id"] for r in sheet] == ["default", "final"]
    assert sheet[0]["text"] == "Go with your recommendation and stay within the ticket's scope."
    assert sheet[1]["text"] == "Thanks. Leave the pull request open and stop."
    prompt = owner.judge_prompt(sheet, "STOP: approve?", "the page")
    assert "id: final" in prompt and "the page" in prompt
    bad = tmp_path / "bad.md"
    bad.write_text("## a\nWhen: x\n")
    with pytest.raises(ValueError):
        owner.parse_sheet(bad)


def test_redact_and_pick():
    text = "Run P3-t4-1 (arm p3, branch p3-t4-1/work) used contract-first; p30 stays."
    out = owner.redact(text, ["p3-t4-1", "p3", "p3-t4-1/work", "contract-first"])
    assert "p3" not in out.lower().replace("p30", "") and "contract-first" not in out
    assert "p30" in out
    assert owner.pick_id("final", ["default", "final"]) == "final"
    assert owner.pick_id("I pick `default`.", ["default", "final"]) == "default"
    assert owner.pick_id("default or final", ["default", "final"]) is None


def test_page_text_strips_html(tmp_path):
    p = tmp_path / "a.html"
    p.write_text("<html><style>x{}</style><body><h1>Title</h1><p>A &amp; B</p></body></html>")
    assert owner.page_text(p).split() == ["Title", "A", "&", "B"]
