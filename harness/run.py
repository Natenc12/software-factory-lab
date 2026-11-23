"""Start (or continue) one run as its own headless Claude Code session.

    python -m harness.run p3-t4-1 --stage stage-1 --arm arms/P3 --ticket tickets/gct/T4.md \\
        --repo Natenc12/gct-lab --base t4-start --model claude-opus-5-5 --ceiling 700000 \\
        --reply-sheet answers/reply-sheet.md --db postgres

Re-running the same command continues a run that stopped on a plan limit and does nothing for a run that
is already finished. Exit codes: 0 finished or ceiling_hit, 75 plan_limit (retry later), 1 harness_fault.
"""

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from harness import owner, sandbox
from harness.common import (
    FINAL,
    LAB_ROOT,
    append_jsonl,
    check_stage,
    default_signals,
    git_head,
    lab_commit,
    now_iso,
    parse_run_id,
    read_json,
    run_dir,
    runs_root,
    write_json,
)
from harness.stream import StreamState, Usage, find_page, find_stop, skills_used, subagents_started

HERE = Path(__file__).resolve().parent
EXIT = {"finished": 0, "ceiling_hit": 0, "plan_limit": 75, "harness_fault": 1}
CONTINUE = "The session was paused by a usage limit and has now resumed. Carry on from where you stopped."
KEEP_ENV = ("HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "SHELL")


def clean_env(root: Path, extra: dict) -> dict:
    """A minimal environment: nothing from the parent Claude session, the run's `lab` first on PATH."""
    env = {k: os.environ[k] for k in KEEP_ENV if k in os.environ}
    for k in filter(None, os.environ.get("HARNESS_PASS_ENV", "").split(",")):
        if k in os.environ:
            env[k] = os.environ[k]
    parts = [p for p in os.environ.get("PATH", "").split(":") if p and str(LAB_ROOT) not in p and "/.claude/" not in p]
    env["PATH"] = ":".join([str(sandbox.control_dir(root) / "bin"), *parts])
    env["TMPDIR"] = str(root / "scratch" / "tmp")
    env["TERM"] = "dumb"
    env["DISABLE_AUTOUPDATER"] = "1"
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    env.update(extra)
    return env


def session_cmd(a, root: Path, prompt_resume: str | None) -> list[str]:
    ctl = sandbox.control_dir(root)
    cmd = [a.claude_bin, "-p", "--output-format", "stream-json", "--verbose", "--model", a.model]
    cmd += ["--setting-sources", "", "--settings", str(ctl / "settings.json")]
    plugin = ctl / "plugin"
    tools = sandbox.ALLOWED_TOOLS.split()
    if plugin.is_dir():
        # An arm with skills: its plugin, the Skill tool, and no --disable-slash-commands (which turns off
        # every skill). Its settings file sets disableBundledSkills, so Claude Code's own skills stay out.
        cmd += ["--plugin-dir", str(plugin)]
        tools.append("Skill")
    else:
        cmd += ["--disable-slash-commands"]
    cmd += ["--strict-mcp-config", "--no-chrome", "--permission-mode", "dontAsk"]
    cmd += ["--tools", ",".join(tools), "--disallowedTools", "WebFetch,WebSearch"]
    cmd += ["--add-dir", str(root)]
    if a.effort:
        cmd += ["--effort", a.effort]
    if (ctl / "arm-prompt.md").exists():
        cmd += ["--append-system-prompt", (ctl / "arm-prompt.md").read_text(encoding="utf-8")]
    if (ctl / "agents.json").exists():
        cmd += ["--agents", str(ctl / "agents.json")]
    cmd += ["--resume", prompt_resume] if prompt_resume else ["--session-id", a._session_id]
    return cmd


def invoke(cmd, prompt, cwd, env, root: Path, budget_left: int, wall_left: float, tick) -> tuple[StreamState, str]:
    """Run one `claude -p` invocation, streaming its records into the transcript.

    Returns the parsed state and how it ended: "result", "ceiling", "wall", or "crash".
    """
    hdir = root / "harness"
    state, ended = StreamState(), {"why": None}
    with open(hdir / "transcript.jsonl", "a", encoding="utf-8") as tr, open(hdir / "stderr.log", "a") as err:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=err,
            text=True,
            start_new_session=True,
            preexec_fn=default_signals,
        )

        def stop(why: str):
            if ended["why"] is None:
                ended["why"] = why
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                return
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)

        timer = threading.Timer(max(wall_left, 1), stop, args=("wall",))
        timer.daemon = True
        timer.start()
        try:
            proc.stdin.write(prompt)
            proc.stdin.close()
        except BrokenPipeError:
            pass
        last = 0.0
        for line in proc.stdout:
            tr.write(line if line.endswith("\n") else line + "\n")
            tr.flush()
            state.feed(line)
            if state.live_usage().counted > budget_left:
                stop("ceiling")
                break
            if time.monotonic() - last > 5:
                last = time.monotonic()
                tick(state)
        proc.stdout.close()
        proc.wait()
        timer.cancel()
    if ended["why"]:
        return state, ended["why"]
    return state, "result" if state.result else "crash"


