"""One sandbox per run, at <runs root>/<stage>/<run-id>/, and its teardown.

    python -m harness.sandbox down <run folder> [--all]

Layout:
    repo/          fresh clone holding only the base ref's history, on branch <run-id>/work
    scratch/       the run's scratch space (also its TMPDIR)
    TICKET.md      the ticket
    arm/           the arm's files (absent for a bare arm)
    db/            SQLite database file (pipeline-lab); Postgres runs get database run_<run_id>
    harness/       records and controls; the run's guard keeps the session out of it
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from harness.common import LAB_ROOT, append_jsonl, git, now_iso, parse_run_id, read_json, write_json

HERE = Path(__file__).resolve().parent
# Built-in tools a run is offered. Leaves out web tools and the app's messaging, scheduling and remote
# tools. The subagent tool is called Task in 2.1.302's init record and Agent in the docs; both are named.
ALLOWED_TOOLS = "Task Agent Bash Read Edit Write NotebookEdit Glob Grep"
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def pg_name(run_id: str) -> str:
    parse_run_id(run_id)
    return "run_" + run_id.replace("-", "_")


def psql(sql: str, db: str = "postgres", pg_bin: str = "psql") -> subprocess.CompletedProcess:
    return subprocess.run(
        [pg_bin, "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d", db, "-tAc", sql], capture_output=True, text=True
    )


def create_postgres(run_id: str, pg_bin: str = "psql", host_url: str = "postgresql://localhost") -> dict:
    name = pg_name(run_id)
    exists = psql(f"SELECT 1 FROM pg_database WHERE datname = '{name}'", pg_bin=pg_bin)
    if exists.returncode != 0:
        raise RuntimeError(f"cannot reach Postgres: {exists.stderr.strip()}")
    if exists.stdout.strip() == "1":
        raise RuntimeError(f"database {name} already exists; it belongs to another run or an old sandbox")
    for sql, db in ((f'CREATE DATABASE "{name}"', "postgres"), ("CREATE EXTENSION IF NOT EXISTS vector", name)):
        out = psql(sql, db, pg_bin)
        if out.returncode != 0:
            raise RuntimeError(f"{sql} failed: {out.stderr.strip()}")
    return {"kind": "postgres", "name": name, "url": f"{host_url}/{name}"}


def drop_postgres(name: str, pg_bin: str = "psql") -> None:
    if not re.match(r"^run_[a-z0-9_]+$", name):
        raise RuntimeError(f"refusing to drop {name!r}: not a run database")
    out = psql(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)', pg_bin=pg_bin)
    if out.returncode != 0:
        raise RuntimeError(f"drop {name} failed: {out.stderr.strip()}")


def parse_agent(path: Path) -> tuple[str, dict]:
    """A subagent file: optional `---` front matter (name, description, tools, model), then its prompt."""
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    if text.startswith("---"):
        head, _, body = text[3:].partition("\n---")
        for line in head.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip("\"'")
        body = body.lstrip("-\n")
    name = meta.get("name") or path.stem
    spec = {"description": meta.get("description") or name, "prompt": body.strip()}
    if meta.get("tools"):
        spec["tools"] = [t.strip() for t in re.split(r"[,\s]+", meta["tools"]) if t.strip()]
    if meta.get("model"):
        spec["model"] = meta["model"]
    return name, spec


def arm_files(arm: Path | None) -> tuple[list[Path], list[Path]]:
    """The arm's instruction files and subagent definitions.

    An arm is a single file, or a folder whose top-level .md files (README.md aside) are its instructions
    and whose agents/*.md files are its subagents.
    """
    if not arm:
        return [], []
    if arm.is_file():
        return [arm], []
    instructions = sorted(p for p in arm.glob("*.md") if p.name.lower() != "readme.md")
    agents = sorted((arm / "agents").glob("*.md")) if (arm / "agents").is_dir() else []
    return instructions, agents


def guard_config(root: Path, runs_root: Path, extra_forbidden: list[str]) -> dict:
    home = os.path.realpath(os.path.expanduser("~"))
    forbidden = [str(LAB_ROOT), str(runs_root), f"{home}/repos", f"{home}/.claude", f"{home}/.config/gh"]
    forbidden += [os.path.realpath(os.path.expanduser(p)) for p in extra_forbidden]
    return {
        "sandbox": str(root),
        "home": home,
        "private": [str(root / "harness")],
        "forbidden": sorted(set(forbidden)),
        "read_ok": [f"{home}/{p}" for p in (".local", ".cache", ".pyenv", ".cargo", ".rustup", "Library/Caches")],
        "write_ok": ["/dev/null", "/tmp", "/private/tmp"],
        "forbidden_words": ["grounded-class-tutor", "github.com", "api.github"],
        "log": str(root / "harness" / "guard.log"),
    }


def settings(root: Path, cfg: dict) -> dict:
    hdir = root / "harness"
    guard_cmd = f'"{sys.executable}" "{hdir / "guard.py"}" "{hdir / "guard.json"}"'
    deny = [
        "WebFetch",
        "WebSearch",
        "Bash(gh *)",
        "Bash(curl *)",
        "Bash(wget *)",
        *(f"Bash(git {s} *)" for s in ("fetch", "pull", "clone", "ls-remote", "remote", "push")),
        f"Read(/{hdir}/**)",
        f"Edit(/{hdir}/**)",
    ]
    for bad in cfg["forbidden"]:
        if not Path(root).is_relative_to(bad):
            deny += [f"Read(/{bad}/**)", f"Edit(/{bad}/**)"]
    return {
        "autoMemoryEnabled": False,
        "includeCoAuthoredBy": False,
        "permissions": {"allow": ALLOWED_TOOLS.split(), "deny": deny},
        "hooks": {"PreToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": guard_cmd}]}]},
    }


def create(
    root: Path,
    run_id: str,
    *,
    repo: str,
    repo_url: str,
    base: str,
    pr_base: str,
    ticket: Path,
    arm: Path | None,
    db: str,
    runs_root: Path,
    gh_bin: str,
    pg_bin: str = "psql",
    extra_forbidden: list[str] = (),
) -> dict:
    """Build the sandbox. Raises if the folder exists; cleans up after itself if a step fails."""
    parse_run_id(run_id)
    if root.exists():
        raise RuntimeError(f"sandbox already exists: {root}")
    root.mkdir(parents=True)
    hdir = root / "harness"
    hdir.mkdir()
    manifest = {"run_id": run_id, "root": str(root), "created": now_iso(), "database": None, "branch": None}
    write_json(hdir / "sandbox.json", manifest)
    try:
        branch = f"{run_id}/work"
        rdir = root / "repo"
        git("init", "-q", str(rdir))
        # Private repos over https authenticate through gh, as `lab` does when it pushes.
        cred = ["-c", "credential.helper=", "-c", f"credential.helper=!{gh_bin} auth git-credential"]
        git(*(cred if repo_url.startswith("https://") else []), "fetch", "-q", "--no-tags", repo_url, base, cwd=rdir)
        base_commit = git("rev-parse", "FETCH_HEAD", cwd=rdir)
        git("checkout", "-q", "-b", branch, "FETCH_HEAD", cwd=rdir)
        if not SHA_RE.match(base) and base != branch:
            git("branch", "-q", base.removeprefix("refs/heads/"), base_commit, cwd=rdir)
        git("config", "user.name", "lab-runner", cwd=rdir)
        git("config", "user.email", "lab-runner@example.invalid", cwd=rdir)
        with open(rdir / ".git" / "info" / "exclude", "a", encoding="utf-8") as f:
            f.write("\n.env\n*.db\n.venv/\n")
        manifest.update(branch=branch, base_commit=base_commit)

        (root / "scratch" / "tmp").mkdir(parents=True)
        shutil.copyfile(ticket, root / "TICKET.md")
        env = {}
        if db == "sqlite":
            (root / "db").mkdir()
            path = root / "db" / "lab.db"
            manifest["database"] = {"kind": "sqlite", "path": str(path)}
            env = {"LAB_DB": str(path), "DATABASE_URL": f"sqlite:///{path}"}
        elif db == "postgres":
            manifest["database"] = create_postgres(run_id, pg_bin)
            env = {"DATABASE_URL": manifest["database"]["url"]}
        write_json(hdir / "sandbox.json", manifest)

        instructions, agents = arm_files(arm)
        if arm and arm.is_dir():
            shutil.copytree(arm, root / "arm")
        elif arm:
            (root / "arm").mkdir()
            shutil.copyfile(arm, root / "arm" / arm.name)
        if instructions:
            parts = [f"<!-- {p.name} -->\n{p.read_text(encoding='utf-8').strip()}\n" for p in instructions]
            (hdir / "arm-prompt.md").write_text("\n".join(parts), encoding="utf-8")
        if agents:
            write_json(hdir / "agents.json", dict(parse_agent(p) for p in agents))

        cfg = guard_config(root, runs_root, list(extra_forbidden))
        write_json(hdir / "guard.json", cfg)
        shutil.copyfile(HERE / "guard.py", hdir / "guard.py")
        write_json(hdir / "settings.json", settings(root, cfg))
        (hdir / "bin").mkdir()
        lab = (HERE / "lab.py").read_text(encoding="utf-8").replace("#!/usr/bin/env python3", f"#!{sys.executable}", 1)
        (hdir / "bin" / "lab").write_text(lab, encoding="utf-8")
        (hdir / "bin" / "lab").chmod(0o755)
        write_json(
            hdir / "lab.json",
            {
                "repo": repo,
                "branch": branch,
                "pr_base": pr_base,
                "push_url": repo_url,
                "repo_dir": str(rdir),
                "ticket": str(root / "TICKET.md"),
                "sandbox": str(root),
                "private": str(hdir),
                "events": str(hdir / "lab-events.jsonl"),
                "gh": gh_bin,
            },
        )
        manifest["env"] = env
        write_json(hdir / "sandbox.json", manifest)
        append_jsonl(hdir / "events.jsonl", {"time": now_iso(), "event": "sandbox_created", "base": base_commit})
        return manifest
    except Exception:
        teardown(root, everything=True, quiet=True)
        raise


def teardown(root: Path, everything: bool = False, quiet: bool = False, pg_bin: str = "psql") -> list[str]:
    """Drop the run's database and remove what the run created. Keeps harness/ unless `everything`."""
    root = Path(os.path.realpath(root))
    manifest = read_json(root / "harness" / "sandbox.json")
    if not manifest or os.path.realpath(manifest.get("root", "")) != str(root):
        raise RuntimeError(f"{root} has no sandbox manifest of its own; refusing to remove anything")
    parse_run_id(manifest["run_id"])
    if root.name != manifest["run_id"]:
        raise RuntimeError(f"{root} does not match its manifest's run id; refusing")
    removed = []
    dbinfo = manifest.get("database") or {}
    if dbinfo.get("kind") == "postgres":
        drop_postgres(dbinfo["name"], pg_bin)
        removed.append(f"database {dbinfo['name']}")
    targets = [root] if everything else [root / n for n in ("repo", "scratch", "arm", "db", "TICKET.md")]
    for t in targets:
        if t.is_dir():
            shutil.rmtree(t)
            removed.append(str(t))
        elif t.exists():
            t.unlink()
            removed.append(str(t))
    if not everything:
        manifest["torn_down"] = now_iso()
        write_json(root / "harness" / "sandbox.json", manifest)
    if not quiet:
        for r in removed:
            print(f"removed {r}")
    return removed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m harness.sandbox", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("down", help="drop the run's database and remove its files (records kept)")
    d.add_argument("run_folder")
    d.add_argument("--all", action="store_true", help="also remove harness/ (transcript and records)")
    args = ap.parse_args(argv)
    try:
        teardown(Path(args.run_folder), everything=args.all)
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
