"""A tiny practice codebase, ticket package and answer package for the grader's tests.

The codebase has a paging bug, a migration, a scope-out module and two existing tests. It needs only
this Python and pytest, so the grader's tests run in CI without uv, Postgres or the network.
"""

import json
import subprocess
from pathlib import Path

G = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false"]

BUGGY = '''def page(items, number, size):
    """Page `number` (from 1) of `items`, `size` per page."""
    if number < 1 or size < 1:
        raise ValueError("bad page")
    start = (number - 1) * size
    first = max(start - 1, 0)
    return items[first : first + size]
'''
FIXED = BUGGY.replace("    first = max(start - 1, 0)\n", "    first = start\n")
OTHER = "def helper():\n    return 1\n"
MIGRATE = """import os
import sqlite3
from pathlib import Path

conn = sqlite3.connect(os.environ["LAB_DB"])
conn.execute("create table if not exists done (name text primary key)")
done = {r[0] for r in conn.execute("select name from done")}
applied = []
for f in sorted(Path("migrations").glob("*.sql")):
    if f.name not in done:
        conn.executescript(f.read_text())
        conn.execute("insert into done values (?)", (f.name,))
        applied.append(f.name)
conn.commit()
print("\\n".join(f"applied {a}" for a in applied) or "nothing to apply")
"""
TESTS = """import pytest

from app.pages import page


def test_first_page():
    assert page(list(range(10)), 1, 3) == [0, 1, 2]


def test_bad_page():
    with pytest.raises(ValueError):
        page([], 0, 1)
"""
NEW_TEST = """

def test_second_page():
    assert page(list(range(7)), 2, 3) == [3, 4, 5]
"""
WEAK_TEST = """

def test_page_returns_a_list():
    assert isinstance(page(list(range(7)), 2, 3), list)
"""
HIDDEN = """from app.pages import page


def test_hidden_pages_are_disjoint():
    items = list(range(7))
    assert [page(items, n, 3) for n in (1, 2, 3, 4)] == [[0, 1, 2], [3, 4, 5], [6], []]
"""
ACCEPTANCE = """from app.pages import page


def test_acceptance_page_two():
    assert page(list(range(7)), 2, 3) == [3, 4, 5]
"""


def sh(*args, cwd=None) -> str:
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def write(root: Path, files: dict) -> None:
    for rel, content in files.items():
        p = root / rel
        if content is None:
            p.unlink(missing_ok=True)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)


def commit(repo: Path, base: str, files: dict, msg: str = "change", branch: str | None = None) -> str:
    """Commit `files` (path -> text, None deletes) on top of `base`; returns the new commit."""
    sh("git", "checkout", "-q", "--detach", base, cwd=repo)
    write(repo, files)
    sh(*G, "add", "-A", cwd=repo)
    sh(*G, "commit", "-q", "--allow-empty", "-m", msg, cwd=repo)
    sha = sh("git", "rev-parse", "HEAD", cwd=repo)
    if branch:
        sh("git", "branch", "-f", branch, sha, cwd=repo)
    sh("git", "checkout", "-q", "--detach", base, cwd=repo)
    return sha


