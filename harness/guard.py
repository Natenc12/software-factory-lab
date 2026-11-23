#!/usr/bin/env python3
"""PreToolUse guard for one run. Standard library only, so it can be copied into the run's folder.

As a hook: `guard.py <guard.json>` reads Claude Code's hook input on stdin and prints a deny decision
when the tool call leaves the sandbox, uses the web, or runs a blocked command. The leak scan imports
`check()` to judge the same tool calls after the fact.
"""

import json
import os
import re
import shlex
import sys

BLOCKED_TOOLS = {
    "WebFetch",
    "WebSearch",
    "SendMessage",
    "ListAgents",
    "RemoteTrigger",
    "PushNotification",
    "CronCreate",
    "ScheduleWakeup",
    "EnterWorktree",
    "DesignSync",
}
BLOCKED_CMDS = {"gh", "hub", "curl", "wget", "ssh", "scp", "sftp", "nc", "ncat", "telnet", "open", "osascript"}
BLOCKED_GIT = {"fetch", "pull", "clone", "ls-remote", "remote", "push", "submodule"}
WRAPPERS = {"env", "command", "exec", "time", "nohup", "sudo", "nice", "xargs", "builtin"}
SHELLS = {"bash", "sh", "zsh", "dash", "eval"}
FORBIDDEN_NAME = re.compile(r"^(answers|hidden([._-].*)?)$", re.I)
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
PATH_KEYS = ("file_path", "path", "notebook_path")
EMBEDDED_PATH = re.compile(r"(?<![\w.~-])(~?/[^\s'\"(),;:=<>|&`*?]+)")


def _real(p: str) -> str:
    return os.path.realpath(p)


def _under(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("/") + "/")


def resolve(token: str, cwd: str, home: str) -> str:
    t = token
    if t.startswith("~"):
        t = home + t[1:]
    t = t.replace("${HOME}", home).replace("$HOME", home)
    if not os.path.isabs(t):
        t = os.path.join(cwd, t)
    return _real(os.path.normpath(t))


def path_reason(token: str, cwd: str, cfg: dict, write: bool = False) -> str | None:
    """Why this path is off limits for the run, or None if it is fine."""
    home = cfg["home"]
    p = resolve(token, cwd, home)
    for priv in cfg.get("private", []):
        if _under(p, priv):
            return f"{token}: the harness records folder is off limits"
    if _under(p, cfg["sandbox"]):
        return None
    for bad in cfg.get("forbidden", []):
        if _under(p, bad):
            return f"{token}: forbidden place ({bad})"
    if any(FORBIDDEN_NAME.match(part) for part in p.split("/") if part):
        return f"{token}: forbidden name (answers/hidden)"
    if write and not any(_under(p, ok) for ok in cfg.get("write_ok", [])):
        return f"{token}: writes must stay inside the sandbox"
    if any(_under(p, r) for r in [home, "/Users", "/Volumes"]):
        if not any(_under(p, ok) for ok in cfg.get("read_ok", [])):
            return f"{token}: outside the sandbox"
    return None


def _looks_like_path(tok: str) -> str | None:
    if "://" in tok or not tok:
        return None
    if tok.startswith("-") and "=" in tok:
        tok = tok.split("=", 1)[1]
    elif tok.startswith("-"):
        return None
    if "=" in tok and not tok.startswith(("/", "~", ".")):
        tok = tok.split("=", 1)[1]  # VAR=/some/path
    cut = re.split(r"[*?\[{]", tok, maxsplit=1)[0]
    if cut in (".", "..", "~") or cut.startswith(("/", "~", "./", "../", "$HOME", "${HOME}")) or "/" in cut:
        return cut or None
    return None


def _segments(cmd: str) -> list[list[str]]:
    flat = cmd
    for op in ("$(", "`", "<(", ">(", "\n"):
        flat = flat.replace(op, " ; ")
    try:
        lex = shlex.shlex(flat, posix=True, punctuation_chars=";&|()<>")
        lex.whitespace_split = True
        tokens = list(lex)
    except ValueError:
        tokens = flat.split()
    segs, cur = [], []
    for t in tokens:
        if t and set(t) <= set(";&|()"):
            if cur:
                segs.append(cur)
            cur = []
        elif t and set(t) <= set("<>&0123456789") and any(c in t for c in "<>"):
            continue  # redirection operator; the target is checked as a path
        else:
            cur.append(t)
    if cur:
        segs.append(cur)
    return segs


def _git_sub(args: list[str]) -> str | None:
    skip = False
    for a in args:
        if skip:
            skip = False
            continue
        if a in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"):
            skip = True
            continue
        if a.startswith("-"):
            continue
        return a
    return None


def _is_relative(p: str) -> bool:
    return not p.startswith(("/", "~", "$HOME", "${HOME}"))


def _cd_target(words: list[str], cwd: str | None, home: str) -> tuple[bool, str | None]:
    """(known, new working directory) after a `cd` or `pushd` segment."""
    target = words[1] if len(words) > 1 else "~"
    if target == "-" or "$" in target.replace("$HOME", "").replace("${HOME}", "") or "`" in target:
        return False, None
    if cwd is None and _is_relative(target):
        return False, None
    return True, resolve(target, cwd or "/", home)


