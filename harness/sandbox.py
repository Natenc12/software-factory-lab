"""One sandbox per run, at <runs root>/<stage>/<run-id>/, and its teardown.

    python -m harness.sandbox down <run folder> [--all]

Layout:
    repo/          fresh clone holding only the base ref's history, on branch <run-id>/work
    scratch/       the run's scratch space (also its TMPDIR)
    TICKET.md      the ticket
    arm/           the arm's files (absent for a bare arm)
    db/            SQLite database file (pipeline-lab); Postgres runs get database run_<run_id>
    harness/       records (transcript, run.json, owner log); the session cannot read or write it

The run's controls (settings, guard hook, `lab`) live outside the run folder, in
<runs root>/<stage>/.control/<run-id>/, so nothing the session can write can change them.
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
# The OS sandbox's network allowlist: package downloads only. GitHub is reached only through `lab`,
# which runs outside the sandbox. Postgres is reached through its Unix socket, not TCP.
NET_ALLOW = ["pypi.org", "files.pythonhosted.org"]


# A sealed run (opt-in per codebase) reaches no package registry and reads nothing of the machine's but its
# own run folder and the toolchain it needs. These are the toolchain folders it may read.
SEALED_READ = (".local/bin", ".local/lib/node_modules/pnpm", ".local/share/uv/python")
# The user's temp folders (macOS keeps them under /var/folders); a sealed run may not read them.
USER_TEMP = ("/private/var/folders", "/var/folders")


def run_slug(root: Path) -> str:
    """The folder name Claude Code gives a session started in this run's checkout."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(Path(root) / "repo"))


def shared_temp(tmp_root: str | None = None) -> tuple[str, list[str]]:
    """(Claude Code's shared temp folder, the temp entries a sealed run is denied).

    Claude Code's sandbox makes every command's TMPDIR /tmp/claude-<uid>, and that folder also holds every
    session's scratch (audit folders, clones). So /tmp and /tmp/claude-<uid> stay readable, and a sealed run
    is denied every other entry of /tmp and every subfolder of /tmp/claude-<uid> that exists at its start.
    """
    tmp = os.path.realpath(tmp_root or "/tmp")
    mine = os.path.join(tmp, f"claude-{os.getuid()}")
    denied = [os.path.join(tmp, e) for e in sorted(os.listdir(tmp)) if os.path.join(tmp, e) != mine]
    if os.path.isdir(mine):
        denied += [os.path.join(mine, e) for e in sorted(os.listdir(mine)) if os.path.isdir(os.path.join(mine, e))]
    return mine, denied


# Per-run package caches (setup fills them with network; the session reads them offline).
SEALED_CACHES = {
    "UV_CACHE_DIR": "{run}/scratch/uv-cache",
    "PIP_CACHE_DIR": "{run}/scratch/pip-cache",
    "npm_config_cache": "{run}/scratch/npm-cache",
}
# For the session only, after setup: package tools stay offline.
# CLAUDE_CODE_TMPDIR: Claude Code's own temp files (its shell's working-directory file) go inside the run;
# its default, /tmp/claude-<uid>, is a shared folder a sealed run may not read.
SEALED_SESSION = {
    "UV_OFFLINE": "1",
    "PIP_NO_INDEX": "1",
    "npm_config_offline": "true",
    "CLAUDE_CODE_TMPDIR": "{run}/scratch/tmp",
}


def control_dir(root: Path) -> Path:
    return Path(root).parent / ".control" / Path(root).name


def pg_socket(pg_bin: str = "psql") -> str | None:
    """The local server's Unix socket file, e.g. /tmp/.s.PGSQL.5432."""
    dirs, port = psql("SHOW unix_socket_directories", pg_bin=pg_bin), psql("SHOW port", pg_bin=pg_bin)
    if dirs.returncode != 0 or port.returncode != 0:
        return None
    first = dirs.stdout.strip().split(",")[0].strip()
    # The OS sandbox matches real paths: on macOS /tmp is a link to /private/tmp.
    return os.path.realpath(f"{first}/.s.PGSQL.{port.stdout.strip()}") if first else None


def pg_name(run_id: str) -> str:
    parse_run_id(run_id)
    return "run_" + run_id.replace("-", "_")


