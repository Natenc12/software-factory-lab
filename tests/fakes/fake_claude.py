"""A stand-in for the `claude` command, so tests need no login and spend nothing.

Session calls (`-p --output-format stream-json`) play one step per invocation from a scenario:
FAKE_SCENARIO_FILE maps a run id (found from the working folder, <run-id>/repo) to a list of steps.
Steps: finish, stop, limit, big, crash, leak, token, probe_tester. Record shapes copy a real 2.1.302
trial (2026-11-21). probe_tester runs the tester agent's own PreToolUse hooks from `--agents` on a
fixed set of tool calls, as Claude Code does, and logs each call and its result as a subagent's.
Judge calls (`--output-format json`) answer FAKE_JUDGE (default "default"), or play the answers listed in
the JSON file FAKE_JUDGE_SEQ, one per call.
Every call is logged to FAKE_LOG as JSON: argv, stdin, env keys, cwd.
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def emit(rec: dict) -> None:
    sys.stdout.write(json.dumps(rec) + "\n")
    sys.stdout.flush()


def usage(i: int, o: int, cw: int, cr: int) -> dict:
    return {"input_tokens": i, "output_tokens": o, "cache_creation_input_tokens": cw, "cache_read_input_tokens": cr}


def assistant(sid: str, mid: str, content: list, u: dict) -> dict:
    return {"type": "assistant", "session_id": sid, "message": {"id": mid, "content": content, "usage": u}}


def result(sid: str, text: str, i: int, o: int, cw: int, cr: int, is_error: bool = False, cost: float = 0.01) -> dict:
    """`usage` covers this call; `modelUsage` and `total_cost_usd` are session totals, as in the real CLI."""
    totals = Path(os.environ.get("FAKE_STATE", "/nonexistent")) / f"session-{sid}.json"
    prev = json.loads(totals.read_text()) if totals.exists() else [0, 0, 0, 0, 0.0]
    cum = [prev[0] + i, prev[1] + o, prev[2] + cw, prev[3] + cr, prev[4] + cost]
    if totals.parent.is_dir():
        totals.write_text(json.dumps(cum))
    return {
        "type": "result",
        "subtype": "success",
        "is_error": is_error,
        "session_id": sid,
        "result": text,
        "num_turns": 2,
        "total_cost_usd": cum[4],
        "usage": usage(i, o, cw, cr),
        "modelUsage": {
            "fake-model": {
                "inputTokens": cum[0],
                "outputTokens": cum[1],
                "cacheCreationInputTokens": cum[2],
                "cacheReadInputTokens": cum[3],
            }
        },
    }


TESTER_PROBES = [
    ("Read", {"file_path": "src/app.py"}),
    ("Read", {"file_path": "tests/test_app.py"}),
    ("Grep", {"pattern": "def ", "path": "."}),
    ("Read", {"file_path": "../scratch/team/contract.md"}),
    ("Read", {"file_path": "tests/conftest.py"}),
    ("Write", {"file_path": "tests/test_ticket_acceptance.py", "content": "def test_x(): pass\n"}),
    ("Write", {"file_path": "src/app.py", "content": "hacked = True\n"}),
]


def run_agent_hooks(spec: dict, tool: str, inp: dict) -> str | None:
    """Run an agent's PreToolUse hooks for one tool call; return the deny reason, if any."""
    for group in spec.get("hooks", {}).get("PreToolUse", []):
        if group.get("matcher", "*") not in ("*", "", tool) and tool not in group["matcher"].split("|"):
            continue
        for h in group["hooks"]:
            data = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": inp, "cwd": os.getcwd()}
            out = subprocess.run(h["command"], shell=True, input=json.dumps(data), capture_output=True, text=True)
            if out.returncode == 2:
                return out.stderr.strip()
            if out.stdout.strip():
                d = json.loads(out.stdout).get("hookSpecificOutput", {})
                if d.get("permissionDecision") == "deny":
                    return d.get("permissionDecisionReason", "denied")
    return None


