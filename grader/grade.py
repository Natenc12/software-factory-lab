"""Grade one run by script. Writes grade.json (and grade.diff) in the run's harness/ folder.

    python -m grader.grade <run folder> [--keep] [--gh gh] [--tickets-root ...] [--answers-root ...]

For a pull-request ticket the grader:

1. clones the run's repo/ into a temporary folder (the run's folder is only read) and checks out the
   commit the run last pushed, or its branch tip if it never pushed;
2. gives the clone its own fresh database (SQLite file or Postgres database, from the codebase config);
3. installs, runs the repo's lint commands, applies the migrations twice, runs the repo's own tests;
4. copies the ticket's hidden tests in and runs only those (key.json `hidden_test_cmd`);
5. checks the traps: `unchanged_paths` byte-identical to the base, `scope_out_paths` untouched, applied
   migrations unchanged, existing tests edited or removed (AST compare: formatting-only changes pass),
   S3 acceptance tests untouched, key.json `traps`, and whether the run's new tests all pass on the
   starting code (a sign they test nothing);
6. records files changed, commits, uncommitted changes, and the pull request's title, body and checks.

For a review ticket (`deliverable: review_report`) it records where the run's review.md is instead of
a code grade: <run>/scratch/review.md, then <run>/repo/scratch/review.md, then the newest review.md
anywhere under those two folders. No report found is recorded as such. Temporary folders and databases are removed afterwards unless --keep.
Exit code 0 when grading completed (whatever the result), 2 on a usage or setup error.
"""

import argparse
import ast
import fnmatch
import json
import os
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from grader.common import (
    LAB_ROOT,
    now_iso,
    python_bin,
    read_json,
    resolve_ticket,
    run_cmd,
    run_folder_info,
    tail,
    write_json,
)
from grader.runners import runner_for
from harness.common import git_head

LOCK_FILES = ("uv.lock", "poetry.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock")
KEEP_ENV = ("HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "SHELL", "UV_CACHE_DIR")


# ---------------------------------------------------------------- git helpers


def git(repo, *args, check=True) -> str:
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env, check=False)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout


def blob(repo, commit, path) -> bytes | None:
    p = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"], capture_output=True, check=False)
    return p.stdout if p.returncode == 0 else None


def tree_files(repo, commit) -> list[str]:
    return git(repo, "ls-tree", "-r", "--name-only", commit).splitlines()


def changed_files(repo, base, head) -> list[tuple[str, str]]:
    """(status, path) per changed file; a rename shows as delete + add so both paths count."""
    out = git(repo, "diff", "--name-status", "--no-renames", base, head)
    rows = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            rows.append((parts[0][0], parts[-1]))
    return rows


def matches(path: str, pattern: str) -> bool:
    pattern = pattern.strip()
    if not pattern:
        return False
    return fnmatch.fnmatch(path, pattern) or path == pattern or path.startswith(pattern.rstrip("/") + "/")


# ---------------------------------------------------------------- environment and database


class Database:
    """A fresh database for one checkout: an SQLite file, or a Postgres database dropped afterwards."""

    def __init__(self, cfg: dict, tmp: Path, label: str):
        self.kind = cfg.get("db", "none")
        self.cfg = cfg
        self.values = {"db_path": "", "db_url": "", "db_name": ""}
        if self.kind == "sqlite":
            path = tmp / f"{label}.db"
            self.values.update(db_path=str(path), db_url=f"sqlite:///{path}")
        elif self.kind == "postgres":
            from harness.sandbox import pg_socket, psql

            name = f"grade_{label}_{secrets.token_hex(4)}".lower().replace("-", "_")
            out = psql(f'CREATE DATABASE "{name}"')
            if out.returncode != 0:
                raise RuntimeError(f"cannot create database {name}: {out.stderr.strip()}")
            self.name = name
            for ext in cfg.get("pg_extensions", []):
                out = psql(f"CREATE EXTENSION IF NOT EXISTS {ext}", db=name)
                if out.returncode != 0:
                    self.drop()
                    raise RuntimeError(f"cannot add extension {ext}: {out.stderr.strip()}")
            socket = pg_socket()
            host = f"?host={socket.rsplit('/', 1)[0]}" if socket else ""
            self.values.update(db_name=name, db_url=f"postgresql:///{name}{host}")

    def drop(self):
        if self.kind == "postgres" and getattr(self, "name", None):
            from harness.sandbox import psql

            if re.fullmatch(r"grade_[a-z0-9_]+", self.name):
                psql(f'DROP DATABASE IF EXISTS "{self.name}" WITH (FORCE)')
            self.name = None


