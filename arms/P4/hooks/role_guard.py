#!/usr/bin/env python3
"""PreToolUse hook that holds each team role to its job. Standard library only.

    role_guard.py <role> <work folder>

The work folder holds `repo/` (the checkout) and `scratch/`. Claude Code passes the tool call as JSON
on stdin; a refused call gets a deny decision on stdout. Roles:

    planner    writes only scratch/team/contract.md
    architect  writes only scratch/team/design.md
    builder    may not change the tester's file, the contract, the design note or the review folder
    tester     writes only tests/test_ticket_acceptance.py; in the checkout reads only its own file,
               conftest.py files in tests/, pyproject.toml, top-level .md files, design/ and docs/;
               in scratch/ reads only the contract and the design note
    reviewer   changes nothing outside scratch/team/review/; may not read scratch/ beyond the contract,
               the test results and its own folder
"""

import json
import os
import re
import shlex
import sys

TESTER_FILE = "tests/test_ticket_acceptance.py"
GIT_WRITES = {
    "add", "am", "apply", "branch", "checkout", "cherry-pick", "clean", "commit", "config", "merge", "mv",
    "push", "rebase", "reset", "restore", "revert", "rm", "stash", "switch", "tag", "update-ref", "worktree",
}  # fmt: skip
WRITE_CMDS = {"rm", "mv", "cp", "touch", "mkdir", "rmdir", "tee", "truncate", "ln", "chmod", "dd", "install", "patch"}
IN_PLACE = {"sed", "perl", "ruby"}


def real(p: str, cwd: str) -> str:
    p = os.path.expanduser(p)
    return os.path.realpath(p if os.path.isabs(p) else os.path.join(cwd, p))


def under(p: str, root: str) -> bool:
    return p == root or p.startswith(root.rstrip("/") + "/")


class Run:
    def __init__(self, folder: str):
        self.root = os.path.realpath(folder)
        self.repo = os.path.join(self.root, "repo")
        self.scratch = os.path.join(self.root, "scratch")
        self.team = os.path.join(self.scratch, "team")
        self.contract = os.path.join(self.team, "contract.md")
        self.design = os.path.join(self.team, "design.md")
        self.results = os.path.join(self.team, "test-results.md")
        self.review = os.path.join(self.team, "review")
        self.tester_file = os.path.join(self.repo, TESTER_FILE)


def tester_read(run: Run, p: str) -> str | None:
    """Inside the checkout the tester reads only an allow-list; in scratch/, only the contract and design note."""
    if under(p, run.repo):
        rel = os.path.relpath(p, run.repo)
        allowed = (
            p == run.tester_file
            or (rel.startswith("tests/") and os.path.basename(p) == "conftest.py")
            or rel == "pyproject.toml"
            or ("/" not in rel and rel.endswith(".md"))
            or rel.startswith(("design/", "docs/"))
        )
        if allowed:
            return None
        return (
            f"in the checkout the tester may read only its own file ({TESTER_FILE}), conftest.py files in "
            "tests/, pyproject.toml, top-level .md files, design/ and docs/"
        )
    if under(p, run.scratch) and p not in (run.contract, run.design):
        return "the tester may read only the contract and the design note in scratch/"
    return None


def reviewer_read(run: Run, p: str) -> str | None:
    ok = (run.contract, run.results)
    if under(p, run.scratch) and p not in ok and not under(p, run.review) and not under(p, run.scratch + "/tmp"):
        return "the reviewer may read only the contract, the test results and its own folder in scratch/"
    return None


def scope_reason(run: Run, scope: str, read_rule, blocked_dirs: list[str]) -> str | None:
    """A search over a folder is refused if the folder holds, or sits inside, a place the role may not read."""
    if os.path.isfile(scope):
        return read_rule(run, scope)
    for d in blocked_dirs:
        if under(d, scope):
            return f"search a narrower folder: {scope} includes {os.path.relpath(d, run.root)}/"
    return read_rule(run, os.path.join(scope, "x"))


def words(cmd: str) -> list[str]:
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=";&|()<>")
    lex.whitespace_split = True
    lex.commenters = ""
    try:
        return list(lex)
    except ValueError:
        return cmd.split()


