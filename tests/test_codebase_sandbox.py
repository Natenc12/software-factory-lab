"""A codebase's config can widen its runs' sandbox: extra hosts and toolchain cache folders, end to end."""

import json
import os

import pytest

from grader import make_plan
from harness import sandbox, stage
from harness.common import read_json
from tests.conftest import scenario
from tests.test_run import write_plan


def test_codebase_config_becomes_run_plan_keys(monkeypatch):
    cfg = {
        "name": "rusty",
        "run_env": {"CARGO_TERM_COLOR": "never"},
        "run_allow_domains": ["crates.io", "static.crates.io", "index.crates.io"],
        "run_allow_write": ["~/.cargo/registry"],
    }
    monkeypatch.setattr(make_plan, "load_config", lambda name: cfg)
    assert make_plan.codebase_run_extras("rusty") == {
        "env": ["CARGO_TERM_COLOR=never"],
        "allow_domain": ["crates.io", "static.crates.io", "index.crates.io"],
        "allow_write": ["~/.cargo/registry"],
    }
    # Today's codebases: gct adds only its env, as before; pipeline-lab adds nothing.
    monkeypatch.undo()
    assert make_plan.codebase_run_extras("gct") == {"env": ["UV_PYTHON=3.10"]}
    assert make_plan.codebase_run_extras("pipeline-lab") == {}


def test_plan_domains_and_write_folders_reach_the_run_sandbox(lab_env, practice, tmp_path):
    scenario(lab_env, p0_t1_1=["finish"])
    plan_path = write_plan(lab_env, practice, tmp_path, 10_000_000, ["p0-t1-1"])
    plan = json.loads(open(plan_path).read())
    cache = tmp_path / "toolchain-cache"
    plan["runs"][0].update(
        allow_domain=["proxy.golang.org", "sum.golang.org"],
        allow_write=[str(cache)],
        env=["GOMODCACHE={run}/scratch/gomod"],
    )
    open(plan_path, "w").write(json.dumps(plan))
    assert stage.main([plan_path, "--poll-seconds", "0.2"]) == 0
    root = lab_env["runs"] / "test" / "p0-t1-1"
    s = json.loads((sandbox.control_dir(root) / "settings.json").read_text())
    net = s["sandbox"]["network"]["allowedDomains"]
    assert net == ["pypi.org", "files.pythonhosted.org", "proxy.golang.org", "sum.golang.org"]
    assert os.path.realpath(cache) in s["sandbox"]["filesystem"]["allowWrite"]
    assert read_json(root / "harness" / "sandbox.json")["env"]["GOMODCACHE"] == f"{root}/scratch/gomod"
    guard_cfg = read_json(root / "harness" / "guard.json")
    assert os.path.realpath(cache) in guard_cfg["read_ok"]


@pytest.mark.parametrize("bad", ["~", "/", "~/.claude", "~/repos", "~/.config"])
def test_write_folders_cannot_open_forbidden_places(tmp_path, bad):
    root = tmp_path / "runs" / "s" / "p0-t1-1"
    cfg = sandbox.guard_config(root, tmp_path / "runs", [])
    with pytest.raises(RuntimeError):
        sandbox.writable_folders([bad], cfg)
    assert sandbox.writable_folders(["~/.cargo/registry"], cfg) == [
        os.path.realpath(os.path.expanduser("~/.cargo/registry"))
    ]