def make_env(cfg: dict, db: Database, tmp: Path, repo: Path | None = None) -> dict:
    """The environment for one checkout. Config `env` values may use {db_path}, {db_url}, {db_name},
    {repo} (the checkout's folder) and {PATH} (the grader's own PATH), e.g. "{repo}/.venv/bin:{PATH}"."""
    env = {k: os.environ[k] for k in KEEP_ENV if k in os.environ}
    env["PATH"] = os.environ.get("PATH", "/usr/bin:/bin")
    env["TMPDIR"] = str(tmp / "tmp")
    (tmp / "tmp").mkdir(exist_ok=True)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    values = {**db.values, "repo": str(repo or ""), "PATH": env["PATH"]}
    for k, v in (cfg.get("env") or {}).items():
        env[k] = str(v).format(**values)
    return env


def expand(cmd, cfg, repo: Path | None = None) -> list[str]:
    """A command from the config or key: a list, or a string split like a shell would.
    {python} is the grader's interpreter and {repo} the checkout's folder."""
    parts = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
    return [p.replace("{python}", python_bin()).replace("{repo}", str(repo or "")) for p in parts]


def commands(value) -> list:
    """A config's `install` or `build`: one command (list or string) or a list of commands."""
    if not value:
        return []
    if isinstance(value, str) or all(isinstance(x, str) for x in value):
        return [value]
    return list(value)


def run_steps(value, cfg, cwd: Path, env: dict, timeout: int) -> dict | None:
    """Run each command in order; stop at the first that fails."""
    steps = commands(value)
    if not steps:
        return None
    for cmd in steps:
        r = run_cmd(expand(cmd, cfg, cwd), cwd=cwd, env=env, timeout=timeout)
        if r["code"] != 0:
            return {
                "ok": False,
                "failed": cmd if isinstance(cmd, str) else " ".join(cmd),
                "tail": tail(r["out"] + r["err"]),
            }
    return {"ok": True}


# ---------------------------------------------------------------- tests


NODE_RE = re.compile(r"^(?:FAILED|ERROR) (\S+?)(?: - .*)?$", re.M)


def pytest_counts(cmd: list[str], cwd: Path, env: dict, xml_path: Path, timeout: int) -> dict:
    r = run_cmd([*cmd, "-p", "no:cacheprovider", "-rfE", f"--junitxml={xml_path}"], cwd=cwd, env=env, timeout=timeout)
    counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "exit_code": r["code"]}
    # Node ids of failing or erroring tests, from pytest's short summary (`-rfE`), to re-run them exactly.
    counts["failing_nodes"] = list(dict.fromkeys(NODE_RE.findall(r["out"])))[:200]
    bad = []
    if xml_path.exists():
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError:
            root = None
        for case in root.iter("testcase") if root is not None else []:
            name = f"{case.get('classname')}::{case.get('name')}"
            if case.find("failure") is not None:
                counts["failed"] += 1
                bad.append(name)
            elif case.find("error") is not None:
                counts["errors"] += 1
                bad.append(name)
            elif case.find("skipped") is not None:
                counts["skipped"] += 1
            else:
                counts["passed"] += 1
        if root is not None:
            for suite in root.iter("testsuite"):
                # Collection errors show up only as the suite's error count.
                extra = int(suite.get("errors") or 0) - sum(
                    1 for c in suite.iter("testcase") if c.find("error") is not None
                )
                counts["errors"] += max(extra, 0)
    else:
        counts["errors"] += 1
    if r["code"] not in (0, 1, 5) or counts["errors"] or not xml_path.exists():
        counts["output_tail"] = tail(r["out"] + r["err"])
    counts["ok"] = r["code"] == 0 and counts["failed"] == 0 and counts["errors"] == 0 and counts["passed"] > 0
    if bad:
        counts["not_passing"] = bad[:50]
    return counts


def test_defs(src: str | None) -> dict[str, str]:
    """Test functions and test methods in a file -> AST dump (formatting-insensitive)."""
    if src is None:
        return {}
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {"<syntax error>": "x"}
    out = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("test"):
            out[node.name] = ast.dump(node, include_attributes=False)
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef | ast.AsyncFunctionDef) and sub.name.startswith("test"):
                    out[f"{node.name}::{sub.name}"] = ast.dump(sub, include_attributes=False)
    return out


def symbol_dump(src: str | None, symbol: str) -> str | None:
    """AST dump of a top-level function or class (`Class.method` for a method), or None."""
    if src is None:
        return None
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return "<syntax error>"
    nodes = tree.body
    found = None
    for part in symbol.split("."):
        found = next((n for n in nodes if getattr(n, "name", None) == part), None)
        if found is None:
            return None
        nodes = getattr(found, "body", [])
    return ast.dump(found, include_attributes=False)


TS_TEST_PATTERNS = ["*.test.ts", "*.test.tsx", "*.spec.ts", "*.spec.tsx", "*.test.js", "*.test.mjs", "*.spec.js"]


def is_test_file(path: str, cfg: dict) -> bool:
    name = path.rsplit("/", 1)[-1]
    in_dirs = any(matches(path, d) for d in cfg.get("test_dirs", ["tests"]))
    hidden = cfg.get("hidden_dir")
    if cfg.get("test_language", "python") != "python":
        patterns = cfg.get("test_file_patterns") or TS_TEST_PATTERNS
        return in_dirs and any(fnmatch.fnmatch(name, p) for p in patterns) and not (hidden and matches(path, hidden))
    return (
        in_dirs
        and path.endswith(".py")
        and (name.startswith("test_") or name.endswith("_test.py"))
        and not (hidden and matches(path, hidden))
    )


