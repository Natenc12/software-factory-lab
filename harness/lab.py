#!/usr/bin/env python3
"""The `lab` command a run gets instead of GitHub access. Standard library only; copied into each run.

    lab ticket                                   print the ticket
    lab pr open --title T --body-file F [--draft] push this run's branch, open its one pull request
    lab pr update [--title T] [--body-file F]    push this run's branch, edit its pull request
    lab pr checks                                CI status of this run's pull request

It reads its settings from `lab.json` beside the script (or $LAB_CONFIG). It never merges, labels or
comments: the only `gh` calls it can make are `pr list`, `pr create`, `pr edit` and `pr checks`.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

GH_ALLOWED = {("pr", "list"), ("pr", "create"), ("pr", "edit"), ("pr", "checks")}


def load_config() -> dict:
    path = os.environ.get("LAB_CONFIG") or str(Path(os.path.realpath(__file__)).parent.parent / "lab.json")
    return json.loads(Path(path).read_text(encoding="utf-8"))


def log(cfg: dict, event: dict) -> None:
    event = {"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **event}
    with open(cfg["events"], "a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")


def gh(cfg: dict, *args: str) -> subprocess.CompletedProcess:
    if tuple(args[:2]) not in GH_ALLOWED:
        raise SystemExit(f"lab: refusing gh {' '.join(args[:2])}")
    return subprocess.run([cfg["gh"], *args, "--repo", cfg["repo"]], capture_output=True, text=True)


def inside(cfg: dict, path: str) -> Path:
    p = Path(os.path.realpath(path))
    root = cfg["sandbox"].rstrip("/") + "/"
    if not str(p).startswith(root) or str(p).startswith(cfg["private"].rstrip("/") + "/"):
        raise SystemExit(f"lab: {path} must be a file inside your run folder")
    if not p.is_file():
        raise SystemExit(f"lab: no such file: {path}")
    return p


def push(cfg: dict) -> None:
    branch = cfg["branch"]
    out = subprocess.run(
        [
            "git",
            "-C",
            cfg["repo_dir"],
            "-c",
            "credential.helper=",
            "-c",
            f"credential.helper=!{cfg['gh']} auth git-credential",
            "push",
            "--force",
            "--quiet",
            cfg["push_url"],
            f"refs/heads/{branch}:refs/heads/{branch}",
        ],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        raise SystemExit(f"lab: push failed: {out.stderr.strip()}")
    head = subprocess.run(["git", "-C", cfg["repo_dir"], "rev-parse", branch], capture_output=True, text=True)
    log(cfg, {"event": "push", "branch": branch, "commit": head.stdout.strip()})
    print(f"pushed {branch}")


def find_pr(cfg: dict) -> int | None:
    out = gh(cfg, "pr", "list", "--head", cfg["branch"], "--state", "all", "--json", "number")
    if out.returncode != 0:
        raise SystemExit(f"lab: could not look up the pull request: {out.stderr.strip()}")
    items = json.loads(out.stdout or "[]")
    return int(items[0]["number"]) if items else None


def cmd_ticket(cfg: dict, _args) -> int:
    print(Path(cfg["ticket"]).read_text(encoding="utf-8"), end="")
    return 0


def cmd_open(cfg: dict, args) -> int:
    body = inside(cfg, args.body_file)
    if find_pr(cfg) is not None:
        raise SystemExit("lab: this run already has a pull request; use `lab pr update`")
    push(cfg)
    extra = ["--draft"] if args.draft else []
    out = gh(
        cfg,
        "pr",
        "create",
        "--head",
        cfg["branch"],
        "--base",
        cfg["pr_base"],
        "--title",
        args.title,
        "--body-file",
        str(body),
        *extra,
    )
    if out.returncode != 0:
        raise SystemExit(f"lab: could not open the pull request: {out.stderr.strip()}")
    m = re.search(r"/pull/(\d+)", out.stdout)
    number = int(m.group(1)) if m else find_pr(cfg)
    log(cfg, {"event": "pr_open", "pr": number, "title": args.title})
    print(out.stdout.strip())
    return 0


def cmd_update(cfg: dict, args) -> int:
    number = find_pr(cfg)
    if number is None:
        raise SystemExit("lab: no pull request yet; use `lab pr open --title ... --body-file ...`")
    push(cfg)
    edits = []
    if args.title:
        edits += ["--title", args.title]
    if args.body_file:
        edits += ["--body-file", str(inside(cfg, args.body_file))]
    if edits:
        out = gh(cfg, "pr", "edit", str(number), *edits)
        if out.returncode != 0:
            raise SystemExit(f"lab: could not edit the pull request: {out.stderr.strip()}")
    log(cfg, {"event": "pr_update", "pr": number, "edited": bool(edits)})
    print(f"pull request #{number} updated")
    return 0


def cmd_checks(cfg: dict, _args) -> int:
    number = find_pr(cfg)
    if number is None:
        raise SystemExit("lab: no pull request yet")
    out = gh(cfg, "pr", "checks", str(number))
    print((out.stdout + out.stderr).strip())
    return out.returncode


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="lab", description="This run's only way to reach GitHub.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ticket", help="print the ticket").set_defaults(fn=cmd_ticket)
    pr = sub.add_parser("pr", help="this run's pull request").add_subparsers(dest="pr_cmd", required=True)
    o = pr.add_parser("open", help="push the branch and open the pull request")
    o.add_argument("--title", required=True)
    o.add_argument("--body-file", required=True)
    o.add_argument("--draft", action="store_true")
    o.set_defaults(fn=cmd_open)
    u = pr.add_parser("update", help="push the branch; optionally change the title or body")
    u.add_argument("--title")
    u.add_argument("--body-file")
    u.set_defaults(fn=cmd_update)
    pr.add_parser("checks", help="CI status of the pull request").set_defaults(fn=cmd_checks)
    args = ap.parse_args(argv)
    return args.fn(load_config(), args)


if __name__ == "__main__":
    sys.exit(main())
