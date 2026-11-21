"""One run end to end against the fake `claude`: clean room, stop-and-reply, limits, ceiling, records."""

import json

from harness import run, scan, stage
from harness.common import read_json
from tests.conftest import calls, run_args, scenario


def record(env, run_id):
    return read_json(env["runs"] / "test" / run_id / "harness" / "run.json")


def sessions(env):
    return [c for c in calls(env) if "stream-json" in c["argv"]]


def test_stop_reply_resume_and_records(lab_env, practice):
    scenario(lab_env, p1_t1_1=["stop", "finish"])
    assert run.main(run_args(lab_env, practice, "p1-t1-1", "--arm", "harness/examples")) == 0
    rec = record(lab_env, "p1-t1-1")
    assert rec["status"] == "finished" and rec["stops"] == 1
    # Two invocations of 4300 cache write + 5 in + 60 out, from the result records (not the repeated messages).
    assert rec["tokens"] == {"input": 10, "output": 120, "cache_write": 8600, "cache_read": 68000, "counted": 8730}
    assert rec["cost_usd"] == 0.02 and rec["turns"] == 4
    assert rec["judge_tokens"]["counted"] == 903 and rec["judge_model"] == "fake-judge"
    assert rec["branch"] == "p1-t1-1/work" and rec["practice_base_commit"] == practice["main"]
    assert rec["lab_commit"] and rec["session_id"] and rec["model"] == "fake-model"
    assert rec["claude_code_version"] == "0.0.0-fake"

    first, second = sessions(lab_env)
    assert first["argv"][first["argv"].index("--session-id") + 1] == rec["session_id"]
    assert second["argv"][second["argv"].index("--resume") + 1] == rec["session_id"]
    assert second["stdin"] == "Go with your recommendation and stay within the ticket's scope."
    assert "TICKET.md" in first["stdin"] and "STOP:" in first["stdin"]
    for c in (first, second):
        argv = c["argv"]
        assert argv[argv.index("--setting-sources") + 1] == ""
        assert {"--disable-slash-commands", "--strict-mcp-config", "--no-chrome"} <= set(argv)
        assert argv[argv.index("--permission-mode") + 1] == "dontAsk"
        assert argv[argv.index("--settings") + 1].endswith(".control/p1-t1-1/settings.json")
        assert argv[argv.index("--model") + 1] == "fake-model"
        assert "WebFetch" not in argv[argv.index("--tools") + 1]
        assert "CLAUDECODE" not in c["env"], "the parent session's environment leaked into the run"
        assert c["cwd"].endswith("p1-t1-1/repo")
    assert "--append-system-prompt" in first["argv"]

    log = [
        json.loads(line) for line in (lab_env["runs"] / "test/p1-t1-1/harness/owner-log.jsonl").read_text().splitlines()
    ]
    assert len(log) == 1
    entry = log[0]
    assert entry["reply_id"] == "default" and entry["judge_model"] == "fake-judge"
    assert entry["reply_text"] == "Go with your recommendation and stay within the ticket's scope."
    assert "p1-t1-1" not in entry["question"] and "[redacted]" in entry["question"]
    page = (lab_env["runs"] / "test/p1-t1-1/harness" / entry["page_file"]).read_text()
    assert "Fix the CLI too?" in page and "p1-t1-1" not in page
    judge = [c for c in calls(lab_env) if "stream-json" not in c["argv"]][0]
    assert judge["argv"][judge["argv"].index("--tools") + 1] == ""
    assert "p1-t1-1" not in judge["stdin"] and "examples" not in judge["stdin"]
    transcript = (lab_env["runs"] / "test/p1-t1-1/harness/transcript.jsonl").read_text()
    assert transcript.count('"type": "result"') == 2

    # Re-running a finished run does nothing.
    assert run.main(run_args(lab_env, practice, "p1-t1-1")) == 0
    assert len(sessions(lab_env)) == 2