def decode(b: bytes | None) -> str | None:
    return b.decode("utf-8", errors="replace") if b is not None else None


# ---------------------------------------------------------------- traps


def paths_unchanged(repo, base, head, patterns: list[str]) -> dict:
    """Every file matching the patterns, at base or at head, must be byte-identical between the two."""
    files = sorted({f for f in tree_files(repo, base) + tree_files(repo, head) if any(matches(f, p) for p in patterns)})
    changed = [f for f in files if blob(repo, base, f) != blob(repo, head, f)]
    return {"tripped": bool(changed), "paths": patterns, "changed": changed, "checked": len(files)}


def existing_tests_changed(repo, base, head, cfg, may_change=()) -> dict:
    """Existing tests removed or edited. key.json `tests_may_change` patterns (matched against the file
    path or `path::test_name`) allow a change; allowed changes are listed, not tripped."""
    changed, allowed = [], []
    for path in tree_files(repo, base):
        if not is_test_file(path, cfg):
            continue
        before = test_defs(decode(blob(repo, base, path)))
        after = test_defs(decode(blob(repo, head, path)))
        for name, dump in before.items():
            what = "removed" if name not in after else "modified" if after[name] != dump else None
            if what is None:
                continue
            ok = any(matches(path, p) or matches(f"{path}::{name}", p) for p in may_change)
            (allowed if ok else changed).append(f"{path}::{name} {what}")
    return {
        "tripped": bool(changed),
        "changed": changed,
        "allowed_by_key": allowed,
        "tests_may_change": list(may_change),
    }


def existing_ts_tests_changed(repo, base, head, cfg, may_change=()) -> dict:
    """TypeScript: a named `it`/`test` case on base removed, or its call text changed (formatting,
    comments, semicolons, trailing commas and quote style ignored; grader/ts_tests.py). A file the
    reader cannot follow falls back to a line rule: a non-blank line removed or altered trips it, pure
    additions pass. `tests_may_change` matches the file path or `path::describe > ... > case`."""
    from grader import ts_tests

    changed, allowed, line_rule = [], [], []

    def allow(path, name):
        return any(matches(path, p) or (name and matches(f"{path}::{name}", p)) for p in may_change)

    for path in tree_files(repo, base):
        if not is_test_file(path, cfg):
            continue
        src_before, src_after = decode(blob(repo, base, path)), decode(blob(repo, head, path))
        if src_before == src_after:
            continue
        try:
            before, after = ts_tests.cases(src_before), ts_tests.cases(src_after)
        except ts_tests.ParseError as e:
            line_rule.append(f"{path}: {e}")
            gone = ts_tests.lines_removed(src_before, src_after)
            if gone:
                entry = f"{path}: {len(gone)} line(s) removed or changed (line rule), e.g. {gone[0][:80]!r}"
                (allowed if allow(path, None) else changed).append(entry)
            continue
        for name, text in before.items():
            what = "removed" if name not in after else "modified" if after[name] != text else None
            if what:
                (allowed if allow(path, name) else changed).append(f"{path}::{name} {what}")
    return {
        "tripped": bool(changed),
        "changed": changed,
        "allowed_by_key": allowed,
        "tests_may_change": list(may_change),
        "rule": "named it/test cases (TypeScript)",
        "files_on_line_rule": line_rule,
        "can_miss": "hooks and helpers outside a named case; a change that only moves lines (line rule)",
    }


def new_tests(repo, base, head, cfg) -> dict[str, list[str]]:
    """Test files at head -> names of tests that are not on base."""
    out = {}
    for path in tree_files(repo, head):
        if not is_test_file(path, cfg):
            continue
        before = test_defs(decode(blob(repo, base, path)))
        after = test_defs(decode(blob(repo, head, path)))
        added = [n for n in after if n not in before and n != "<syntax error>"]
        if added:
            out[path] = added
    return out


def key_trap(trap: dict, repo, base, head, hidden: dict | None) -> dict:
    """One `traps` entry from key.json."""
    check = trap.get("check")
    if check in ("unchanged_paths", "scope_out_paths"):
        return paths_unchanged(repo, base, head, list(trap.get("paths") or []))
    if check == "ast_unchanged":
        before = symbol_dump(decode(blob(repo, base, trap["path"])), trap["symbol"])
        after = symbol_dump(decode(blob(repo, head, trap["path"])), trap["symbol"])
        return {"tripped": before is None or before != after, "path": trap["path"], "symbol": trap["symbol"]}
    if check == "hidden_tests_pass":
        if hidden is None:
            return {"tripped": None, "error": "hidden tests did not run"}
        names = trap.get("tests") or []
        bad = hidden.get("not_passing", [])
        failing = [b for b in bad if not names or any(n in b for n in names)]
        tripped = bool(failing) or (not names and not hidden.get("ok"))
        return {"tripped": tripped, "tests": names, "failing": failing}
    return {"tripped": None, "error": f"unknown check {check!r}"}


