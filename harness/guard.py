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


def bash_reason(cmd: str, cwd: str, cfg: dict, depth: int = 0) -> str | None:
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
                r = bash_reason(tok, cwd, cfg, depth + 1)
                if r:
                    return r
            for p in {_looks_like_path(tok), *EMBEDDED_PATH.findall(tok)} - {None}:
                r = path_reason(p, cwd, cfg)
                if r:
                    return r
    return None


def check(tool: str, inp: dict, cwd: str, cfg: dict) -> str | None:
    """Return why a tool call must be refused, or None to let it through."""
    inp = inp or {}
    if tool in BLOCKED_TOOLS or tool.startswith("mcp__"):
        return f"the {tool} tool is not available in this lab"
    cwd = cwd or cfg["sandbox"]
    if tool == "Bash":
        cmd = str(inp.get("command") or "")
        if not _under(_real(cwd), cfg["sandbox"]):
            first = (_segments(cmd) or [[]])[0]
            if not (
                len(first) == 2 and first[0] == "cd" and _under(resolve(first[1], cwd, cfg["home"]), cfg["sandbox"])
            ):
                return f"your shell is outside the sandbox; run `cd {cfg['sandbox']}` first"
        return bash_reason(cmd, cwd, cfg)
    for key in PATH_KEYS:
        if inp.get(key):
            r = path_reason(str(inp[key]), cwd, cfg, write=tool in WRITE_TOOLS)
            if r:
                return r
    pat = str(inp.get("pattern") or "")
    if tool == "Glob" and (pat.startswith(("/", "~")) or ".." in pat):
        p = _looks_like_path(pat)
        if p:
            return path_reason(p, cwd, cfg)
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