def bash_effects(cmd: str, cwd: str) -> tuple[list[str], list[str], set[str]]:
    """Best effort: (paths written, path-like words, git subcommands that change the repo)."""
    toks = words(cmd.replace("\n", " ; "))
    written, paths, git = [], [], set()
    seg: list[str] = []

    def close(seg):
        if not seg:
            return
        name = os.path.basename(seg[0])
        args = [a for a in seg[1:] if not a.startswith("-")]
        if name == "git":
            rest = seg[1:]
            while rest and rest[0].startswith("-"):
                rest = rest[2:] if rest[0] in ("-C", "-c") else rest[1:]
            if rest and rest[0] in GIT_WRITES:
                git.add(rest[0])
        if name in WRITE_CMDS:
            written.extend(real(a, cwd) for a in args)
        if name in IN_PLACE and any(a.startswith("-i") or a.startswith("-pi") for a in seg[1:]):
            written.extend(real(a, cwd) for a in args[1:])

    i = 0
    while i < len(toks):
        t = toks[i]
        nxt = toks[i + 1] if i + 1 < len(toks) else ""
        if t and set(t) <= set(";&|()<>"):
            if ">" in t or "<" in t:
                if seg and seg[-1].isdigit():
                    seg.pop()  # the file descriptor in 2>file
                if ">" in t and not (t.endswith("&") or nxt.isdigit() or nxt == "-"):
                    written.append(real(nxt, cwd))
                elif "<" in t:
                    paths.append(nxt)
                i += 2
                continue
            close(seg)
            seg = []
        else:
            seg.append(t)
            if "/" in t or t.startswith((".", "~")):
                paths.append(t)
        i += 1
    close(seg)
    return written, [real(p, cwd) for p in paths if not re.match(r"^\w+://", p)], git


def check(role: str, tool: str, inp: dict, cwd: str, run: Run) -> str | None:
    """Why this role may not make this tool call, or None."""
    inp = inp or {}
    cwd = cwd or run.repo
    path = inp.get("file_path") or inp.get("notebook_path")
    target = real(str(path), cwd) if path else None
    writes = tool in ("Write", "Edit", "MultiEdit", "NotebookEdit")

    if role in ("planner", "architect"):
        own = run.contract if role == "planner" else run.design
        if writes and target != own:
            return f"the {role} writes only {os.path.relpath(own, run.root)}"
        if tool == "Bash":
            return f"the {role} does not run commands"
        return None

    if role == "builder":
        protected = (run.tester_file, run.contract, run.design)
        if writes and target and (target in protected or under(target, run.review)):
            return "the builder may not change the tester's tests, the contract, the design note or the review"
        if tool == "Bash":
            written, _, _ = bash_effects(str(inp.get("command") or ""), cwd)
            if any(w in protected or under(w, run.review) for w in written):
                return "the builder may not change the tester's tests, the contract, the design note or the review"
        return None

    if role == "tester":
        if writes:
            return None if target == run.tester_file else f"the tester writes only {TESTER_FILE}"
        if tool == "Read" and target:
            return tester_read(run, target)
        if tool == "Grep":
            scope = real(str(inp.get("path") or cwd), cwd)
            return scope_reason(run, scope, tester_read, [run.repo, run.scratch])
        if tool == "Glob":
            return None  # file names only, no contents
        return f"the tester has no {tool} tool"

    if role == "reviewer":
        if writes:
            return None if target and under(target, run.review) else "the reviewer changes nothing"
        if tool == "Read" and target:
            return reviewer_read(run, target)
        if tool == "Grep":
            scope = real(str(inp.get("path") or cwd), cwd)
            return scope_reason(run, scope, reviewer_read, [run.scratch])
        if tool == "Bash":
            written, paths, git = bash_effects(str(inp.get("command") or ""), cwd)
            if git:
                return f"the reviewer changes nothing: git {sorted(git)[0]} is not allowed"
            inside = (run.review, run.scratch + "/tmp")
            outside = ("/dev/null", "/tmp", "/private/tmp")
            # Inside the work folder only its own places count, even when the folder itself sits under /tmp.
            bad = [w for w in written if not any(under(w, d) for d in (inside if under(w, run.root) else outside))]
            if bad:
                return f"the reviewer changes nothing outside {os.path.relpath(run.review, run.root)}/"
            for p in paths:
                r = reviewer_read(run, p)
                if r:
                    return r
        return None

    return f"unknown role {role}"


def main() -> int:
    role, folder = sys.argv[1], sys.argv[2]
    data = json.loads(sys.stdin.read() or "{}")
    reason = check(role, data.get("tool_name", ""), data.get("tool_input") or {}, data.get("cwd") or "", Run(folder))
    if reason:
        out = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Not allowed for this role: {reason}",
            }
        }
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