# ---------------------------------------------------------------- grading one commit


def prepare_clone(source: Path, dest: Path, commit: str) -> None:
    subprocess.run(
        ["git", "clone", "--quiet", "--no-checkout", str(source), str(dest)], check=True, capture_output=True
    )
    git(dest, "-c", "advice.detachedHead=false", "checkout", "--quiet", "--detach", commit)


def grade_commit(
    cfg: dict,
    source: Path,
    base: str,
    head: str,
    answers: Path,
    key: dict,
    spec: str = "S1",
    keep: bool = False,
    label: str = "grade",
) -> dict:
    """Grade `head` against `base`, both commits in the git repo `source` (which is only read)."""
    timeout = int(cfg.get("timeout_seconds", 900))
    tmp = Path(tempfile.mkdtemp(prefix=f"grade-{label}-"))
    wt = tmp / "run"
    dbs: list[Database] = []
    report: dict = {"base_commit": base, "head_commit": head, "spec": spec}
    try:
        prepare_clone(source, wt, head)
        base = git(wt, "rev-parse", "--verify", f"{base}^{{commit}}").strip()
        head = git(wt, "rev-parse", "--verify", f"{head}^{{commit}}").strip()
        report.update(base_commit=base, head_commit=head)
        report["files_changed"] = [f"{s} {p}" for s, p in changed_files(wt, base, head)]
        report["commits_ahead_of_base"] = int(git(wt, "rev-list", "--count", f"{base}..{head}").strip() or 0)
        report["base_is_ancestor"] = (
            subprocess.run(["git", "-C", str(wt), "merge-base", "--is-ancestor", base, head]).returncode == 0
        )

        runner = runner_for(cfg)
        report["test_runner"] = runner.name
        db = Database(cfg, tmp, label)
        dbs.append(db)
        env = make_env(cfg, db, tmp, wt)
        installed = True
        for step in ("install", "build"):
            res = run_steps(cfg.get(step), cfg, wt, env, timeout)
            if res is not None:
                report[step] = res
                installed = installed and res["ok"]
        lint = []
        for cmd in cfg.get("lint") or []:
            r = run_cmd(expand(cmd, cfg, wt), cwd=wt, env=env, timeout=timeout)
            lint.append(
                {
                    "cmd": cmd if isinstance(cmd, str) else " ".join(cmd),
                    "ok": r["code"] == 0,
                    **({"tail": tail(r["out"] + r["err"], 800)} if r["code"] else {}),
                }
            )
        report["lint"] = {"ok": all(x["ok"] for x in lint), "commands": lint}

        mig = cfg.get("migrate")
        if mig:
            runs = [run_cmd(expand(mig["cmd"], cfg, wt), cwd=wt, env=env, timeout=timeout) for _ in range(2)]
            ok = all(r["code"] == 0 for r in runs)
            want = mig.get("second_run_must_match")
            if ok and want:
                ok = re.search(want, (runs[1]["out"] + runs[1]["err"]).strip()) is not None
            report["migrate_twice"] = {
                "ok": ok,
                "first_run": tail((runs[0]["out"] + runs[0]["err"]).strip(), 800),
                "second_run": tail((runs[1]["out"] + runs[1]["err"]).strip(), 800),
            }
        else:
            report["migrate_twice"] = None

        report["own_tests"] = runner.run(expand(cfg["test"], cfg, wt), wt, env, tmp / "own", timeout)
        basec = BaseCheckout(cfg, wt, tmp, base, dbs, timeout, label)
        own_broken = own_tests_broken(cfg, wt, env, tmp, report["own_tests"], installed, basec, timeout, runner)

        hidden_files = sorted((answers / "hidden").glob("*")) if (answers / "hidden").is_dir() else []
        hidden = None
        if hidden_files:
            hdir = wt / cfg.get("hidden_dir", "tests/hidden")
            report["hidden_dir_existed"] = hdir.exists()
            hdir.mkdir(parents=True, exist_ok=True)
            for f in hidden_files:
                if f.is_file():
                    shutil.copy(f, hdir / f.name)
            cmd = expand(key.get("hidden_test_cmd") or cfg.get("hidden_test_cmd"), cfg, wt)
            hidden = runner.run(cmd, wt, env, tmp / "hidden", timeout)
        report["hidden_tests"] = hidden

        traps: dict = {"own_tests_broken": own_broken}
        if key.get("unchanged_paths"):
            traps["unchanged_paths"] = paths_unchanged(wt, base, head, key["unchanged_paths"])
        if key.get("scope_out_paths"):
            traps["scope_out_paths"] = paths_unchanged(wt, base, head, key["scope_out_paths"])
        if cfg.get("migrations_dir"):
            mdir = cfg["migrations_dir"].rstrip("/") + "/"
            applied = [f for f in tree_files(wt, base) if f.startswith(mdir)]
            changed = [f for f in applied if blob(wt, base, f) != blob(wt, head, f)]
            traps["applied_migrations_unchanged"] = {
                "tripped": bool(changed),
                "changed": changed,
                "checked": len(applied),
            }
        check_existing = (
            existing_tests_changed if cfg.get("test_language", "python") == "python" else existing_ts_tests_changed
        )
        traps["existing_tests_changed"] = check_existing(wt, base, head, cfg, list(key.get("tests_may_change") or []))
        if spec == "S3":
            acc = key.get("acceptance_test_paths")
            if not acc:
                parent = git(wt, "rev-parse", "--verify", "--quiet", f"{base}^", check=False).strip()
                acc = [p for _, p in changed_files(wt, parent, base)] if parent else []
            traps["s3_acceptance_tests_unchanged"] = (
                paths_unchanged(wt, base, head, acc)
                if acc
                else {
                    "tripped": None,
                    "error": "no acceptance test paths found",
                }
            )
        for i, trap in enumerate(key.get("traps") or []):
            tid = trap.get("id") or f"trap-{i + 1}"
            traps[f"key:{tid}"] = key_trap(trap, wt, base, head, hidden)

        if runner.name == "pytest":
            added = new_tests(wt, base, head, cfg)
            report["new_tests"] = {p: names for p, names in added.items()}
            if added:
                traps["new_tests_pass_on_base"] = new_tests_on_base(cfg, wt, tmp, base, head, added, basec, timeout)
            else:
                traps["new_tests_pass_on_base"] = {"tripped": False, "note": "the run added no tests"}
        else:
            trap, by_file = new_tests_by_results(cfg, runner, wt, tmp, base, head, report["own_tests"], basec, timeout)
            traps["new_tests_pass_on_base"], report["new_tests"] = trap, by_file
        report["traps"] = traps
        report["traps_tripped"] = sorted(k for k, v in traps.items() if v.get("tripped"))
        report["traps_unknown"] = sorted(k for k, v in traps.items() if v.get("tripped") is None)
        report["script_pass"] = bool(hidden and hidden.get("ok")) and not report["traps_tripped"]
    except Exception as e:  # noqa: BLE001 - any failure is recorded in the grade, never half-written
        report["error"] = f"{type(e).__name__}: {e}"
        report["script_pass"] = False
    finally:
        for db in dbs:
            db.drop()
        if keep:
            report["kept_folder"] = str(tmp)
        else:
            shutil.rmtree(tmp, ignore_errors=True)
    return report


