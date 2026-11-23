"""Leak scan: did a run read or list a forbidden place, or use a blocked command?

    python -m harness.scan <run folder>

Reads <run folder>/harness/transcript.jsonl (every tool call, subagents' included) and judges each call
with the same rules as the run's guard, plus a check for other runs' branches. Relative paths are
resolved against the working directory in effect, following `cd` within a command and across commands. Writes
<run folder>/harness/scan.json. `clean` is false when any offending call got through; calls the guard
or the permission rules refused are listed as blocked attempts.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from harness import guard
from harness.common import read_json, write_json

BRANCH_RE = re.compile(r"\b[a-z0-9]+-[a-z0-9]+-[0-9]+/work\b")
# GitHub token formats: classic (ghp_, gho_, ghu_, ghs_, ghr_) and fine-grained (github_pat_).
TOKEN_RE = re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}\b")
# `gh auth ...` or git's credential helpers called from inside a program or a quoted string.
GH_AUTH_RE = re.compile(r"""\bgh\b["'\s,\]\[]{1,8}auth\b|auth\s+git-credential|\bgit\b["'\s,]{1,6}credential\b""")
REFUSED = ("Blocked by the lab guard", "hook error", "denied", "not allowed", "Permission to use")


def tool_results(lines: list[str]) -> dict[str, tuple[bool, str]]:
    out = {}
    for line in lines:
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("type") != "user":
            continue
        content = (rec.get("message") or {}).get("content")
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                text = block.get("content")
                text = json.dumps(text) if not isinstance(text, str) else text
                out[block.get("tool_use_id")] = (bool(block.get("is_error")), text)
    return out


SHELL_RESET_RE = re.compile(r"Shell cwd was reset to (\S+)")


def scan(folder: Path) -> dict:
    folder = Path(folder).resolve()
    hdir = folder / "harness"
    cfg = read_json(hdir / "guard.json")
    if not cfg:
        raise SystemExit(f"{hdir / 'guard.json'} missing: not a harness run folder")
    run = read_json(hdir / "run.json", {})
    own_branch = run.get("branch") or f"{folder.name}/work"
    lines = (hdir / "transcript.jsonl").read_text(encoding="utf-8", errors="replace").splitlines()
    results = tool_results(lines)
    # The working directory per shell: the lead's, and each subagent's (keyed by the call that started it).
    # Every shell starts in the checkout; a `cd` carries to the next command once its result is in.
    start = str(Path(cfg["sandbox"]) / "repo")
    cwd: dict[str | None, str | None] = {}
    pending: dict[str, tuple[str | None, str, str | None]] = {}
    calls, offences, unresolved = 0, [], []
    for no, line in enumerate(lines, 1):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        shell = rec.get("parent_tool_use_id") if isinstance(rec, dict) else None
        if rec.get("type") == "user":
            content = (rec.get("message") or {}).get("content")
            for block in content if isinstance(content, list) else []:
                if not isinstance(block, dict) or block.get("type") != "tool_result":
                    continue
                if block.get("tool_use_id") in pending:
                    owner, cmd, before = pending.pop(block["tool_use_id"])
                    after = guard.final_cwd(cmd, before, cfg)
                    if block.get("is_error") and after != before and not (after and os.path.isdir(after)):
                        # The command failed somewhere and its `cd` target is not a folder on disk, so
                        # the `cd` may not have run. (A failing test after a good `cd` keeps the folder.)
                        after = None
                    cwd[owner] = after
                text = block.get("content")
                reset = SHELL_RESET_RE.search(text if isinstance(text, str) else json.dumps(text))
                if reset:
                    cwd[shell] = reset.group(1)
            continue
        if rec.get("type") != "assistant":
            continue
        for block in (rec.get("message") or {}).get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            calls += 1
            name, inp = block.get("name", ""), block.get("input") or {}
            here = cwd.get(shell, start)
            unknown: list[str] = []
            reason = guard.check(name, inp, here, cfg, unresolved=unknown, scan=True)
            if name == "Bash":
                pending[block.get("id")] = (shell, str(inp.get("command") or ""), here)
            text = json.dumps(inp)
            if not reason:
                others = sorted(set(BRANCH_RE.findall(text)) - {own_branch})
                if others:
                    reason = f"names another run's branch: {', '.join(others)}"
            if not reason and GH_AUTH_RE.search(text):
                reason = "asks gh or git for GitHub credentials"
            if not reason and name != "Bash":
                for word in cfg.get("forbidden_words", []):
                    if word.lower() in text.lower() and name not in ("Write", "Edit", "MultiEdit"):
                        reason = f"mentions {word!r}"
            if reason:
                is_error, result = results.get(block.get("id"), (False, ""))
                blocked = is_error and any(k.lower() in result.lower() for k in REFUSED)
                offences.append({"line": no, "tool": name, "input": inp, "reason": reason, "blocked": blocked})
            elif unknown:
                unresolved.append({"line": no, "tool": name, "input": inp, "paths": sorted(set(unknown))})
    calls_by_id = {}
    for line in lines:
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        for block in (rec.get("message") or {}).get("content") or [] if rec.get("type") == "assistant" else []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                calls_by_id[block.get("id")] = block
    for tid, (_err, text) in results.items():
        if TOKEN_RE.search(text):
            call = calls_by_id.get(tid) or {}
            offences.append(
                {
                    "line": None,
                    "tool": call.get("name", "?"),
                    "input": call.get("input") or {},
                    "reason": "tool output contains a GitHub token",
                    "blocked": False,
                }
            )
    # Sealed runs: touching another session's folder in Claude Code's shared temp folder makes the run not
    # clean even when it was refused, so a read through the one gap the sandbox leaves is caught where seen.
    st = cfg.get("shared_temp")
    if st:
        spellings = {st, st.replace("/private/tmp/", "/tmp/", 1)}
        own = Path(cfg.get("own_temp", "")).name
        pat = re.compile("(?:" + "|".join(re.escape(s) for s in spellings) + r")/([^/\s'\"]+)/")

        def touches(text: str) -> bool:
            return any(m.group(1) != own for m in pat.finditer(text))

        for o in offences:
            if guard.SHARED_TEMP_REASON in o["reason"] or touches(json.dumps(o["input"])):
                o["blocked"] = False
        seen = {json.dumps(o["input"], sort_keys=True) for o in offences}
        for no, line in enumerate(lines, 1):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            for block in (rec.get("message") or {}).get("content") or [] if rec.get("type") == "assistant" else []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    inp = block.get("input") or {}
                    if touches(json.dumps(inp)) and json.dumps(inp, sort_keys=True) not in seen:
                        seen.add(json.dumps(inp, sort_keys=True))
                        offences.append(
                            {
                                "line": no,
                                "tool": block.get("name"),
                                "input": inp,
                                "reason": guard.SHARED_TEMP_REASON,
                                "blocked": False,
                            }
                        )
        glog = hdir / "guard.log"
        for no, line in enumerate(glog.read_text(errors="replace").splitlines() if glog.exists() else [], 1):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            inp = rec.get("input") or {}
            if touches(json.dumps(inp)) and json.dumps(inp, sort_keys=True) not in seen:
                seen.add(json.dumps(inp, sort_keys=True))
                offences.append(
                    {
                        "line": f"guard.log:{no}",
                        "tool": rec.get("tool"),
                        "input": inp,
                        "reason": guard.SHARED_TEMP_REASON,
                        "blocked": False,
                    }
                )
    got_through = [o for o in offences if not o["blocked"]]
    return {
        "run_folder": str(folder),
        "clean": not got_through,
        "tool_calls": calls,
        "offences": got_through,
        "blocked_attempts": [o for o in offences if o["blocked"]],
        # Relative paths used where the transcript does not show the working directory. Listed for a
        # reader; they do not make the scan unclean.
        "could_not_resolve": unresolved,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m harness.scan", description=__doc__.split("\n\n")[0])
    ap.add_argument("run_folder")
    args = ap.parse_args(argv)
    report = scan(Path(args.run_folder))
    write_json(Path(args.run_folder) / "harness" / "scan.json", report)
    print(
        f"{'clean' if report['clean'] else 'NOT CLEAN'}: {report['tool_calls']} tool calls, "
        f"{len(report['offences'])} offending, {len(report['blocked_attempts'])} blocked attempts, "
        f"{len(report['could_not_resolve'])} with paths it could not resolve"
    )
    for o in report["offences"]:
        print(f"  line {o['line']}: {o['tool']} {json.dumps(o['input'])[:200]} -> {o['reason']}")
    return 0 if report["clean"] else 2


if __name__ == "__main__":
    sys.exit(main())