def test_stop_cap(lab_env, practice):
    scenario(lab_env, p1_t1_1=["stop"])
    assert run.main(run_args(lab_env, practice, "p1-t1-1", "--max-stops", "2")) == 0
    rec = record(lab_env, "p1-t1-1")
    assert rec["status"] == "finished" and rec["stop_cap_hit"] and rec["stops"] == 2
    assert len(sessions(lab_env)) == 3


def test_judge_fallback_is_flagged(lab_env, practice, monkeypatch):
    monkeypatch.setenv("FAKE_JUDGE", "I would say maybe")
    scenario(lab_env, p1_t1_1=["stop", "finish"])
    assert run.main(run_args(lab_env, practice, "p1-t1-1")) == 0
    entry = json.loads((lab_env["runs"] / "test/p1-t1-1/harness/owner-log.jsonl").read_text())
    assert entry["judge_fallback"] is True and entry["reply_id"] == "default" and len(entry["judge_answers"]) == 2


def test_plan_limit_then_resume(lab_env, practice):
    scenario(lab_env, p1_t1_1=["stop", "limit", "finish"])
    assert run.main(run_args(lab_env, practice, "p1-t1-1")) == 75
    rec = record(lab_env, "p1-t1-1")
    assert rec["status"] == "plan_limit" and rec["resets_at"] and rec["stops"] == 1
    assert run.main(run_args(lab_env, practice, "p1-t1-1")) == 0
    rec = record(lab_env, "p1-t1-1")
    assert rec["status"] == "finished" and len(rec["invocations"]) == 3
    s = sessions(lab_env)
    assert s[2]["argv"][s[2]["argv"].index("--resume") + 1] == rec["session_id"]
    assert s[2]["stdin"] == run.CONTINUE


def test_ceiling_stops_the_session(lab_env, practice):
    scenario(lab_env, p1_t1_1=["big"])
    assert run.main(run_args(lab_env, practice, "p1-t1-1")) == 0
    rec = record(lab_env, "p1-t1-1")
    assert rec["status"] == "ceiling_hit"
    assert 400000 < rec["tokens"]["counted"] < 600000, "the session should be stopped soon after the ceiling"
    lines = (lab_env["runs"] / "test/p1-t1-1/harness/transcript.jsonl").read_text().count("msg_big_")
    assert lines < 50


def test_crash_is_a_harness_fault_and_fresh_restarts(lab_env, practice):
    scenario(lab_env, p1_t1_1=["crash"])
    assert run.main(run_args(lab_env, practice, "p1-t1-1")) == 1
    assert record(lab_env, "p1-t1-1")["status"] == "harness_fault"
    assert run.main(run_args(lab_env, practice, "p1-t1-1")) == 1  # refuses without --fresh
    scenario(lab_env, p1_t1_1=["finish"])
    assert run.main(run_args(lab_env, practice, "p1-t1-1", "--fresh")) == 0
    assert record(lab_env, "p1-t1-1")["status"] == "finished"


def test_leak_scan(lab_env, practice, monkeypatch):
    monkeypatch.setenv("FAKE_LEAK_PATH", str(lab_env["runs"] / "test" / "p2-t1-1" / "repo" / "answers.md"))
    scenario(lab_env, p1_t1_1=["leak"], p1_t1_2=["finish"])
    run.main(run_args(lab_env, practice, "p1-t1-1"))
    run.main(run_args(lab_env, practice, "p1-t1-2"))
    bad = lab_env["runs"] / "test" / "p1-t1-1"
    assert scan.main([str(bad)]) == 2
    report = read_json(bad / "harness" / "scan.json")
    assert report["clean"] is False
    assert [o["tool"] for o in report["offences"]] == ["Read"]
    assert [o["input"]["command"] for o in report["blocked_attempts"]] == ["gh pr list"]
    assert report["offences"][0]["line"] > 0
    assert "github token" not in json.dumps(report).lower()
    good = lab_env["runs"] / "test" / "p1-t1-2"
    assert scan.main([str(good)]) == 0 and read_json(good / "harness" / "scan.json")["clean"] is True


