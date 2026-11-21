"""A stand-in for the `claude` command, so tests need no login and spend nothing.

Session calls (`-p --output-format stream-json`) play one step per invocation from a scenario:
FAKE_SCENARIO_FILE maps a run id (found from the working folder, <run-id>/repo) to a list of steps.
Steps: finish, stop, limit, big, crash, leak. Record shapes copy a real 2.1.302 trial (2026-11-21).
Judge calls (`--output-format json`) answer FAKE_JUDGE (default "default").
Every call is logged to FAKE_LOG as JSON: argv, stdin, env keys, cwd.
"""

import json
import os
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
    return {
        "type": "result",
        "subtype": "success",
        "is_error": is_error,
        "session_id": sid,
        "result": text,
        "num_turns": 2,
        "total_cost_usd": cost,
        "usage": usage(i, o, cw, cr),
        "modelUsage": {
            "fake-model": {
                "inputTokens": i,
                "outputTokens": o,
                "cacheCreationInputTokens": cw,
                "cacheReadInputTokens": cr,
            }
        },
    }


def main() -> int:
    argv = sys.argv[1:]
    stdin = sys.stdin.read()
    log = os.environ.get("FAKE_LOG")
    if log:
        with open(log, "a") as f:
            f.write(json.dumps({"argv": argv, "stdin": stdin, "env": sorted(os.environ), "cwd": os.getcwd()}) + "\n")
    fmt = argv[argv.index("--output-format") + 1] if "--output-format" in argv else "text"
    if fmt == "json":
        answer = os.environ.get("FAKE_JUDGE", "default")
        print(json.dumps(result("judge", answer, 900, 3, 0, 0, cost=0.002)))
        return 0

    sid = argv[argv.index("--resume") + 1] if "--resume" in argv else argv[argv.index("--session-id") + 1]
    run_id = Path(os.getcwd()).parent.name
    steps = json.loads(Path(os.environ["FAKE_SCENARIO_FILE"]).read_text())[run_id]
    counter = Path(os.environ["FAKE_STATE"]) / f"{run_id}.count"
    n = int(counter.read_text()) if counter.exists() else 0
    counter.write_text(str(n + 1))
    step = steps[min(n, len(steps) - 1)]

    emit({"type": "system", "subtype": "init", "session_id": sid, "skills": [], "plugins": [], "tools": ["Bash"]})
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