def stderr_tail(root: Path) -> str:
    try:
        return (root / "harness" / "stderr.log").read_text(errors="replace")[-2000:]
    except FileNotFoundError:
        return ""


def handle_stop(a, root: Path, rec: dict, question: str, env: dict) -> dict:
    """Save and strip the question (and its page), ask the judge, log the reply, return the reply."""
    hdir = root / "harness"
    n = rec["stops"] + 1
    (hdir / "stops").mkdir(exist_ok=True)
    ids = parse_run_id(a.run_id)
    terms = [a.run_id, ids["arm"], f"{a.run_id}/work", *(a.redact or [])]
    if a.arm:
        terms.append(Path(a.arm).name)
    clean_q = owner.redact(question, terms)
    (hdir / "stops" / f"{n}-question.txt").write_text(clean_q + "\n", encoding="utf-8")
    page, page_file = None, None
    rel = find_page(question)
    if rel:
        for base in (root / "repo", root):
            p = Path(os.path.realpath(base / os.path.expanduser(rel)))
            inside = str(p).startswith(str(root) + "/") and not str(p).startswith(str(hdir) + "/")
            if inside and p.is_file():
                page = owner.redact(owner.page_text(p), terms)
                page_file = f"stops/{n}-page.txt"
                (hdir / page_file).write_text(page + "\n", encoding="utf-8")
                break
    sheet = owner.parse_sheet(Path(a.reply_sheet))
    (hdir / "judge").mkdir(exist_ok=True)
    # The judge runs on the owner's side: without the codebase's run_env, which is for the run's toolchain.
    judge_env = {k: v for k, v in clean_env(root, {}).items() if k not in ("LAB_DB", "DATABASE_URL")}
    verdict = owner.ask_judge(
        a.claude_bin,
        a.judge_model,
        owner.judge_prompt(sheet, clean_q, page),
        [r["id"] for r in sheet],
        hdir / "judge",
        judge_env,
    )
    reply = next(r for r in sheet if r["id"] == verdict["id"])
    append_jsonl(
        hdir / "owner-log.jsonl",
        {
            "time": now_iso(),
            "stop": n,
            "question": clean_q,
            "page_file": page_file,
            "reply_id": reply["id"],
            "reply_text": reply["text"],
            "rescue": reply.get("rescue", False),
            "judge_model": a.judge_model,
            "judge_fallback": verdict["fallback"],
            "judge_answers": verdict["answers"],
        },
    )
    rec["judge_tokens"] = (Usage.from_dict(rec.get("judge_tokens")) + verdict["usage"]).as_dict()
    rec["judge_cost_usd"] = round(rec.get("judge_cost_usd", 0) + verdict["cost_usd"], 6)
    rec["stops"] = n
    return reply


