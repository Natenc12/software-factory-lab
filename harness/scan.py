"""Leak scan: did a run read or list a forbidden place, or use a blocked command?

    python -m harness.scan <run folder>

Reads <run folder>/harness/transcript.jsonl (every tool call, subagents' included) and judges each call
with the same rules as the run's guard, plus a check for other runs' branches. Writes
<run folder>/harness/scan.json. `clean` is false when any offending call got through; calls the guard
or the permission rules refused are listed as blocked attempts.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from harness import guard
from harness.common import read_json, write_json

BRANCH_RE = re.compile(r"\b[a-z0-9]+-[a-z0-9]+-[0-9]+/work\b")
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
    calls, offences = 0, []
    for no, line in enumerate(lines, 1):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("type") != "assistant":
            continue
        for block in (rec.get("message") or {}).get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            calls += 1
            name, inp = block.get("name", ""), block.get("input") or {}
            reason = guard.check(name, inp, str(folder / "repo"), cfg)
            text = json.dumps(inp)
            if not reason:
                others = sorted(set(BRANCH_RE.findall(text)) - {own_branch})
                if others:
                    reason = f"names another run's branch: {', '.join(others)}"
            if not reason and name != "Bash":
                for word in cfg.get("forbidden_words", []):
                    if word.lower() in text.lower() and name not in ("Write", "Edit", "MultiEdit"):
                        reason = f"mentions {word!r}"
            if reason:
                is_error, result = results.get(block.get("id"), (False, ""))
                blocked = is_error and any(k.lower() in result.lower() for k in REFUSED)
                offences.append({"line": no, "tool": name, "input": inp, "reason": reason, "blocked": blocked})
    got_through = [o for o in offences if not o["blocked"]]
    return {
        "run_folder": str(folder),
        "clean": not got_through,
        "tool_calls": calls,
        "offences": got_through,
        "blocked_attempts": [o for o in offences if o["blocked"]],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m harness.scan", description=__doc__.split("\n\n")[0])
    ap.add_argument("run_folder")
    args = ap.parse_args(argv)
    report = scan(Path(args.run_folder))
    write_json(Path(args.run_folder) / "harness" / "scan.json", report)
    print(
        f"{'clean' if report['clean'] else 'NOT CLEAN'}: {report['tool_calls']} tool calls, "
        f"{len(report['offences'])} offending, {len(report['blocked_attempts'])} blocked attempts"
    )
    for o in report["offences"]:
        print(f"  line {o['line']}: {o['tool']} {json.dumps(o['input'])[:200]} -> {o['reason']}")
    return 0 if report["clean"] else 2


if __name__ == "__main__":
    sys.exit(main())
