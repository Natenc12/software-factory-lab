"""Create (or re-create) the starting branches for a codebase's tickets in a local clone of its practice repo.

    python3 tickets/tools/make_base_branches.py gct [T1 T2 ...] [--lab ~/repos/gct-lab] [--push]
    python3 tickets/tools/make_base_branches.py sqlglot [main T1 ...] [--push] [--tag stage-4-candidate]
    python3 tickets/tools/make_base_branches.py hono [main T1 ...] [--push] [--tag stage-4-candidate]

For each ticket:

- `base/<T>` points at the commit in `BASES`, plus one commit that deletes agent-instruction files
  (`CLAUDE.md`, `AGENTS.md`, `.claude/`) when that commit has any, so no run starts with project
  guidance that competes with its arm. For T8 the branch also gets one commit made from
  `answers/<codebase>/T8/feature.patch` (the feature under review, planted bugs included).
- `base/<T>-s3` (tickets that have one) is `base/<T>` plus one commit that adds the files under
  `answers/<codebase>/<T>/acceptance/`, at the same paths.

Commits are made in a temporary worktree with a fixed author and date, so re-running gives the same
SHAs. `--push` pushes exactly these branches to `origin` with `--force-with-lease`; nothing else.

A codebase listed in `PREP` gets its own one-commit setup instead of the plain deletion above (for
sqlglot: agent files and upstream CI removed, the integration-test submodule dropped, the lines asking
agents to tag their commits removed from `AGENTS.md` and `CONTRIBUTING.md`, our own test workflow
added). A codebase whose `BASES` has a `main` entry also gets `main` built the same way when `main` is
named (or no ticket is named). `--tag <prefix>` adds a tag `<prefix>/<branch>` on each branch made and,
with `--push`, pushes those tags too.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# The commit each ticket starts from. Replays: the parent of the real fix. Others: the frozen main.
BASES = {
    "gct": {
        "T1": "694a4c71c8fc108c1759658b11df2fc258481af9",
        "T2": "5c05d2f6fcab615d3a4c4211485bea5618374d28",
        "T3": "2e6213625a1be545631a56e9a6d74d65fff38b05",
        "T4": "283ebf86add01478e5c92a5468b0e88148e5fb28",
        "T5": "283ebf86add01478e5c92a5468b0e88148e5fb28",
        "T6": "283ebf86add01478e5c92a5468b0e88148e5fb28",
        "T7": "283ebf86add01478e5c92a5468b0e88148e5fb28",
        "T8": "283ebf86add01478e5c92a5468b0e88148e5fb28",
        "T9": "283ebf86add01478e5c92a5468b0e88148e5fb28",
        "T10": "283ebf86add01478e5c92a5468b0e88148e5fb28",
        "T11": "283ebf86add01478e5c92a5468b0e88148e5fb28",
        "T12": "283ebf86add01478e5c92a5468b0e88148e5fb28",
    },
    # sqlglot: upstream tobymao/sqlglot. main is upstream 089891f (2026-11-20); replays start at the
    # parent of the real fix.
    "sqlglot": {
        "main": "089891f2521780e2c5b243005017af9db62f25a6",
        "T1": "dc4afaf5c9a6748a004998ed13e3b438e20e431e^",
        "T2": "9951ad252d0ef17bab744b94fcb8f90ba6bbf858^",
        "T3": "34ac378866650d732a1de72c96058078938c95f3^",
        "T4": "8802c5a7c9745703a29a824f4e245d44671ad940^",
        "T5": "68ef75b2b6e6d1223115f16c9ff257fea662ab5c^",
        "T6": "089891f2521780e2c5b243005017af9db62f25a6",
        "T7": "089891f2521780e2c5b243005017af9db62f25a6",
        "T8": "089891f2521780e2c5b243005017af9db62f25a6",
    },
    # hono: upstream honojs/hono. main is upstream 9075031 (v4.13.21, 2026-11-23); replays start at
    # the parent of the real fix.
    "hono": {
        "main": "9075031ea46533ae3b6e5b6c11f8333d67a7d6c2",
        "T1": "08807ce12aa3aa27c8c5adf63e677bbab6bceda9^",  # trie router, honojs/hono#5422
        "T2": "ed1d5f72^",  # auth realm, honojs/hono#5590
        "T3": "fb48e2b2^",  # Bun WebSocket onError, honojs/hono#5598
        "T4": "6e8fbe18^",  # async JSX component results, honojs/hono#5575
        "T5": "a46d6025^",  # client init merge, honojs/hono#5646
        "T6": "9075031ea46533ae3b6e5b6c11f8333d67a7d6c2",
        "T7": "9075031ea46533ae3b6e5b6c11f8333d67a7d6c2",
        "T8": "9075031ea46533ae3b6e5b6c11f8333d67a7d6c2",
    },
}

LAB_NAMES = {"gct": "gct-lab", "sqlglot": "sqlglot-lab", "hono": "hono-lab"}

IDENTITY = {
    "GIT_AUTHOR_NAME": "gct-lab",
    "GIT_AUTHOR_EMAIL": "gct-lab@users.noreply.github.com",
    "GIT_COMMITTER_NAME": "gct-lab",
    "GIT_COMMITTER_EMAIL": "gct-lab@users.noreply.github.com",
    "GIT_AUTHOR_DATE": "2026-11-21T12:00:00+00:00",
    "GIT_COMMITTER_DATE": "2026-11-21T12:00:00+00:00",
}
IDENTITIES = {
    "gct": IDENTITY,
    "sqlglot": {
        "GIT_AUTHOR_NAME": "sqlglot-lab",
        "GIT_AUTHOR_EMAIL": "sqlglot-lab@users.noreply.github.com",
        "GIT_COMMITTER_NAME": "sqlglot-lab",
        "GIT_COMMITTER_EMAIL": "sqlglot-lab@users.noreply.github.com",
        "GIT_AUTHOR_DATE": "2026-11-23T12:00:00+00:00",
        "GIT_COMMITTER_DATE": "2026-11-23T12:00:00+00:00",
    },
    "hono": {
        "GIT_AUTHOR_NAME": "hono-lab",
        "GIT_AUTHOR_EMAIL": "hono-lab@users.noreply.github.com",
        "GIT_COMMITTER_NAME": "hono-lab",
        "GIT_COMMITTER_EMAIL": "hono-lab@users.noreply.github.com",
        "GIT_AUTHOR_DATE": "2026-11-23T12:00:00+00:00",
        "GIT_COMMITTER_DATE": "2026-11-23T12:00:00+00:00",
    },
}

AGENT_FILES = ["CLAUDE.md", "AGENTS.md", ".claude"]

PRACTICE = ROOT / "tickets" / "tools" / "practice"

# Lines that tell agents to tag their commits or pull requests with their model name.
TAG_LINE_MARK = "If you are an agent, you must add your model"


def prep_sqlglot(wt: Path) -> None:
    """The practice-copy setup commit for sqlglot (see the module docstring)."""
    git("rm", "-r", "-q", "--ignore-unmatch", "--", "CLAUDE.md", ".claude", ".cursor", ".cursorrules", cwd=wt)
    git("rm", "-r", "-q", "--ignore-unmatch", "--", ".github/workflows", cwd=wt)
    if (wt / ".gitmodules").exists():
        git("rm", "-q", "--cached", "--ignore-unmatch", "--", "sqlglot-integration-tests", cwd=wt)
        git("rm", "-q", "--", ".gitmodules", cwd=wt)
    for name in ("AGENTS.md", "CONTRIBUTING.md"):
        f = wt / name
        if f.exists():
            lines = f.read_text(encoding="utf-8").splitlines(keepends=True)
            kept = [line for line in lines if TAG_LINE_MARK not in line]
            if kept != lines:
                f.write_text("".join(kept), encoding="utf-8")
                git("add", name, cwd=wt)
    dest = wt / ".github" / "workflows" / "tests.yml"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PRACTICE / "sqlglot" / "tests.yml", dest)
    git("add", ".github/workflows/tests.yml", cwd=wt)


def prep_hono(wt: Path) -> None:
    """The practice-copy setup commit for hono: upstream's whole `.github/` (workflows, templates, bots)
    and any agent-instruction files go, and the practice copy's test-only workflow comes in."""
    git("rm", "-r", "-q", "--ignore-unmatch", "--", ".github", *HONO_AGENT_FILES, cwd=wt)
    dest = wt / ".github" / "workflows" / "test.yml"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PRACTICE / "hono" / "test.yml", dest)
    git("add", ".github/workflows/test.yml", cwd=wt)