def bash_reason(
    cmd: str, cwd: str | None, cfg: dict, depth: int = 0, unresolved: list | None = None, scan: bool = False
) -> str | None:
    """Why a Bash command must be refused, or None.

    Relative paths are resolved against the working directory in effect: `cd` (or `pushd`) earlier in
    the same command moves it. `cwd=None` means it is not known (the scan only); then a relative path is
    added to `unresolved` instead of being judged. When a `cd` target can't be known (a variable, `cd -`),
    the live guard keeps the last known folder and the scan stops resolving relative paths.
    """
    low = cmd.lower()
    for word in cfg.get("forbidden_words", []):
        if word.lower() in low:
            return f"mentions {word!r}"
    for seg in _segments(cmd):
        words = list(seg)
        while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
            words.pop(0)
        while words and os.path.basename(words[0]) in WRAPPERS:
            words.pop(0)
            while words and (words[0].startswith("-") or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0])):
                words.pop(0)
        if len(words) >= 2 and os.path.basename(words[0]) == "uv" and words[1] in ("run", "tool"):
            words = [w for w in words[2:] if not w.startswith("-")] or words
        if not words:
            continue
        name = os.path.basename(words[0])
        if name in BLOCKED_CMDS:
            return f"`{name}` is blocked in this lab; use the `lab` command for GitHub"
        if name == "git":
            sub = _git_sub(words[1:])
            if sub in BLOCKED_GIT:
                return f"`git {sub}` is blocked in this lab; `lab pr update` pushes your branch"
        if name == "cd" and len(words) == 1:
            words = ["cd", "~"]
        for tok in words[1:] if "/" not in words[0] else words:
            if depth < 3 and (" " in tok or (name in SHELLS and tok not in ("-c", "-lc", "-l"))):
                r = bash_reason(tok, cwd, cfg, depth + 1, unresolved, scan)
                if r:
                    return r
            for p in sorted({_looks_like_path(tok), *EMBEDDED_PATH.findall(tok)} - {None}):
                if cwd is None and _is_relative(p):
                    if unresolved is not None:
                        unresolved.append(p)
                    continue
                r = path_reason(p, cwd or "/", cfg)
                if r:
                    return r
        if name in ("cd", "pushd"):
            known, new = _cd_target(words, cwd, cfg["home"])
            if known:
                cwd = new
            elif scan:
                cwd = None
    return None


def _top_level(cmd: str) -> str:
    """The command with everything inside (...), $(...) and backticks blanked out, quotes respected."""
    out, depth, quote, tick = [], 0, None, False
    for ch in cmd:
        if quote:
            if ch == quote:
                quote = None
            out.append(ch if depth == 0 and not tick else " ")
            continue
        if ch in ("'", '"'):
            quote = ch
        elif ch == "`":
            tick = not tick
            out.append(" ")
            continue
        elif ch == "(":
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
            out.append(" ")
            continue
        out.append(ch if depth == 0 and not tick else " ")
    return "".join(out)


def final_cwd(cmd: str, cwd: str | None, cfg: dict) -> str | None:
    """The shell's working directory after a command, following its top-level `cd`s; None if unknown.

    A `cd` inside parentheses or `$(...)` runs in a subshell and does not carry over.
    """
    top = _top_level(cmd)
    for seg in _segments(top):
        words = list(seg)
        while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
            words.pop(0)
        if words and words[0] in ("cd", "pushd"):
            known, new = _cd_target(words if len(words) > 1 else ["cd", "~"], cwd, cfg["home"])
            cwd = new if known else None
    return cwd


def check(
    tool: str, inp: dict, cwd: str | None, cfg: dict, unresolved: list | None = None, scan: bool = False
) -> str | None:
    """Return why a tool call must be refused, or None to let it through.

    The live hook always knows `cwd`. The scan passes `scan=True`, and `cwd=None` when the transcript
    does not show it; relative paths then go to `unresolved` instead of being judged.
    """
    inp = inp or {}
    if tool in BLOCKED_TOOLS or tool.startswith("mcp__"):
        return f"the {tool} tool is not available in this lab"
    if not scan:
        cwd = cwd or cfg["sandbox"]
    if tool == "Bash":
        cmd = str(inp.get("command") or "")
        if not scan and not _under(_real(cwd), cfg["sandbox"]):
            first = (_segments(cmd) or [[]])[0]
            if not (
                len(first) == 2 and first[0] == "cd" and _under(resolve(first[1], cwd, cfg["home"]), cfg["sandbox"])
            ):
                return f"your shell is outside the sandbox; run `cd {cfg['sandbox']}` first"
        return bash_reason(cmd, cwd, cfg, unresolved=unresolved, scan=scan)
    paths = [(str(inp[key]), tool in WRITE_TOOLS) for key in PATH_KEYS if inp.get(key)]
    pat = str(inp.get("pattern") or "")
    if tool == "Glob" and (pat.startswith(("/", "~")) or ".." in pat):
        p = _looks_like_path(pat)
        if p:
            paths.append((p, False))
    for p, write in paths:
        if cwd is None and _is_relative(p):
            if unresolved is not None:
                unresolved.append(p)
            continue
        r = path_reason(p, cwd or "/", cfg, write=write)
        if r:
            return r
    return None


def main() -> int:
    cfg = json.loads(open(sys.argv[1], encoding="utf-8").read())
    data = json.loads(sys.stdin.read() or "{}")
    tool = data.get("tool_name", "")
    reason = check(tool, data.get("tool_input") or {}, data.get("cwd") or cfg["sandbox"], cfg)
    log = cfg.get("log")
    if log:
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"tool": tool, "input": data.get("tool_input"), "deny": reason}) + "\n")
    if reason:
        out = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Blocked by the lab guard: {reason}",
            }
        }
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
