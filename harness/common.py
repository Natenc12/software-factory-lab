"""Small helpers shared by the harness modules: run ids, paths, JSON files, git commits."""

import json
import os
import re
import subprocess
import time
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[1]
RUN_ID_RE = re.compile(r"^(?P<arm>[a-z0-9]+)-(?P<ticket>[a-z0-9]+)-(?P<repeat>[0-9]+)$")
STAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
FINAL = ("finished", "ceiling_hit")
STATUSES = ("running", "finished", "ceiling_hit", "harness_fault", "plan_limit")


def parse_run_id(run_id: str) -> dict:
    """`p3-t4-1` -> {"arm": "p3", "ticket": "t4", "repeat": "1"}. Raises ValueError if malformed."""
    m = RUN_ID_RE.match(run_id or "")
    if not m:
        raise ValueError(f"bad run id {run_id!r}: expected <arm>-<ticket>-<repeat>, e.g. p3-t4-1")
    return m.groupdict()


def check_stage(stage: str) -> str:
    if not STAGE_RE.match(stage or ""):
        raise ValueError(f"bad stage name {stage!r}: letters, digits, '-' and '_' only")
    return stage


def runs_root(override: str | None = None) -> Path:
    raw = override or os.environ.get("FACTORY_RUNS_ROOT") or "~/factory-runs"
    return Path(os.path.realpath(os.path.expanduser(raw)))


def run_dir(stage: str, run_id: str, root: str | None = None) -> Path:
    return runs_root(root) / check_stage(stage) / run_id


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_json(path: Path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path: Path, data) -> None:
    """Write atomically, so a reader never sees half a file."""
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def append_jsonl(path: Path, record: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def git(*args: str, cwd: Path | str | None = None, check: bool = True) -> str:
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if check and out.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {out.stderr.strip()}")
    return out.stdout.strip()


def git_head(path: Path | str) -> str | None:
    out = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return out.stdout.strip() or None


def lab_commit() -> dict:
    """The commit of this repo that ran the harness, and whether the checkout had local changes."""
    dirty = subprocess.run(
        ["git", "-C", str(LAB_ROOT), "status", "--porcelain", "--", "harness"], capture_output=True, text=True
    ).stdout.strip()
    return {"commit": git_head(LAB_ROOT), "harness_dirty": bool(dirty)}