def make_practice(tmp: Path) -> dict:
    """Practice repo (base and S3 base), codebase config, ticket and answer packages under tmp."""
    repo = tmp / "practice"
    repo.mkdir()
    sh("git", "init", "-q", "-b", "main", cwd=repo)
    write(
        repo,
        {
            "app/__init__.py": "",
            "app/pages.py": BUGGY,
            "app/other.py": OTHER,
            "migrations/0001_init.sql": "create table if not exists t (id integer);\n",
            "migrate.py": MIGRATE,
            "tests/test_pages.py": TESTS,
            "pytest.ini": "[pytest]\npythonpath = .\n",
        },
    )
    sh(*G, "add", "-A", cwd=repo)
    sh(*G, "commit", "-qm", "base", cwd=repo)
    base = sh("git", "rev-parse", "HEAD", cwd=repo)
    s3 = commit(repo, base, {"tests/test_acceptance.py": ACCEPTANCE}, "acceptance tests", branch="base/T1-s3")
    sh("git", "branch", "-f", "base/T1", base, cwd=repo)

    codebases = tmp / "codebases"
    codebases.mkdir()
    cfg = {
        "name": "tiny",
        "repo": "example/tiny",
        "local_clone": str(repo),
        "db": "sqlite",
        "env": {"LAB_DB": "{db_path}"},
        "install": None,
        "lint": [["{python}", "-m", "py_compile", "app/pages.py"]],
        "migrate": {"cmd": ["{python}", "migrate.py"], "second_run_must_match": "nothing to apply"},
        "migrations_dir": "migrations",
        "test": ["{python}", "-m", "pytest", "-q"],
        "test_dirs": ["tests"],
        "hidden_dir": "tests/hidden",
        "hidden_test_cmd": "{python} -m pytest -q tests/hidden",
        "timeout_seconds": 120,
    }
    (codebases / "tiny.json").write_text(json.dumps(cfg))

    tickets = tmp / "tickets"
    pkg = tickets / "tiny" / "T1"
    pkg.mkdir(parents=True)
    for level in ("S0", "S1", "S2", "S3"):
        (pkg / f"{level}.md").write_text(
            f"# Paging repeats a row ({level})\n\nPage 2 repeats the last item of page 1.\n"
        )
    meta = {
        "id": "T1",
        "kind": "replay",
        "title": "Paging repeats a row",
        "repo": "example/tiny",
        "base_ref": "base/T1",
        "s3_base_ref": "base/T1-s3",
        "db": "sqlite",
        "deliverable": "pull_request",
        "spec_words": {"S0": 10, "S1": 100, "S2": 200, "S3": 300},
    }
    (pkg / "meta.json").write_text(json.dumps(meta))

    answers = tmp / "answers"
    ans = answers / "tiny" / "T1"
    (ans / "hidden").mkdir(parents=True)
    (ans / "hidden" / "test_hidden_t1.py").write_text(HIDDEN)
    fix = commit(repo, base, {"app/pages.py": FIXED, "tests/test_pages.py": TESTS + NEW_TEST}, "reference")
    (ans / "reference.patch").write_text(sh("git", "diff", base, fix, cwd=repo) + "\n")
    key = {
        "hidden_test_cmd": "{python} -m pytest -q tests/hidden",
        "unchanged_paths": ["migrations/0001_init.sql"],
        "scope_out_paths": ["app/other.py"],
        "traps": [{"id": "helper-unchanged", "check": "ast_unchanged", "path": "app/other.py", "symbol": "helper"}],
    }
    (ans / "key.json").write_text(json.dumps(key))
    (ans / "replies.md").write_text("## T1-scope\nWhen: asks to change other.py.\nReply: Leave other.py alone.\n")
    return {
        "repo": repo,
        "base": base,
        "s3": s3,
        "codebases": codebases,
        "cfg": cfg,
        "tickets": tickets,
        "answers": answers,
        "key": key,
        "ans": ans,
    }


def make_run_folder(
    tmp: Path, p: dict, run_id: str, head: str, base: str | None = None, spec: str = "S1", **run
) -> Path:
    """A finished run's folder as the harness leaves it: repo/ on <run-id>/work, records in harness/."""
    folder = tmp / "runs" / "test" / run_id
    hdir = folder / "harness"
    hdir.mkdir(parents=True)
    sh("git", "clone", "-q", str(p["repo"]), str(folder / "repo"))
    branch = f"{run_id}/work"
    sh("git", "checkout", "-q", "-b", branch, head, cwd=folder / "repo")
    (folder / "scratch").mkdir()
    rec = {
        "run_id": run_id,
        "stage": "test",
        "arm": "bare",
        "ticket": str(p["tickets"] / "tiny" / "T1" / f"{spec}.md"),
        "repo": "example/tiny",
        "base_ref": "base/T1",
        "practice_base_commit": base or p["base"],
        "branch": branch,
        "model": "claude-opus-5-5",
        "status": "finished",
        "reason": "ended without STOP",
        "tokens": {"input": 1000, "output": 2000, "cache_write": 3000, "cache_read": 10000, "counted": 6000},
        "judge_tokens": {"counted": 0},
        "cost_usd": 0.12,
        "wall_seconds": 61.5,
        "pr_number": 7,
        "reply_sheet": "",
    }
    rec.update(run)
    (hdir / "run.json").write_text(json.dumps(rec))
    (hdir / "lab-events.jsonl").write_text(json.dumps({"event": "push", "branch": branch, "commit": head}) + "\n")
    transcript = [
        {"type": "system", "subtype": "init", "session_id": "s"},
        {
            "type": "assistant",
            "message": {
                "id": "m1",
                "content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "pytest -q"}}],
            },
        },
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": "3 passed"}]}},
        {"type": "result", "result": f"Opened the pull request for {run_id}. All tests pass.", "is_error": False},
    ]
    (hdir / "transcript.jsonl").write_text("\n".join(json.dumps(r) for r in transcript) + "\n")
    (hdir / "scan.json").write_text(json.dumps({"clean": True, "offences": [], "tool_calls": 1}))
    return folder


def tree_snapshot(root: Path, skip=()) -> dict:
    """path -> (size, mtime_ns) for every file under root, to prove a folder was not changed."""
    out = {}
    for p in sorted(root.rglob("*")):
        rel = str(p.relative_to(root))
        if p.is_file() and not any(rel.startswith(s) for s in skip):
            st = p.stat()
            out[rel] = (st.st_size, st.st_mtime_ns)
    return out


__all__ = ["FIXED", "NEW_TEST", "WEAK_TEST", "TESTS", "commit", "make_practice", "make_run_folder", "tree_snapshot"]