def write_plan(env, practice, tmp_path, budget, runs):
    plan = {
        "stage": "test",
        "budget_tokens": budget,
        "parallel": 2,
        "defaults": {
            "ticket": str(env["ticket"]),
            "repo": "example/lab",
            "repo_url": practice["url"],
            "base": "main",
            "model": "fake-model",
            "judge_model": "fake-judge",
            "ceiling": 400000,
            "claude_bin": env["claude"],
            "gh_bin": env["gh"],
        },
        "runs": [{"run_id": r} for r in runs],
    }
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    return str(path)


def test_stage_runs_retries_limits_and_skips_done(lab_env, practice, tmp_path, capsys):
    scenario(lab_env, p0_t1_1=["finish"], p1_t1_1=["limit", "finish"], p2_t1_1=["stop", "finish"])
    plan = write_plan(lab_env, practice, tmp_path, 10_000_000, ["p0-t1-1", "p1-t1-1", "p2-t1-1"])
    assert stage.main([plan, "--poll-seconds", "0.2"]) == 0
    out = capsys.readouterr().out
    assert "plan or rate limit" in out
    summary = read_json(lab_env["runs"] / "test" / "stage.json")
    assert summary["runs"] == {"p0-t1-1": "finished", "p1-t1-1": "finished", "p2-t1-1": "finished"}
    n = len(sessions(lab_env))
    assert stage.main([plan, "--poll-seconds", "0.2"]) == 0
    assert len(sessions(lab_env)) == n, "finished runs must be skipped on re-invoke"
    assert "3 already done" in capsys.readouterr().out


def test_stage_halts_new_starts_at_80_percent(lab_env, practice, tmp_path, capsys):
    scenario(lab_env, p0_t1_1=["finish"], p0_t1_2=["finish"], p0_t1_3=["finish"], p0_t1_4=["finish"])
    plan = write_plan(lab_env, practice, tmp_path, 5000, ["p0-t1-1", "p0-t1-2", "p0-t1-3", "p0-t1-4"])
    assert stage.main([plan, "--poll-seconds", "0.2", "--parallel", "1"]) == 3
    out = capsys.readouterr().out
    assert "HALT" in out and "No new runs will start" in out
    summary = read_json(lab_env["runs"] / "test" / "stage.json")
    assert summary["halted"] and list(summary["runs"].values()).count("finished") == 1


def test_scan_flags_tokens_and_gh_auth_from_programs(lab_env, practice):
    scenario(lab_env, p1_t1_1=["token"])
    run.main(run_args(lab_env, practice, "p1-t1-1"))
    folder = lab_env["runs"] / "test" / "p1-t1-1"
    assert scan.main([str(folder)]) == 2
    reasons = [(o["tool"], o["reason"]) for o in read_json(folder / "harness" / "scan.json")["offences"]]
    assert ("Bash", "asks gh or git for GitHub credentials") in reasons
    assert reasons.count(("Bash", "tool output contains a GitHub token")) == 2


def test_claude_gets_default_sigint_even_when_the_harness_inherited_it_ignored(lab_env, practice):
    """A stage started in the background inherits SIGINT ignored; runs must not (gct-lab tests send SIGINT)."""
    import signal

    scenario(lab_env, p1_t1_1=["stop", "finish"])
    saved = {sig: signal.signal(sig, signal.SIG_IGN) for sig in (signal.SIGINT, signal.SIGQUIT)}
    try:
        assert run.main(run_args(lab_env, practice, "p1-t1-1")) == 0
        assert signal.getsignal(signal.SIGINT) == signal.SIG_IGN, "the harness's own handling must not change"
    finally:
        for sig, old in saved.items():
            signal.signal(sig, old)
    seen = calls(lab_env)
    assert len(seen) == 3  # session, reply judge, resumed session
    assert all(c["signals"] == {"SIGINT": "default", "SIGQUIT": "default"} for c in seen), seen