HONO_AGENT_FILES = ["CLAUDE.md", "AGENTS.md", ".claude", ".cursor", ".cursorrules", ".windsurfrules", "GEMINI.md"]

PREP = {
    "sqlglot": (prep_sqlglot, "Set up the practice copy: no agent files, our own CI, no submodule"),
    "hono": (prep_hono, "Practice copy: remove upstream workflows and templates, add a test-only workflow"),
}

MESSAGES = {
    "agents": "Remove agent instruction files",
    "s3": "Add acceptance tests for the ticket",
    "T8": "Add a list of the files in a class",
}


def git(*args: str, cwd: Path, env: dict | None = None) -> str:
    out = subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {out.stderr.strip()}")
    return out.stdout.strip()


def commit_on(
    lab: Path,
    start: str,
    message: str,
    add_tree: Path | None = None,
    patch: Path | None = None,
    remove: list[str] | None = None,
    prep=None,
    identity: dict | None = None,
) -> str:
    env = {**os.environ, **(identity or IDENTITY)}
    tmp = Path(tempfile.mkdtemp(prefix="base-branch-"))
    wt = tmp / "wt"
    try:
        git("worktree", "add", "--detach", str(wt), start, cwd=lab)
        if remove:
            git("rm", "-r", "-q", "--ignore-unmatch", "--", *remove, cwd=wt)
        if prep is not None:
            prep(wt)
        if patch is not None:
            git("apply", "--index", str(patch), cwd=wt)
        if add_tree is not None:
            for src in sorted(p for p in add_tree.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
                dest = wt / src.relative_to(add_tree)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                git("add", str(dest.relative_to(wt)), cwd=wt)
        git("commit", "-q", "-m", message, cwd=wt, env=env)
        return git("rev-parse", "HEAD", cwd=wt)
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=lab, capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("codebase")
    ap.add_argument("tickets", nargs="*")
    ap.add_argument("--lab", help="local clone of the practice repo (default ~/repos/<codebase>-lab)")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--tag", help="also tag each branch made as <prefix>/<branch>")
    args = ap.parse_args(argv)
    lab = Path(args.lab or Path.home() / "repos" / LAB_NAMES.get(args.codebase, args.codebase)).expanduser()
    bases = BASES[args.codebase]
    identity = IDENTITIES.get(args.codebase, IDENTITY)
    prep = PREP.get(args.codebase)
    made: list[str] = []
    for tid in args.tickets or sorted(bases, key=lambda k: (k != "main", len(k), k)):
        start = git("rev-parse", "--verify", bases[tid] + "^{commit}", cwd=lab)
        if prep is not None:
            start = commit_on(lab, start, prep[1], prep=prep[0], identity=identity)
        elif git("ls-tree", "--name-only", start, "--", *AGENT_FILES, cwd=lab):
            start = commit_on(lab, start, MESSAGES["agents"], remove=AGENT_FILES, identity=identity)
        if tid == "main":
            git("branch", "-f", "main", start, cwd=lab) if git(
                "rev-parse", "--abbrev-ref", "HEAD", cwd=lab
            ) != "main" else git("reset", "-q", "--hard", start, cwd=lab)
            made.append("main")
            print(f"main -> {start}")
            continue
        meta = json.loads((ROOT / "tickets" / args.codebase / tid / "meta.json").read_text())
        adir = ROOT / "answers" / args.codebase / tid
        if (adir / "feature.patch").is_file() and meta.get("deliverable") == "review_report":
            start = commit_on(lab, start, MESSAGES["T8"], patch=adir / "feature.patch", identity=identity)
        git("branch", "-f", meta["base_ref"], start, cwd=lab)
        made.append(meta["base_ref"])
        print(f"{meta['base_ref']} -> {start}")
        s3 = meta.get("s3_base_ref")
        if s3:
            sha = commit_on(lab, start, MESSAGES["s3"], add_tree=adir / "acceptance", identity=identity)
            git("branch", "-f", s3, sha, cwd=lab)
            made.append(s3)
            print(f"{s3} -> {sha}")
    tags = []
    if args.tag:
        for ref in made:
            tag = f"{args.tag}/{ref}"
            git("tag", "-f", tag, f"refs/heads/{ref}", cwd=lab)
            tags.append(tag)
            print(f"tag {tag}")
    if args.push:
        for ref in made:
            git("push", "-q", "--force-with-lease", "origin", f"refs/heads/{ref}:refs/heads/{ref}", cwd=lab)
            print(f"pushed {ref}")
        for tag in tags:
            git("push", "-q", "--force", "origin", f"refs/tags/{tag}:refs/tags/{tag}", cwd=lab)
            print(f"pushed tag {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
