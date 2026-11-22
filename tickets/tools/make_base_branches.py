"""Create (or re-create) the starting branches for a codebase's tickets in a local clone of its practice repo.

    python3 tickets/tools/make_base_branches.py gct [T1 T2 ...] [--lab ~/repos/gct-lab] [--push]

For each ticket:

- `base/<T>` points at the commit in `BASES`, plus one commit that deletes agent-instruction files
  (`CLAUDE.md`, `AGENTS.md`, `.claude/`) when that commit has any, so no run starts with project
  guidance that competes with its arm. For T8 the branch also gets one commit made from
  `answers/<codebase>/T8/feature.patch` (the feature under review, planted bugs included).
- `base/<T>-s3` (tickets that have one) is `base/<T>` plus one commit that adds the files under
  `answers/<codebase>/<T>/acceptance/`, at the same paths.

Commits are made in a temporary worktree with a fixed author and date, so re-running gives the same
SHAs. `--push` pushes exactly these branches to `origin` with `--force-with-lease`; nothing else.
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
    }
}

IDENTITY = {
    "GIT_AUTHOR_NAME": "gct-lab",
    "GIT_AUTHOR_EMAIL": "gct-lab@users.noreply.github.com",
    "GIT_COMMITTER_NAME": "gct-lab",
    "GIT_COMMITTER_EMAIL": "gct-lab@users.noreply.github.com",
    "GIT_AUTHOR_DATE": "2026-11-21T12:00:00+00:00",
    "GIT_COMMITTER_DATE": "2026-11-21T12:00:00+00:00",
}

AGENT_FILES = ["CLAUDE.md", "AGENTS.md", ".claude"]

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
) -> str:
    env = {**os.environ, **IDENTITY}
    tmp = Path(tempfile.mkdtemp(prefix="base-branch-"))
    wt = tmp / "wt"
    try:
        git("worktree", "add", "--detach", str(wt), start, cwd=lab)
        if remove:
            git("rm", "-r", "-q", "--ignore-unmatch", "--", *remove, cwd=wt)
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
    ap.add_argument("--lab", default=str(Path.home() / "repos" / "gct-lab"))
    ap.add_argument("--push", action="store_true")
    args = ap.parse_args(argv)
    lab = Path(args.lab).expanduser()
    bases = BASES[args.codebase]
    made: list[str] = []
    for tid in args.tickets or sorted(bases):
        meta = json.loads((ROOT / "tickets" / args.codebase / tid / "meta.json").read_text())
        adir = ROOT / "answers" / args.codebase / tid
        start = git("rev-parse", "--verify", bases[tid] + "^{commit}", cwd=lab)
        if git("ls-tree", "--name-only", start, "--", *AGENT_FILES, cwd=lab):
            start = commit_on(lab, start, MESSAGES["agents"], remove=AGENT_FILES)
        if tid == "T8":
            start = commit_on(lab, start, MESSAGES["T8"], patch=adir / "feature.patch")
        git("branch", "-f", meta["base_ref"], start, cwd=lab)
        made.append(meta["base_ref"])
        print(f"{meta['base_ref']} -> {start}")
        s3 = meta.get("s3_base_ref")
        if s3:
            sha = commit_on(lab, start, MESSAGES["s3"], add_tree=adir / "acceptance")
            git("branch", "-f", s3, sha, cwd=lab)
            made.append(s3)
            print(f"{s3} -> {sha}")
    if args.push:
        for ref in made:
            git("push", "-q", "--force-with-lease", "origin", f"refs/heads/{ref}:refs/heads/{ref}", cwd=lab)
            print(f"pushed {ref}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