def psql(sql: str, db: str = "postgres", pg_bin: str = "psql") -> subprocess.CompletedProcess:
    return subprocess.run(
        [pg_bin, "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d", db, "-tAc", sql], capture_output=True, text=True
    )


def create_postgres(run_id: str, pg_bin: str = "psql") -> dict:
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
    socket = pg_socket(pg_bin)
    if not socket:
        raise RuntimeError("cannot find the Postgres server's Unix socket")
    sock_dir = socket.rsplit("/", 1)[0]
    return {"kind": "postgres", "name": name, "url": f"postgresql:///{name}?host={sock_dir}", "socket": socket}


def drop_postgres(name: str, pg_bin: str = "psql") -> None:
    if not re.match(r"^run_[a-z0-9_]+$", name):
        raise RuntimeError(f"refusing to drop {name!r}: not a run database")
    out = psql(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)', pg_bin=pg_bin)
    if out.returncode != 0:
        raise RuntimeError(f"drop {name} failed: {out.stderr.strip()}")


def fill(obj, values: dict):
    """Replace `{key}` placeholders in every string of a JSON value."""
    if isinstance(obj, str):
        for k, v in values.items():
            obj = obj.replace("{" + k + "}", v)
        return obj
    if isinstance(obj, list):
        return [fill(x, values) for x in obj]
    if isinstance(obj, dict):
        return {k: fill(v, values) for k, v in obj.items()}
    return obj


def parse_agent(path: Path, values: dict | None = None) -> tuple[str, dict]:
    """A subagent file: optional `---` front matter (name, description, tools, model, hooks), then its prompt.

    `hooks:` names a JSON file in the arm folder holding the agent's own hooks, in Claude Code's
    format. `{python}`, `{arm}` (the arm's copy in the control folder) and `{run}` (the run folder)
    are filled in from `values`.
    """
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
    if meta.get("hooks"):
        arm = path.parent.parent
        hooks_file = (arm / meta["hooks"]).resolve()
        if not hooks_file.is_relative_to(arm.resolve()) or not hooks_file.is_file():
            raise RuntimeError(f"{path.name}: hooks file {meta['hooks']} not found in the arm folder")
        spec["hooks"] = fill(json.loads(hooks_file.read_text(encoding="utf-8")), values or {})
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


# An arm's own skills ship as a plugin in the control folder, so they never sit in the run's checkout
# or reach a pull request's diff. Claude Code names plugin skills `<plugin>:<skill>`.
SKILL_PLUGIN = "work"
# Claude Code 2.1.330 keeps these three skills loaded even with disableBundledSkills (seen in the
# session's init record, 2026-11-22), so a run with skills switches them off by name.
BUILTIN_SKILLS_LEFT = ("design", "doctor", "plugin-authoring")
# Built-in commands the docs say the Skill tool can start; a run with skills may not.
BUILTIN_COMMANDS_VIA_SKILL = ("init", "security-review", "review", "ultrareview")


def skill_files(arm: Path | None) -> list[Path]:
    """An arm folder's skills: `skills/<name>/SKILL.md`, one file each (the guard blocks reads elsewhere)."""
    if not arm or not arm.is_dir() or not (arm / "skills").is_dir():
        return []
    found = []
    for folder in sorted(p for p in (arm / "skills").iterdir() if not p.name.startswith(".")):
        extra = sorted(f.name for f in folder.iterdir()) if folder.is_dir() else [folder.name]
        if extra != ["SKILL.md"]:
            raise RuntimeError(f"skill {folder.name}: a skill folder holds only SKILL.md, found {extra}")
        found.append(folder / "SKILL.md")
    return found