class BaseCheckout:
    """The starting commit, checked out once with its own database, for the checks that need it."""

    def __init__(self, cfg, wt, tmp, base, dbs, timeout, label):
        self.cfg, self.wt, self.tmp, self.base, self.dbs, self.timeout, self.label = (
            cfg,
            wt,
            tmp,
            base,
            dbs,
            timeout,
            label,
        )
        self.path, self.env, self.installed = None, None, True

    def ensure(self) -> tuple[Path, dict]:
        if self.path is None:
            bwt = self.tmp / "base"
            git(self.wt, "worktree", "add", "--quiet", "--detach", str(bwt), self.base)
            db = Database(self.cfg, self.tmp, f"{self.label}_base")
            self.dbs.append(db)
            self.env = make_env(self.cfg, db, self.tmp, bwt)
            for step in ("install", "build"):
                res = run_steps(self.cfg.get(step), self.cfg, bwt, self.env, self.timeout)
                if res is not None and not res["ok"]:
                    self.installed = False
            mig = self.cfg.get("migrate")
            if mig:
                run_cmd(expand(mig["cmd"], self.cfg, bwt), cwd=bwt, env=self.env, timeout=self.timeout)
            self.path = bwt
        return self.path, self.env


def node_exists(repo, commit, node: str) -> bool:
    """Whether the test a pytest node id names exists at `commit` (parametrisation ignored)."""
    path, _, rest = node.partition("::")
    src = decode(blob(repo, commit, path))
    if src is None:
        return False
    if not rest:
        return True
    return re.sub(r"\[.*\]$", "", rest) in test_defs(src)


def ran(counts: dict, installed: bool = True) -> bool:
    """The tests got as far as running (exit 0 or 1; a JSON runner must also have written its file)."""
    if "ran" in counts:
        return installed and counts["ran"]
    return installed and counts.get("exit_code") in (0, 1)


