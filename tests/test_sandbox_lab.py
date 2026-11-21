"""Sandboxes hold only the base history and never touch each other; `lab` is the only way to GitHub."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from harness import sandbox
from harness.common import read_json
from tests.conftest import sh


def make(env, practice, run_id, **kw):
    root = env["runs"] / "test" / run_id
    args = dict(
        repo="example/lab",
        repo_url=practice["url"],
        base="main",
        pr_base="main",
        ticket=env["ticket"],
        arm=None,
        db="sqlite",
        runs_root=env["runs"],
        gh_bin=env["gh"],
    )
    args.update(kw)
    return root, sandbox.create(root, run_id, **args)


def test_sandbox_holds_only_the_base_history(lab_env, practice):
    root, manifest = make(lab_env, practice, "p1-t1-1")
    repo = root / "repo"
    assert manifest["base_commit"] == practice["main"]
    assert sh("git", "branch", "--show-current", cwd=repo) == "p1-t1-1/work"
    assert set(sh("git", "branch", "--format=%(refname:short)", cwd=repo).split()) == {"main", "p1-t1-1/work"}
    assert sh("git", "remote", cwd=repo) == ""
    seen = subprocess.run(["git", "cat-file", "-e", practice["other"]], cwd=repo, capture_output=True)
    assert seen.returncode != 0, "another run's commit leaked into the sandbox"
    for name in ("scratch", "TICKET.md", "db", "harness/settings.json", "harness/guard.py", "harness/bin/lab"):
        assert (root / name).exists(), name
    assert manifest["env"]["LAB_DB"] == str(root / "db" / "lab.db")
    settings = json.loads((root / "harness" / "settings.json").read_text())
    assert "WebFetch" in settings["permissions"]["deny"]
    assert "guard.py" in settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    assert settings["autoMemoryEnabled"] is False


def test_arm_folder_file_and_team_agents(lab_env, practice, tmp_path):
    arm = tmp_path / "P4"
    (arm / "agents").mkdir(parents=True)
    (arm / "ARM.md").write_text("Lead the team.")
    (arm / "README.md").write_text("not an instruction")
    (arm / "agents" / "tester.md").write_text(
        "---\nname: tester\ndescription: Writes tests from the contract\ntools: Read, Write, Bash\nmodel: sonnet\n---\nWrite tests only."
    )
    root, _ = make(lab_env, practice, "p4-t1-1", arm=arm)
    assert "Lead the team." in (root / "harness" / "arm-prompt.md").read_text()
    assert "not an instruction" not in (root / "harness" / "arm-prompt.md").read_text()
    agents = json.loads((root / "harness" / "agents.json").read_text())
    assert agents["tester"] == {
        "description": "Writes tests from the contract",
        "prompt": "Write tests only.",
        "tools": ["Read", "Write", "Bash"],
        "model": "sonnet",
    }
    single = tmp_path / "SKILL.md"
    single.write_text("Contract first.")
    root2, _ = make(lab_env, practice, "p3-t1-1", arm=single)
    assert (root2 / "arm" / "SKILL.md").exists()
    assert not (root2 / "harness" / "agents.json").exists()


def test_teardown_removes_only_this_run(lab_env, practice):
    a, _ = make(lab_env, practice, "p1-t1-1")
    b, _ = make(lab_env, practice, "p1-t1-2")
    with pytest.raises(RuntimeError):
        make(lab_env, practice, "p1-t1-1")
    sandbox.teardown(a)
    assert not (a / "repo").exists() and (a / "harness" / "sandbox.json").exists()
    assert (b / "repo" / "app.py").exists()
    sandbox.teardown(a, everything=True)
    assert not a.exists() and b.exists()
    stray = lab_env["runs"] / "test" / "p1-t1-3"
    stray.mkdir()
    with pytest.raises(RuntimeError):
        sandbox.teardown(stray)
    assert stray.exists()
    # A manifest copied from another run does not authorise removing this folder.
    (stray / "harness").mkdir()
    shutil.copy(b / "harness" / "sandbox.json", stray / "harness" / "sandbox.json")
    with pytest.raises(RuntimeError):
        sandbox.teardown(stray)
    assert (b / "repo").exists()


def test_failed_setup_cleans_up(lab_env, practice):
    root = lab_env["runs"] / "test" / "p1-t1-1"
    with pytest.raises(RuntimeError):
        make(lab_env, practice, "p1-t1-1", base="no-such-branch")
    assert not root.exists()


def _pg_ready() -> bool:
    if not shutil.which("psql"):
        return False
    out = subprocess.run(["psql", "-X", "-d", "postgres", "-tAc", "select 1"], capture_output=True, text=True)
    return out.returncode == 0


@pytest.mark.skipif(not _pg_ready(), reason="no local Postgres")
def test_postgres_database_per_run(lab_env, practice):
    rid = "zz-t0-99"
    name = sandbox.pg_name(rid)
    subprocess.run(["psql", "-X", "-d", "postgres", "-qc", f'DROP DATABASE IF EXISTS "{name}"'], capture_output=True)
    root, manifest = make(lab_env, practice, rid, db="postgres")
    try:
        assert manifest["database"]["name"] == name and manifest["env"]["DATABASE_URL"].endswith("/" + name)
        ext = sandbox.psql("SELECT extname FROM pg_extension WHERE extname = 'vector'", name)
        assert ext.stdout.strip() == "vector"
        with pytest.raises(RuntimeError):
            sandbox.create_postgres(rid)
    finally:
        sandbox.teardown(root, everything=True)
    gone = sandbox.psql(f"SELECT 1 FROM pg_database WHERE datname = '{name}'")
    assert gone.stdout.strip() == ""


def lab(root: Path, *args):
    env = {**os.environ, "PATH": f"{root / 'harness' / 'bin'}:{os.environ['PATH']}"}
    return subprocess.run(["lab", *args], cwd=root / "repo", env=env, capture_output=True, text=True)


def test_lab_commands(lab_env, practice):
    root, _ = make(lab_env, practice, "p1-t1-1")
    assert lab(root, "ticket").stdout.startswith("# T1")
    g = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
    (root / "repo" / "app.py").write_text("print('fixed')\n")
    sh(*g, "commit", "-qam", "fix", cwd=root / "repo")
    (root / "scratch" / "body.md").write_text("Fixes T1.")
    assert lab(root, "pr", "checks").returncode != 0  # no PR yet
    assert lab(root, "pr", "update").returncode != 0
    outside = root.parent / "body.md"
    outside.write_text("x")
    assert "inside your run folder" in lab(root, "pr", "open", "--title", "Fix", "--body-file", str(outside)).stderr
    out = lab(root, "pr", "open", "--title", "Fix paging", "--body-file", "../scratch/body.md")
    assert out.returncode == 0, out.stderr
    pushed = sh("git", "--git-dir", practice["url"], "rev-parse", "p1-t1-1/work")
    assert pushed == sh("git", "rev-parse", "HEAD", cwd=root / "repo")
    assert lab(root, "pr", "open", "--title", "Again", "--body-file", "../scratch/body.md").returncode != 0
    assert lab(root, "pr", "update", "--title", "Fix paging (v2)").returncode == 0
    checks = lab(root, "pr", "checks")
    assert checks.returncode == 0 and "pass" in checks.stdout
    gh_calls = [json.loads(line) for line in lab_env["gh_log"].read_text().splitlines()]
    verbs = {tuple(c[:2]) for c in gh_calls}
    assert verbs <= {("pr", "list"), ("pr", "create"), ("pr", "edit"), ("pr", "checks")}
    assert all("--repo" in c and c[c.index("--repo") + 1] == "example/lab" for c in gh_calls)
    flat = " ".join(" ".join(c) for c in gh_calls)
    assert "merge" not in flat and "label" not in flat and "comment" not in flat
    events = [json.loads(line) for line in (root / "harness" / "lab-events.jsonl").read_text().splitlines()]
    assert [e["event"] for e in events] == ["push", "pr_open", "push", "pr_update"]
    assert events[1]["pr"] == 7
    # Main on the remote is untouched; only the run's own branch moved.
    assert sh("git", "--git-dir", practice["url"], "rev-parse", "main") == practice["main"]


def test_lab_cannot_call_other_gh_verbs(lab_env, practice):
    root, _ = make(lab_env, practice, "p1-t1-1")
    lab_script = str(root / "harness" / "bin" / "lab")
    code = f"import runpy; m = runpy.run_path({lab_script!r}); m['gh'](m['load_config'](), 'pr', 'merge', '7')"
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode != 0 and "refusing gh pr merge" in (out.stderr + out.stdout)
    assert read_json(root / "harness" / "sandbox.json")["run_id"] == "p1-t1-1"