def finish_record(root: Path, rec: dict) -> None:
    hdir = root / "harness"
    pr = None
    for line in (hdir / "lab-events.jsonl").read_text().splitlines() if (hdir / "lab-events.jsonl").exists() else []:
        ev = json.loads(line)
        if ev.get("pr"):
            pr = ev["pr"]
    rec["pr_number"] = pr
    if (root / "repo").exists():
        rec["practice_head_commit"] = git_head(root / "repo")
    transcript = hdir / "transcript.jsonl"
    lines = transcript.read_text(errors="replace").splitlines() if transcript.exists() else []
    rec["skills_used"] = skills_used(lines)
    rec["workers"] = subagents_started(lines)
    rec["workers_started"] = len(rec["workers"])
    rec["ended_at"] = now_iso()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m harness.run", description=__doc__.split("\n\n")[0])
    ap.add_argument("run_id", help="<arm>-<ticket>-<repeat>, e.g. p3-t4-1")
    ap.add_argument("--stage", required=True)
    ap.add_argument("--arm", help="the arm's folder; omit for a bare run")
    ap.add_argument("--ticket", required=True, help="the ticket file")
    ap.add_argument("--repo", required=True, help="practice repo on GitHub, owner/name")
    ap.add_argument("--base", required=True, help="base ref (branch, tag or commit) to start from")
    ap.add_argument("--pr-base", help="branch the pull request targets (default: --base)")
    ap.add_argument("--repo-url", help="clone/push URL (default https://github.com/<repo>.git)")
    ap.add_argument("--model", required=True)
    ap.add_argument("--ceiling", type=int, required=True, help="counted-token ceiling for the run")
    ap.add_argument("--reply-sheet", default=str(HERE / "examples" / "reply-sheet.md"))
    ap.add_argument("--judge-model", default="claude-sonnet-5-5")
    ap.add_argument("--max-stops", type=int, default=6)
    ap.add_argument("--db", choices=("sqlite", "postgres", "none"), default="sqlite")
    ap.add_argument("--effort", choices=("low", "medium", "high", "xhigh", "max"))
    ap.add_argument("--prompt-file", default=str(HERE / "prompts" / "run.md"))
    ap.add_argument("--redact", action="append", help="extra term to strip from questions (repeatable)")
    ap.add_argument("--forbid", action="append", default=[], help="extra path the run may not touch (repeatable)")
    ap.add_argument("--allow-domain", action="append", default=[], help="extra host the sandbox may reach")
    ap.add_argument(
        "--setup",
        action="append",
        default=[],
        help="shell command run once in the checkout before the session, with network (repeatable)",
    )
    ap.add_argument(
        "--allow-write", action="append", default=[], help="folder outside the run the sandbox may write (repeatable)"
    )
    ap.add_argument("--env", action="append", default=[], help="KEY=VALUE set in the run's environment (repeatable)")
    ap.add_argument("--max-wall-min", type=float, default=240)
    ap.add_argument("--runs-root", help="default $FACTORY_RUNS_ROOT or ~/factory-runs")
    ap.add_argument("--claude-bin", default=os.environ.get("HARNESS_CLAUDE", "claude"))
    ap.add_argument("--gh-bin", default=os.environ.get("HARNESS_GH") or shutil.which("gh") or "gh")
    ap.add_argument("--fresh", action="store_true", help="remove an earlier attempt of this run and start over")
    a = ap.parse_args(argv)
    try:
        parse_run_id(a.run_id)
        check_stage(a.stage)
        owner.parse_sheet(Path(a.reply_sheet))
    except ValueError as e:
        ap.error(str(e))
    a.claude_bin = shutil.which(a.claude_bin) or a.claude_bin
    root = run_dir(a.stage, a.run_id, a.runs_root)
    hdir = root / "harness"
    rec = read_json(hdir / "run.json")

    if rec and rec.get("status") in FINAL and not a.fresh:
        print(f"{a.run_id}: already {rec['status']}; nothing to do")
        return 0
    if rec and rec.get("status") == "harness_fault" and not a.fresh:
        print(f"{a.run_id}: ended in harness_fault ({rec.get('reason')}); re-run with --fresh to start over")
        return 1
    if a.fresh and root.exists():
        sandbox.teardown(root, everything=True, quiet=True)
        rec = None

    if rec is None:
        if root.exists():
            print(f"{root} exists without a run record; remove it with `python -m harness.sandbox down --all`")
            return 1
        arm = Path(a.arm).resolve() if a.arm else None
        try:
            manifest = sandbox.create(
                root,
                a.run_id,
                repo=a.repo,
                repo_url=a.repo_url or f"https://github.com/{a.repo}.git",
                base=a.base,
                pr_base=a.pr_base or a.base,
                ticket=Path(a.ticket),
                arm=arm,
                db=a.db,
                runs_root=runs_root(a.runs_root),
                gh_bin=a.gh_bin,
                extra_forbidden=a.forbid,
                allow_domains=a.allow_domain,
                allow_write=a.allow_write,
                extra_env=dict(kv.split("=", 1) for kv in a.env),
            )
        except Exception as e:  # noqa: BLE001 - any setup failure is a harness fault, reported plainly
            print(f"{a.run_id}: sandbox setup failed: {e}", file=sys.stderr)
            return 1
        lab = lab_commit()
        rec = {
            "run_id": a.run_id,
            "stage": a.stage,
            "arm": Path(a.arm).name if a.arm else "bare",
            "arm_dir": str(arm) if arm else None,
            "ticket": str(Path(a.ticket).resolve()),
            "repo": a.repo,
            "base_ref": a.base,
            "practice_base_commit": manifest["base_commit"],
            "branch": manifest["branch"],
            "model": a.model,
            "judge_model": a.judge_model,
            "reply_sheet": str(Path(a.reply_sheet).resolve()),
            "ceiling": a.ceiling,
            "max_stops": a.max_stops,
            "lab_commit": lab["commit"],
            "lab_harness_dirty": lab["harness_dirty"],
            "sandbox": str(root),
            "transcript": str(hdir / "transcript.jsonl"),
            "status": "running",
            "reason": None,
            "session_id": None,
            "session_started": False,
            "tokens": Usage().as_dict(),
            "judge_tokens": Usage().as_dict(),
            "cost_usd": 0.0,
            "judge_cost_usd": 0.0,
            "wall_seconds": 0.0,
            "turns": 0,
            "stops": 0,
            "stop_cap_hit": False,
            "pending_prompt": None,
            "invocations": [],
            "started_at": now_iso(),
            "pr_number": None,
        }
        template = Path(a.prompt_file).read_text(encoding="utf-8")
        dbinfo = manifest.get("database") or {}
        rec["pending_prompt"] = template.format(
            branch=manifest["branch"],
            ticket=str(root / "TICKET.md"),
            scratch=str(root / "scratch"),
            database=dbinfo.get("url") or dbinfo.get("path") or "none",
            run_folder=str(root),
        )
        write_json(hdir / "run.json", rec)

    manifest = read_json(hdir / "sandbox.json")
    env = clean_env(root, manifest.get("env") or {})
    if a.setup and "setup" not in rec:
        rec["setup"] = []
        fault = run_setup(a.setup, root, env, rec)
        write_json(hdir / "run.json", rec)
        if fault:
            rec["status"], rec["reason"] = "harness_fault", fault
            finish_record(root, rec)
            write_json(hdir / "run.json", rec)
            print(f"{a.run_id}: harness_fault ({fault})")
            return EXIT["harness_fault"]
    rec["status"], rec["reason"] = "running", None
    return loop(a, root, rec, env)