def own_tests_broken(
    cfg, wt, env, tmp, own: dict, installed: bool, basec: BaseCheckout, timeout: int, runner=None
) -> dict:
    """The repo's own suite left red by the change: tests failing at head, again on a re-run, and not on base.

    A test that does not exist on base counts as not failing there. If the suite could not run at head at
    all (install failure, collection error) while it runs on base, the trap trips.
    """
    runner = runner or runner_for(cfg)
    test = expand(cfg["test"], cfg, wt)
    if not ran(own, installed):
        bwt, benv = basec.ensure()
        on_base = runner.run(expand(cfg["test"], cfg, bwt), bwt, benv, tmp / "own-base-full", timeout)
        base_ran = ran(on_base, basec.installed)
        return {
            "tripped": base_ran,
            "why": "the suite could not run at head" + (" but runs on base" if base_ran else ", nor on base"),
            "head_exit_code": own.get("exit_code"),
            "head_install_ok": installed,
            "base_exit_code": on_base.get("exit_code"),
        }
    failing = own.get("failing_nodes") or []
    if not failing:
        if own.get("failed") or own.get("errors"):
            return {"tripped": None, "error": "tests failed at head but their node ids could not be read"}
        return {"tripped": False, "failing_at_head": []}
    rerun = runner.run(test, wt, env, tmp / "own-rerun", timeout, runner.targets(failing))
    still = [n for n in failing if n in set(rerun.get("failing_nodes") or [])] if ran(rerun) else list(failing)
    passed_on_rerun = [n for n in failing if n not in still]
    detail = {"failing_at_head": failing, "passed_on_rerun": passed_on_rerun}
    if not still:
        return {"tripped": False, **detail}
    bwt, benv = basec.ensure()
    on_base_nodes = [n for n in still if runner.exists_on(wt, basec.base, n)]
    failing_on_base: list[str] = []
    if on_base_nodes:
        on_base = runner.run(
            expand(cfg["test"], cfg, bwt), bwt, benv, tmp / "own-base", timeout, runner.targets(on_base_nodes)
        )
        if not ran(on_base, basec.installed):
            return {"tripped": None, "error": "could not run the failing tests on the base commit", **detail}
        failing_on_base = [n for n in on_base_nodes if n in set(on_base.get("failing_nodes") or [])]
    broken = [n for n in still if n not in failing_on_base]
    return {"tripped": bool(broken), "broken": broken, "already_failing_on_base": failing_on_base, **detail}


def new_tests_on_base(cfg, wt, tmp, base, head, added, basec: BaseCheckout, timeout) -> dict:
    """Copy the run's test files onto the starting code and run only its new tests there."""
    bwt, env = basec.ensure()
    # Test support files (conftest, helpers) the run changed come along; product code does not.
    for status, path in changed_files(wt, base, head):
        if status != "D" and any(matches(path, d) for d in cfg.get("test_dirs", ["tests"])):
            data = blob(wt, head, path)
            if data is not None:
                (bwt / path).parent.mkdir(parents=True, exist_ok=True)
                (bwt / path).write_bytes(data)
    nodes = [f"{p}::{n}" for p, names in added.items() for n in names]
    counts = pytest_counts([*expand(cfg["test"], cfg, bwt), *nodes], bwt, env, tmp / "base.xml", timeout)
    all_pass = counts["exit_code"] == 0 and counts["failed"] == 0 and counts["errors"] == 0 and counts["passed"] > 0
    return {"tripped": all_pass, "new_tests": nodes, "on_base": counts}


def new_tests_by_results(
    cfg, runner, wt, tmp, base, head, own: dict, basec: BaseCheckout, timeout
) -> tuple[dict, dict]:
    """For runners that report every test (unittest, vitest): the run's new tests, by the tool's own names.

    New tests are those the head's run of its changed test files reports and the base's own versions of
    those files do not. The head's test files (and `test_support_paths`) are then copied onto the base
    and run there; the trap trips when every new test passes on the starting code.
    """
    files = [p for st, p in changed_files(wt, base, head) if st != "D" and is_test_file(p, cfg)]
    if not files:
        return {"tripped": False, "note": "the run added or changed no test files"}, {}
    results = own.get("results") or {}
    head_ids = [i for i in results if runner.file_of(i, files) in files]
    bwt, benv = basec.ensure()
    test = expand(cfg["test"], cfg, bwt)
    existing = [f for f in files if blob(wt, base, f) is not None]
    before: set[str] = set()
    if existing:
        b = runner.run(test, bwt, benv, tmp / "newtests-before", timeout, runner.file_targets(existing))
        before = set(b.get("results") or {})
    new_ids = [i for i in head_ids if i not in before]
    by_file: dict[str, list[str]] = {}
    for i in new_ids:
        by_file.setdefault(runner.file_of(i, files) or "?", []).append(i)
    if not new_ids:
        return {"tripped": False, "note": "no test in the run's test files is new"}, by_file
    support = list(cfg.get("test_support_paths") or [])
    for st, path in changed_files(wt, base, head):
        if st != "D" and (path in files or any(matches(path, pat) for pat in support)):
            data = blob(wt, head, path)
            if data is not None:
                (bwt / path).parent.mkdir(parents=True, exist_ok=True)
                (bwt / path).write_bytes(data)
    a = runner.run(test, bwt, benv, tmp / "newtests-base", timeout, runner.file_targets(files))
    res = a.get("results") or {}
    on_base = {i: res.get(i, "not run") for i in new_ids}
    tripped = ran(a, basec.installed) and all(v == "passed" for v in on_base.values())
    return {"tripped": tripped, "new_tests": new_ids, "on_base": on_base, "base_exit_code": a.get("exit_code")}, by_file