def parse_skill(path: Path) -> dict:
    """A skill's name, its description (loaded up front) and its body (loaded only when the skill is used)."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise RuntimeError(f"{path}: a skill starts with front matter (name, description)")
    head, _, body = text[3:].partition("\n---")
    meta = {}
    for line in head.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip("\"'")
    if meta.get("name") != path.parent.name or not meta.get("description"):
        raise RuntimeError(f"{path}: front matter needs name: {path.parent.name} and a description")
    return {"name": meta["name"], "description": meta["description"], "body": body.lstrip("-\n").strip()}


def write_skill_plugin(arm: Path, ctl: Path) -> Path | None:
    """Copy the arm's skills into a plugin folder for `--plugin-dir`. None when the arm has no skills."""
    skills = skill_files(arm)
    if not skills:
        return None
    plugin = ctl / "plugin"
    (plugin / ".claude-plugin").mkdir(parents=True)
    manifest = {"name": SKILL_PLUGIN, "version": "1.0.0", "description": "Skills for working a ticket"}
    write_json(plugin / ".claude-plugin" / "plugin.json", manifest)
    for path in skills:
        parse_skill(path)
        (plugin / "skills" / path.parent.name).mkdir(parents=True)
        shutil.copyfile(path, plugin / "skills" / path.parent.name / "SKILL.md")
    return plugin


def writable_folders(paths: list[str], cfg: dict) -> list[str]:
    """Folders outside the run a codebase's toolchain must write (e.g. `~/.cargo/registry`), as real paths.

    Refuses the home folder, `/`, and any forbidden or private place or a parent of one, so a codebase
    setting cannot open up this repo, other runs, `~/.claude` or the gh login.
    """
    out = []
    bad = [*cfg["forbidden"], *cfg["private"], cfg["sandbox"]]
    for raw in paths:
        p = os.path.realpath(os.path.expanduser(raw))
        overlaps = any(p == b or p.startswith(b.rstrip("/") + "/") or b.startswith(p.rstrip("/") + "/") for b in bad)
        if p in (cfg["home"], "/") or overlaps:
            raise RuntimeError(f"allow_write {raw}: not allowed (home, a forbidden place, or a parent of one)")
        out.append(p)
    return out


def gh_config_dir() -> str:
    """Where the owner's gh login lives, as gh itself finds it from the harness's own environment."""
    if os.environ.get("GH_CONFIG_DIR"):
        return os.path.realpath(os.path.expanduser(os.environ["GH_CONFIG_DIR"]))
    xdg = os.environ.get("XDG_CONFIG_HOME")
    return os.path.realpath(os.path.join(xdg, "gh") if xdg else os.path.expanduser("~/.config/gh"))


def guard_config(root: Path, runs_root: Path, extra_forbidden: list[str]) -> dict:
    """The guard's view of the run: its sandbox, its private folders, and places it may never touch."""
    home = os.path.realpath(os.path.expanduser("~"))
    forbidden = [str(LAB_ROOT), str(runs_root), f"{home}/repos", f"{home}/.claude", f"{home}/.config/gh"]
    forbidden += [os.path.realpath(os.path.expanduser(p)) for p in extra_forbidden]
    return {
        "sandbox": str(root),
        "home": home,
        "private": [str(root / "harness"), str(control_dir(root))],
        "forbidden": sorted(set(forbidden)),
        "read_ok": [f"{home}/{p}" for p in (".local", ".cache", ".pyenv", ".cargo", ".rustup", "Library/Caches")],
        "write_ok": ["/dev/null", "/tmp", "/private/tmp"],
        "forbidden_words": ["grounded-class-tutor", "github.com", "api.github"],
        "log": str(root / "harness" / "guard.log"),
    }


