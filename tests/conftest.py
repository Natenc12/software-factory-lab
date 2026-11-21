"""Shared fixtures: a throwaway practice repo, fake `claude` and `gh`, and a private runs root."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

FAKES = Path(__file__).parent / "fakes"
# Fixture packages hold other repos' tests (hidden tests, practice code); never collect them here.
collect_ignore_glob = ["fixtures/*"]
ROOT = Path(__file__).resolve().parents[1]


def sh(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def wrapper(path: Path, script: Path) -> str:
    path.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n')
    path.chmod(0o755)
    return str(path)


@pytest.fixture
def practice(tmp_path):
    """A bare repo with `main` (2 commits) and another run's branch that no sandbox may see."""
    work = tmp_path / "src"
    work.mkdir()
    g = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
    sh("git", "init", "-q", "-b", "main", cwd=work)
    (work / "app.py").write_text("print('v1')\n")
    sh(*g, "add", ".", cwd=work)
    sh(*g, "commit", "-qm", "v1", cwd=work)
    (work / "app.py").write_text("print('v2')\n")
    sh(*g, "commit", "-qam", "v2", cwd=work)
    sh("git", "checkout", "-qb", "p9-t9-9/work", cwd=work)
    (work / "other.py").write_text("secret = 1\n")
    sh(*g, "add", ".", cwd=work)
    sh(*g, "commit", "-qm", "another run's work", cwd=work)
    sh("git", "checkout", "-q", "main", cwd=work)
    bare = tmp_path / "practice.git"
    sh("git", "clone", "-q", "--bare", str(work), str(bare))
    return {
        "url": str(bare),
        "main": sh("git", "rev-parse", "main", cwd=work),
        "other": sh("git", "rev-parse", "p9-t9-9/work", cwd=work),
    }


@pytest.fixture
def lab_env(tmp_path, monkeypatch):
    """Fake binaries, a runs root, a ticket and a scenario file; env set for the harness and its children."""
    bins = tmp_path / "bin"
    bins.mkdir()
    state = tmp_path / "state"
    state.mkdir()
    env = {
        "claude": wrapper(bins / "claude", FAKES / "fake_claude.py"),
        "gh": wrapper(bins / "gh", FAKES / "fake_gh.py"),
        "runs": tmp_path / "runs",
        "log": tmp_path / "claude-calls.jsonl",
        "gh_log": tmp_path / "gh-calls.jsonl",
        "scenario": tmp_path / "scenario.json",
        "ticket": tmp_path / "TICKET-T1.md",
    }
    env["ticket"].write_text("# T1\nFix the pagination.\n")
    env["scenario"].write_text("{}")
    monkeypatch.setenv("FAKE_LOG", str(env["log"]))
    monkeypatch.setenv("FAKE_GH_LOG", str(env["gh_log"]))
    monkeypatch.setenv("FAKE_STATE", str(state))
    monkeypatch.setenv("FAKE_SCENARIO_FILE", str(env["scenario"]))
    monkeypatch.setenv(
        "HARNESS_PASS_ENV", "FAKE_LOG,FAKE_GH_LOG,FAKE_STATE,FAKE_SCENARIO_FILE,FAKE_JUDGE,FAKE_LEAK_PATH"
    )
    monkeypatch.setenv("FACTORY_RUNS_ROOT", str(env["runs"]))
    monkeypatch.setenv("CLAUDECODE", "1")  # as when the harness itself runs inside a Claude session
    monkeypatch.chdir(ROOT)
    return env


def scenario(env, **runs):
    data = json.loads(env["scenario"].read_text())
    data.update({k.replace("_", "-"): v for k, v in runs.items()})
    env["scenario"].write_text(json.dumps(data))


def calls(env):
    if not env["log"].exists():
        return []
    return [json.loads(line) for line in env["log"].read_text().splitlines()]


def run_args(env, practice, run_id, *extra):
    return [
        run_id,
        "--stage",
        "test",
        "--ticket",
        str(env["ticket"]),
        "--repo",
        "example/lab",
        "--repo-url",
        practice["url"],
        "--base",
        "main",
        "--model",
        "fake-model",
        "--judge-model",
        "fake-judge",
        "--ceiling",
        "400000",
        "--claude-bin",
        env["claude"],
        "--gh-bin",
        env["gh"],
        *extra,
    ]


os.environ.setdefault("GIT_CONFIG_NOSYSTEM", "1")