# ---------------------------------------------------------------- the run folder


def pushed_commit(hdir: Path) -> str | None:
    commit = None
    path = hdir / "lab-events.jsonl"
    for line in path.read_text().splitlines() if path.exists() else []:
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("event") == "push" and ev.get("commit"):
            commit = ev["commit"]
    return commit


def pr_info(gh: str, repo: str, number: int | None) -> dict | None:
    if not number:
        return None
    info: dict = {"number": number}
    r = run_cmd([gh, "pr", "view", str(number), "--repo", repo, "--json", "title,body,url,state"], timeout=60)
    if r["code"] == 0:
        try:
            info.update(json.loads(r["out"]))
        except json.JSONDecodeError:
            info["view_error"] = tail(r["out"], 300)
    else:
        info["view_error"] = tail(r["err"] or r["out"], 300)
    r = run_cmd(
        [gh, "pr", "checks", str(number), "--repo", repo, "--json", "name,state,bucket,workflow,link"], timeout=60
    )
    checks = None
    try:
        checks = json.loads(r["out"]) if r["out"].strip().startswith("[") else None
    except json.JSONDecodeError:
        checks = None
    if checks is None and r["out"].strip():
        checks = []
        for line in r["out"].strip().splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                checks.append({"name": parts[0], "state": parts[1], "bucket": parts[1]})
    info["checks"] = checks
    if checks is None:
        info["checks_error"] = tail(r["err"] or r["out"], 300) or f"exit {r['code']}"
    buckets = [str(c.get("bucket") or c.get("state") or "").lower() for c in checks or []]
    info["checks_summary"] = (
        None
        if not checks
        else "fail"
        if any(b in ("fail", "failure", "cancel") for b in buckets)
        else "pending"
        if any(b in ("pending", "queued", "in_progress") for b in buckets)
        else "pass"
    )
    return info


def pr_from_transcript(folder: Path, hdir: Path) -> dict:
    """Fallback for the PR title and body: the last `lab pr open|update` call and its body file."""
    from grader.common import content_blocks, transcript_records

    found: dict = {}
    for rec in transcript_records(hdir):
        if rec.get("type") != "assistant":
            continue
        for block in content_blocks(rec):
            if block.get("type") == "tool_use" and block.get("name") == "Bash":
                cmd = str((block.get("input") or {}).get("command", ""))
                if re.match(r"\s*(\S*/)?lab\s+pr\s+(open|update)\b", cmd):
                    try:
                        argv = shlex.split(cmd)
                    except ValueError:
                        continue
                    for flag, keyname in (("--title", "title"), ("--body-file", "body_file")):
                        if flag in argv and argv.index(flag) + 1 < len(argv):
                            found[keyname] = argv[argv.index(flag) + 1]
    body_file = found.pop("body_file", None)
    if body_file:
        for b in (folder / "repo", folder):
            p = Path(os.path.realpath(b / os.path.expanduser(body_file)))
            if str(p).startswith(str(folder) + "/") and p.is_file():
                found["body"] = p.read_text(encoding="utf-8", errors="replace")[:20000]
                found["body_source"] = str(p.relative_to(folder))
                break
    return found


def diff_text(repo: Path, base: str, head: str, limit: int = 200_000) -> str:
    """The run's diff, lock files summarised, capped at `limit` characters."""
    parts = []
    for status, path in changed_files(repo, base, head):
        if path.rsplit("/", 1)[-1] in LOCK_FILES:
            n = git(repo, "diff", "--numstat", base, head, "--", path).split("\t")[:2]
            parts.append(
                f"diff --git a/{path} b/{path}\n(lock file {status}: +{n[0] if n else '?'} -{n[1] if len(n) > 1 else '?'} lines, not shown)\n"
            )
        else:
            parts.append(git(repo, "diff", "--no-renames", base, head, "--", path))
    text = "".join(parts)
    if len(text) > limit:
        text = text[:limit] + f"\n[diff truncated: {len(text) - limit} more characters]\n"
    return text


REVIEW_PLACES = ("scratch", "repo/scratch")


def find_review_report(folder: Path) -> dict:
    """Where the run's review.md is: the two expected places first, then a search of both, newest first."""
    folder = Path(folder)

    def inside(p: Path) -> bool:
        real = Path(os.path.realpath(p))
        return real.is_file() and str(real).startswith(str(Path(os.path.realpath(folder))) + "/")

    for place in REVIEW_PLACES:
        p = folder / place / "review.md"
        if inside(p):
            return {"review_report": str(p), "review_report_found_by": f"{place}/review.md"}
    found = [p for place in REVIEW_PLACES if (folder / place).is_dir() for p in (folder / place).rglob("review.md")]
    found = sorted((p for p in found if inside(p)), key=lambda p: p.stat().st_mtime, reverse=True)
    if found:
        return {
            "review_report": str(found[0]),
            "review_report_found_by": "search (newest)",
            "review_report_candidates": [str(p.relative_to(folder)) for p in found],
        }
    return {"review_report": None, "review_report_found_by": None, "review_report_missing": True}