def run_setup(commands: list[str], root: Path, env: dict, rec: dict) -> str | None:
    """Run a codebase's setup commands (e.g. installing dependencies) in the checkout before the session.

    They run once, with the run's environment but outside the OS sandbox and with network, so the session
    itself needs no package registry. `{run}` in a command is the run's folder. Output goes to
    harness/setup.log. Returns why setup failed, or None.
    """
    log = root / "harness" / "setup.log"
    for raw in commands:
        cmd = raw.replace("{run}", str(root))
        t0 = time.monotonic()
        with open(log, "a", encoding="utf-8") as out:
            out.write(f"$ {cmd}\n")
            out.flush()
            try:
                done = subprocess.run(
                    ["/bin/sh", "-c", cmd],
                    cwd=root / "repo",
                    env=env,
                    stdout=out,
                    stderr=subprocess.STDOUT,
                    timeout=1800,
                )
                code = done.returncode
            except subprocess.TimeoutExpired:
                code = "timeout"
        rec["setup"].append({"cmd": cmd, "exit": code, "seconds": round(time.monotonic() - t0, 1)})
        if code != 0:
            return f"setup command failed ({code}): {cmd}"
    return None


def loop(a, root: Path, rec: dict, env: dict) -> int:
    hdir = root / "harness"
    while True:
        prompt = rec.get("pending_prompt") or CONTINUE
        if rec.get("session_started") and rec.get("session_id"):
            a._session_id = rec["session_id"]
            cmd = session_cmd(a, root, rec["session_id"])
        else:
            a._session_id = str(uuid.uuid4())
            rec["session_id"] = a._session_id
            cmd = session_cmd(a, root, None)
        before = Usage.from_dict(rec["tokens"])
        n = len(rec["invocations"]) + 1
        append_jsonl(hdir / "transcript.jsonl", {"type": "harness", "event": "invocation", "n": n, "prompt": prompt})
        t0 = time.monotonic()

        def tick(state, before=before):
            live = dict(rec, tokens=(before + state.live_usage()).as_dict())
            write_json(hdir / "run.json", live)

        wall_left = a.max_wall_min * 60 - rec["wall_seconds"]
        state, how = invoke(cmd, prompt, root / "repo", env, root, a.ceiling - before.counted, wall_left, tick)
        if state.init or state.result:
            rec["session_started"] = True
        if state.init and state.init.get("claude_code_version"):
            rec["claude_code_version"] = state.init["claude_code_version"]
        rec["session_id"] = state.session_id or rec["session_id"]
        # Result totals are running totals for the session, so this call's share is the difference
        # from the last result of the same session. A call killed before its result counts what it logged.
        base = rec.get("session_base") or {}
        same = base.get("session_id") == rec["session_id"]
        if state.result:
            now_tokens, now_cost = state.final_usage(), state.cost_usd
            used = now_tokens - Usage.from_dict(base.get("tokens")) if same else now_tokens
            cost = max(now_cost - base.get("cost_usd", 0.0), 0.0) if same else now_cost
            models_now = state.model_totals()
            models_base = base.get("models", {}) if same else {}
            by_call = {
                m: {
                    "tokens": v["tokens"] - Usage.from_dict((models_base.get(m) or {}).get("tokens")),
                    "cost_usd": max(v["cost_usd"] - (models_base.get(m) or {}).get("cost_usd", 0.0), 0.0),
                }
                for m, v in models_now.items()
            }
            rec["session_base"] = {
                "session_id": rec["session_id"],
                "tokens": now_tokens.as_dict(),
                "cost_usd": now_cost,
                "models": {
                    m: {"tokens": v["tokens"].as_dict(), "cost_usd": v["cost_usd"]} for m, v in models_now.items()
                },
            }
        else:
            used, cost = state.live_usage(), 0.0
            by_call = state.model_totals()
        # Counted tokens and list-price cost per model (the lead's and any subagent's), summed over calls.
        by_model = rec.setdefault("by_model", {})
        for m, v in by_call.items():
            prev = by_model.get(m) or {}
            by_model[m] = {
                **(Usage.from_dict(prev) + v["tokens"]).as_dict(),
                "cost_usd": round(prev.get("cost_usd", 0.0) + v["cost_usd"], 6),
            }
        rec["tokens"] = (before + used).as_dict()
        rec["cost_usd"] = round(rec["cost_usd"] + cost, 6)
        rec["wall_seconds"] = round(rec["wall_seconds"] + time.monotonic() - t0, 1)
        rec["turns"] += state.turns
        rec["invocations"].append(
            {
                "n": n,
                "ended": how,
                "subtype": (state.result or {}).get("subtype"),
                "tokens": used.as_dict(),
                "cost_usd": round(cost, 6),
                "time": now_iso(),
            }
        )
        rec["pending_prompt"] = None
        status = None
        if how == "ceiling" or rec["tokens"]["counted"] > a.ceiling:
            status, reason = "ceiling_hit", f"counted tokens {rec['tokens']['counted']} passed {a.ceiling}"
        elif "not logged in" in (state.text + stderr_tail(root)).lower():
            status, reason = "harness_fault", "not logged in: run `claude auth login`, then re-run with --fresh"
        elif state.plan_limited(stderr_tail(root)):
            status, reason = "plan_limit", (state.text or "rate or plan limit")[:300]
            rec["resets_at"] = state.resets_at()
            rec["pending_prompt"] = CONTINUE if rec["session_started"] else prompt
        elif how == "wall":
            status, reason = "harness_fault", f"wall time passed {a.max_wall_min} minutes"
        elif how == "crash" or state.result.get("is_error"):
            detail = (state.result or {}).get("subtype") or stderr_tail(root)[-300:]
            status, reason = "harness_fault", f"session ended without a clean result: {detail}"
        else:
            question = find_stop(state.text)
            if not question:
                status, reason = "finished", "ended without STOP"
            elif rec["stops"] >= a.max_stops:
                status, reason, rec["stop_cap_hit"] = "finished", f"stop cap {a.max_stops} reached", True
            else:
                reply = handle_stop(a, root, rec, question, env)
                rec["pending_prompt"] = reply["text"]
        if status:
            rec["status"], rec["reason"] = status, reason
            finish_record(root, rec)
            write_json(hdir / "run.json", rec)
            t = rec["tokens"]
            print(
                f"{a.run_id}: {status} ({reason}); counted {t['counted']} tokens "
                f"(in {t['input']}, out {t['output']}, cache write {t['cache_write']}, cache read {t['cache_read']}), "
                f"${rec['cost_usd']:.2f}, {rec['stops']} stops, PR {rec['pr_number']}"
            )
            return EXIT[status]
        write_json(hdir / "run.json", rec)


if __name__ == "__main__":
    sys.exit(main())