def settings(
    root: Path,
    cfg: dict,
    allow_domains: list[str] = NET_ALLOW,
    unix_sockets: list[str] = (),
    skills: list[str] = (),
    allow_write: list[str] = (),
    sealed: bool = False,
    allow_read: list[str] = (),
) -> dict:
    """The run's settings file: OS sandbox first, then permission rules and the guard hook.

    Absolute paths in permission rules start with `//`; sandbox paths are plain absolute paths. With
    `skills` (the arm's skill names), the run may call those skills and no others: Claude Code's bundled
    skills are off, and under dontAsk only the named `Skill(...)` rules are allowed.
    """
    ctl = control_dir(root)
    home = cfg["home"]
    guard_cmd = f'"{sys.executable}" "{ctl / "guard.py"}" "{ctl / "guard.json"}"'
    deny = [
        "WebFetch",
        "WebSearch",
        "Bash(gh *)",
        "Bash(curl *)",
        "Bash(wget *)",
        *(f"Bash(git {s} *)" for s in ("fetch", "pull", "clone", "ls-remote", "remote", "push")),
        *(f"{tool}(/{d}/**)" for d in cfg["private"] for tool in ("Read", "Edit")),
    ]
    for bad in cfg["forbidden"]:
        if not Path(root).is_relative_to(bad):
            deny += [f"Read(/{bad}/**)", f"Edit(/{bad}/**)"]
    lab = str(ctl / "bin" / "lab")
    sandbox = {
        "enabled": True,
        "failIfUnavailable": True,
        "allowUnsandboxedCommands": False,
        "autoAllowBashIfSandboxed": True,
        # Only a call that is `lab ...` and nothing else runs outside the sandbox (docs: every command in
        # the call must match; redirects, cd and $(...) keep a call sandboxed).
        "excludedCommands": ["lab", "lab *", lab, f"{lab} *"],
        "filesystem": {
            "allowWrite": [*([] if sealed else [f"{home}/.cache/uv"]), *allow_write],
            "denyWrite": list(cfg["private"]),
            "denyRead": sorted(
                {
                    *cfg["forbidden"],
                    *cfg["private"],
                    *(f"{home}/{p}" for p in (".ssh", ".aws", ".netrc", ".gnupg")),
                    # Sealed: the whole home folder and the shared temp entries; the narrower allowRead wins.
                    *([home, *USER_TEMP, *cfg.get("temp_denied", [])] if sealed else []),
                }
            ),
            "allowRead": [str(root), *allow_read],
        },
        # allowLocalBinding: a project's own tests may start a server on localhost and talk to it.
        "network": {
            "allowedDomains": list(allow_domains),
            "allowUnixSockets": list(unix_sockets),
            "allowLocalBinding": True,
        },
    }
    file_tools = [t for t in ALLOWED_TOOLS.split() if t not in ("Edit", "Write", "NotebookEdit")]
    out = {
        "autoMemoryEnabled": False,
        "includeCoAuthoredBy": False,
        # `Edit(...)` covers Write and NotebookEdit; scoped, because an Edit allow rule also widens
        # where the sandbox lets Bash write.
        "permissions": {"allow": [*file_tools, f"Edit(/{root}/**)"], "deny": deny},
        "sandbox": sandbox,
        "hooks": {"PreToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": guard_cmd}]}]},
    }
    if skills:
        out["disableBundledSkills"] = True
        out["skillOverrides"] = {name: "off" for name in BUILTIN_SKILLS_LEFT}
        out["permissions"]["allow"] += [f"Skill({SKILL_PLUGIN}:{name})" for name in skills]
        out["permissions"]["deny"] += [f"Skill({name})" for name in BUILTIN_COMMANDS_VIA_SKILL]
    return out


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
    allow_domains: list[str] = (),
    extra_env: dict | None = None,
    allow_write: list[str] = (),
    sealed: bool = False,
    own_packages: list[str] = (),
) -> dict:
    """Build the sandbox. Raises if the folder exists; cleans up after itself if a step fails."""
    parse_run_id(run_id)
    ctl = control_dir(root)
    if root.exists() or ctl.exists():
        raise RuntimeError(f"sandbox already exists: {root}")
    root.mkdir(parents=True)
    hdir = root / "harness"
    hdir.mkdir()
    manifest = {
        "run_id": run_id,
        "root": str(root),
        "control": str(ctl),
        "created": now_iso(),
        "database": None,
        "branch": None,
    }
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
            env = {
                "DATABASE_URL": manifest["database"]["url"],
                "PGHOST": manifest["database"]["socket"].rsplit("/", 1)[0],
            }
        # Codebase settings the run needs (for example UV_PYTHON); the database variables always win.
        # `{run}` in a value is this run's folder, so a toolchain cache can live inside the run.
        if sealed:
            extra_env = {**SEALED_CACHES, **(extra_env or {})}
            manifest["session_env"] = {k: v.replace("{run}", str(root)) for k, v in SEALED_SESSION.items()}
            manifest["sealed"] = True
        env = {**{k: str(v).replace("{run}", str(root)) for k, v in (extra_env or {}).items()}, **env}
        write_json(hdir / "sandbox.json", manifest)

        ctl.mkdir(parents=True)
        instructions, agents = arm_files(arm)
        if arm and arm.is_dir():
            # The arm's skills reach the session only through the Skill tool, from the control folder.
            top_skills = lambda d, names: ["skills"] if Path(d) == arm else []  # noqa: E731
            shutil.copytree(arm, root / "arm", ignore=top_skills)
        elif arm:
            (root / "arm").mkdir()
            shutil.copyfile(arm, root / "arm" / arm.name)
        if instructions:
            parts = [f"<!-- {p.name} -->\n{p.read_text(encoding='utf-8').strip()}\n" for p in instructions]
            (ctl / "arm-prompt.md").write_text("\n".join(parts), encoding="utf-8")
        if agents:
            # Agent hooks run from a copy in the control folder, which the session can neither read nor change.
            shutil.copytree(arm, ctl / "arm")
            values = {"python": sys.executable, "arm": str(ctl / "arm"), "run": str(root)}
            write_json(ctl / "agents.json", dict(parse_agent(p, values) for p in agents))

        plugin = write_skill_plugin(arm, ctl) if arm else None
        cfg = guard_config(root, runs_root, list(extra_forbidden))
        writes = writable_folders(list(allow_write), cfg)
        reads = []
        if sealed:
            # The guard agrees with the sandbox: home only for the toolchain, no shared temp entries, and no
            # path under another session's folder in Claude Code's shared temp folder, even one made later.
            reads = [os.path.realpath(os.path.join(cfg["home"], p)) for p in SEALED_READ]
            cfg["read_ok"] = reads
            mine, denied = shared_temp()
            cfg["temp_denied"] = [d for d in denied if not str(root).startswith(d.rstrip("/") + "/")]
            cfg["shared_temp"] = mine
            cfg["own_temp"] = os.path.join(mine, run_slug(root))
            cfg["forbidden"] = sorted({*cfg["forbidden"], *USER_TEMP, *(os.path.realpath(t) for t in USER_TEMP)})
            cfg["write_ok"] = ["/dev/null"]
        cfg["read_ok"] = sorted({*cfg["read_ok"], *writes})
        cfg["own_packages"] = sorted(set(own_packages))
        sockets = [manifest["database"]["socket"]] if db == "postgres" else []
        skills = [p.parent.name for p in skill_files(arm)] if plugin else []
        domains = [*([] if sealed else NET_ALLOW), *allow_domains]
        run_settings = settings(
            root, cfg, domains, sockets, skills=skills, allow_write=writes, sealed=sealed, allow_read=[*reads, *sockets]
        )
        for folder in (ctl, hdir):  # live copies in the control folder, a record copy in harness/
            write_json(folder / "guard.json", cfg)
            write_json(folder / "settings.json", run_settings)
        shutil.copyfile(HERE / "guard.py", ctl / "guard.py")
        (ctl / "bin").mkdir()
        lab = (HERE / "lab.py").read_text(encoding="utf-8").replace("#!/usr/bin/env python3", f"#!{sys.executable}", 1)
        (ctl / "bin" / "lab").write_text(lab, encoding="utf-8")
        (ctl / "bin" / "lab").chmod(0o755)
        write_json(
            ctl / "lab.json",
            {
                "repo": repo,
                "branch": branch,
                "pr_base": pr_base,
                "push_url": repo_url,
                "repo_dir": str(rdir),
                "ticket": str(root / "TICKET.md"),
                "sandbox": str(root),
                "private": [str(hdir), str(ctl)],
                "events": str(hdir / "lab-events.jsonl"),
                "gh": gh_bin,
                # `lab` runs inside the session's environment, which a codebase's run_env can change
                # (XDG_CONFIG_HOME moves gh's login). Its gh and git calls use these instead.
                "owner_env": {"HOME": os.path.realpath(os.path.expanduser("~")), "GH_CONFIG_DIR": gh_config_dir()},
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
    ctl = Path(manifest.get("control") or control_dir(root))
    if ctl == control_dir(root) and (read_json(ctl / "lab.json") or {}).get("sandbox") == str(root):
        targets.append(ctl)
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