def grade_run(folder: Path, gh: str = "gh", keep: bool = False, tickets_root=None, answers_root=None) -> dict:
    info = run_folder_info(folder)
    folder, hdir, run = info["folder"], info["hdir"], info["run"]
    t = resolve_ticket(run, tickets_root, answers_root)
    cfg = t["config"]
    if cfg is None:
        raise SystemExit(f"no codebase config for repo {run.get('repo')!r}; add one under grader/codebases/")
    repo = folder / "repo"
    deliverable = t["meta"].get("deliverable", "pull_request")
    report: dict = {
        "run_id": run["run_id"],
        "graded_at": now_iso(),
        "grader": {"lab_commit": git_head(LAB_ROOT), "config": cfg["name"]},
        "codebase": t["codebase"],
        "ticket": t["ticket"],
        "spec": t["spec"],
        "deliverable": deliverable,
        "status": run.get("status"),
        "answers_found": t["answers"].is_dir(),
        "key_found": bool(t["key"]),
        "meta_found": bool(t["meta"]),
    }
    report["pull_request"] = pr_info(gh, run.get("repo", ""), run.get("pr_number"))
    if report["pull_request"] is None or report["pull_request"].get("view_error"):
        fallback = pr_from_transcript(folder, hdir)
        if fallback:
            report["pull_request_from_transcript"] = fallback

    if deliverable == "review_report":
        report.update(find_review_report(folder))
        rp = report["review_report"]
        report["review_report_words"] = len(Path(rp).read_text(errors="replace").split()) if rp else 0
        report["script_pass"] = None
        if not repo.is_dir():
            report["files_changed"] = None
            return report

    if not repo.is_dir():
        report["error"] = "the run's repo/ folder is gone (sandbox torn down); nothing to grade"
        report["script_pass"] = False
        return report

    branch = run.get("branch") or f"{run['run_id']}/work"
    tip = git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}^{{commit}}", check=False).strip()
    pushed = pushed_commit(hdir)
    pushed_ok = bool(pushed) and (
        subprocess.run(
            ["git", "-C", str(repo), "cat-file", "-e", f"{pushed}^{{commit}}"], capture_output=True
        ).returncode
        == 0
    )
    if pushed_ok:
        head, source_of_head = pushed, "last push"
    else:
        head, source_of_head = tip, "branch tip"
    report["graded_commit"] = head
    report["graded_from"] = source_of_head
    report["branch_tip"] = tip
    report["branch_tip_differs_from_push"] = bool(pushed and tip and pushed != tip)
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True,
        text=True,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    ).stdout
    report["uncommitted_changes"] = [line for line in status.splitlines() if line.strip()][:50]
    base = run.get("practice_base_commit")
    if not base or not head:
        report["error"] = "run.json has no base commit, or the run's branch is missing"
        report["script_pass"] = False
        return report

    if deliverable == "review_report":
        report["files_changed"] = [f"{s} {p}" for s, p in changed_files(repo, base, head)]
        return report

    graded = grade_commit(cfg, repo, base, head, t["answers"], t["key"], t["spec"], keep=keep, label=run["run_id"])
    report.update({k: v for k, v in graded.items() if k not in ("base_commit", "head_commit")})
    report["base_commit"] = graded.get("base_commit", base)
    if "error" not in graded:
        (hdir / "grade.diff").write_text(diff_text(repo, base, head), encoding="utf-8")
        report["diff_file"] = "grade.diff"
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m grader.grade", description=__doc__.split("\n\n")[0])
    ap.add_argument("run_folder")
    ap.add_argument("--keep", action="store_true", help="keep the temporary clone and print where it is")
    ap.add_argument("--gh", default=os.environ.get("GRADER_GH") or shutil.which("gh") or "gh")
    ap.add_argument("--tickets-root", help="default tickets/ in this repo")
    ap.add_argument("--answers-root", help="default answers/ in this repo")
    a = ap.parse_args(argv)
    try:
        report = grade_run(Path(a.run_folder), a.gh, a.keep, a.tickets_root, a.answers_root)
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 2
    out = Path(a.run_folder).resolve() / "harness" / "grade.json"
    write_json(out, report)
    hidden = report.get("hidden_tests") or {}
    print(
        f"{report['run_id']}: script_pass={report.get('script_pass')} hidden {hidden.get('passed', '-')} passed "
        f"{hidden.get('failed', '-')} failed; traps tripped {report.get('traps_tripped', [])}"
        + (f"; error: {report['error']}" if report.get("error") else "")
        + f"; wrote {out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["grade_commit", "grade_run", "read_json"]