def main() -> int:
    argv = sys.argv[1:]
    stdin = sys.stdin.read()
    log = os.environ.get("FAKE_LOG")
    if log:
        with open(log, "a") as f:
            disposition = {
                name: "ignored" if signal.getsignal(getattr(signal, name)) == signal.SIG_IGN else "default"
                for name in ("SIGINT", "SIGQUIT")
            }
            record = {
                "argv": argv,
                "stdin": stdin,
                "env": sorted(os.environ),
                "cwd": os.getcwd(),
                "signals": disposition,
            }
            f.write(json.dumps(record) + "\n")
    fmt = argv[argv.index("--output-format") + 1] if "--output-format" in argv else "text"
    if fmt == "json":
        answer = os.environ.get("FAKE_JUDGE", "default")
        seq = os.environ.get("FAKE_JUDGE_SEQ")
        if seq:  # a JSON list of answers, one per call, the last one repeated
            answers = json.loads(Path(seq).read_text())
            counter = Path(seq + ".count")
            n = int(counter.read_text()) if counter.exists() else 0
            counter.write_text(str(n + 1))
            answer = answers[min(n, len(answers) - 1)]
        print(json.dumps(result("judge", answer, 900, 3, 0, 0, cost=0.002)))
        return 0

    sid = argv[argv.index("--resume") + 1] if "--resume" in argv else argv[argv.index("--session-id") + 1]
    run_id = Path(os.getcwd()).parent.name
    steps = json.loads(Path(os.environ["FAKE_SCENARIO_FILE"]).read_text())[run_id]
    counter = Path(os.environ["FAKE_STATE"]) / f"{run_id}.count"
    n = int(counter.read_text()) if counter.exists() else 0
    counter.write_text(str(n + 1))
    step = steps[min(n, len(steps) - 1)]

    emit(
        {
            "type": "system",
            "subtype": "init",
            "session_id": sid,
            "claude_code_version": "0.0.0-fake",
            "skills": [],
            "plugins": [],
            "tools": ["Bash"],
        }
    )
    if step == "crash":
        sys.stderr.write("fake crash\n")
        return 1
    if step == "limit":
        info = {"status": "rejected", "resetsAt": int(time.time()) - 60, "rateLimitType": "five_hour"}
        emit({"type": "rate_limit_event", "session_id": sid, "rate_limit_info": info})
        emit(result(sid, f"Claude AI usage limit reached|{int(time.time()) - 60}", 0, 0, 0, 0, is_error=True, cost=0))
        return 1
    if step == "big":
        for k in range(200):
            emit(assistant(sid, f"msg_big_{k}", [{"type": "text", "text": "..."}], usage(10, 5, 50000, 1000)))
            time.sleep(0.02)
        emit(result(sid, "done", 2000, 1000, 10_000_000, 200000))
        return 0
    u = usage(3, 20, 4000, 15000)
    tool = {"type": "tool_use", "id": f"toolu_{n}", "name": "Bash", "input": {"command": "git status"}}
    # The same API message arrives twice, as the real CLI does; usage must be counted once.
    emit(assistant(sid, f"msg_{n}", [{"type": "thinking", "thinking": ""}], u))
    emit(assistant(sid, f"msg_{n}", [tool], u))
    emit(
        {
            "type": "user",
            "session_id": sid,
            "message": {"content": [{"type": "tool_result", "tool_use_id": f"toolu_{n}", "content": "clean"}]},
        }
    )
    if step == "leak":
        leak = os.environ.get("FAKE_LEAK_PATH", "/nowhere/answers/key.md")
        calls = [
            {"type": "tool_use", "id": "toolu_leak", "name": "Read", "input": {"file_path": leak}},
            {"type": "tool_use", "id": "toolu_gh", "name": "Bash", "input": {"command": "gh pr list"}},
        ]
        emit(assistant(sid, f"msg_leak_{n}", calls, usage(2, 10, 100, 100)))
        results = [
            {"type": "tool_result", "tool_use_id": "toolu_leak", "content": "secret answers"},
            {
                "type": "tool_result",
                "tool_use_id": "toolu_gh",
                "is_error": True,
                "content": "PreToolUse:Bash hook error: Blocked by the lab guard: gh",
            },
        ]
        emit({"type": "user", "session_id": sid, "message": {"content": results}})
    if step == "token":
        code = (
            "import subprocess; print(subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True).stdout)"
        )
        calls = [
            {"type": "tool_use", "id": "toolu_tok", "name": "Bash", "input": {"command": f'python3 -c "{code}"'}},
            {"type": "tool_use", "id": "toolu_env", "name": "Bash", "input": {"command": "env | sort"}},
        ]
        emit(assistant(sid, f"msg_tok_{n}", calls, usage(2, 10, 100, 100)))
        fake = "gho_" + "A1b2C3d4" * 5
        results = [
            {"type": "tool_result", "tool_use_id": "toolu_tok", "content": fake},
            {"type": "tool_result", "tool_use_id": "toolu_env", "content": f"GH_TOKEN={fake}\nHOME=/x"},
        ]
        emit({"type": "user", "session_id": sid, "message": {"content": results}})
    if step == "probe_tester":
        agents = json.loads(Path(argv[argv.index("--agents") + 1]).read_text())
        parent = "toolu_agent_tester"
        start = {"type": "tool_use", "id": parent, "name": "Task", "input": {"subagent_type": "tester"}}
        emit(assistant(sid, "msg_probe_start", [start], usage(1, 5, 10, 10)))
        for k, (tool, inp) in enumerate(TESTER_PROBES):
            call = {"type": "tool_use", "id": f"toolu_probe_{k}", "name": tool, "input": inp}
            rec = assistant(sid, f"msg_probe_{k}", [call], usage(1, 5, 10, 10))
            emit({**rec, "parent_tool_use_id": parent})
            deny = run_agent_hooks(agents["tester"], tool, inp)
            if deny:
                res = {"tool_use_id": call["id"], "is_error": True, "content": f"PreToolUse:{tool} hook error: {deny}"}
            else:
                res = {"tool_use_id": call["id"], "content": "allowed"}
            emit({"type": "user", "session_id": sid, "parent_tool_use_id": parent,
                  "message": {"content": [{"type": "tool_result", **res}]}})  # fmt: skip
    if step == "skill":
        call = {"type": "tool_use", "id": "toolu_skill", "name": "Skill", "input": {"skill": "work:release-note"}}
        # Streaming repeats the record; the skill must be counted once.
        emit(assistant(sid, f"msg_skill_{n}", [call], usage(2, 10, 100, 100)))
        emit(assistant(sid, f"msg_skill_{n}", [call], usage(2, 10, 100, 100)))
        done = {"type": "tool_result", "tool_use_id": "toolu_skill", "content": "Launching skill: work:release-note"}
        emit({"type": "user", "session_id": sid, "message": {"content": [done]}})
        later = {"type": "tool_use", "id": "toolu_skill2", "name": "Skill", "input": {"skill": "work:sql-style"}}
        emit(assistant(sid, f"msg_skill2_{n}", [later], usage(2, 10, 100, 100)))
    if step == "stop":
        page = Path(os.getcwd()).parent / "scratch" / f"ask-{n}.html"
        page.write_text(f"<html><body><h1>Question from {run_id}</h1><p>Fix the CLI too?</p></body></html>")
        text = f"I found a second bug in the CLI.\nSTOP: Run {run_id} asks: fix it too? page: ../scratch/ask-{n}.html"
    else:
        text = "Opened the pull request. Done."
    emit(assistant(sid, f"msg_{n}_b", [{"type": "text", "text": text}], usage(2, 40, 300, 19000)))
    emit(result(sid, text, 5, 60, 4300, 34000))
    return 0


if __name__ == "__main__":
    sys.exit(main())
