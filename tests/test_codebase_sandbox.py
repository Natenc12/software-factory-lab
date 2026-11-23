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


def test_setup_runs_once_in_the_checkout_before_the_session(lab_env, practice):
    from harness import run
    from tests.conftest import calls, run_args

    scenario(lab_env, p0_t1_1=["limit", "finish"])
    setup = ["echo $LAB_DB > {run}/scratch/setup-saw.txt && pwd >> {run}/scratch/setup-saw.txt", "touch node_modules"]
    args = run_args(lab_env, practice, "p0-t1-1", *[x for s in setup for x in ("--setup", s)])
    assert run.main(args) == 75  # plan limit after setup
    root = lab_env["runs"] / "test" / "p0-t1-1"
    saw = (root / "scratch" / "setup-saw.txt").read_text().split()
    assert saw == [str(root / "db" / "lab.db"), str(root / "repo")]
    rec = read_json(root / "harness" / "run.json")
    assert [s["exit"] for s in rec["setup"]] == [0, 0] and str(root) in rec["setup"][0]["cmd"]
    assert "$ touch node_modules" in (root / "harness" / "setup.log").read_text()
    assert run.main(args) == 0  # resumed: setup is not run again
    assert (root / "harness" / "setup.log").read_text().count("$ touch node_modules") == 1
    assert len([c for c in calls(lab_env) if "stream-json" in c["argv"]]) == 2


def test_failed_setup_is_a_harness_fault_and_no_session_starts(lab_env, practice):
    from harness import run
    from tests.conftest import calls, run_args

    scenario(lab_env, p0_t1_1=["finish"])
    assert run.main(run_args(lab_env, practice, "p0-t1-1", "--setup", "exit 3")) == 1
    rec = read_json(lab_env["runs"] / "test" / "p0-t1-1" / "harness" / "run.json")
    assert rec["status"] == "harness_fault" and "setup command failed (3)" in rec["reason"]
    assert calls(lab_env) == []


def test_runs_without_setup_have_no_setup_record(lab_env, practice):
    from harness import run
    from tests.conftest import run_args

    scenario(lab_env, p0_t1_1=["finish"])
    assert run.main(run_args(lab_env, practice, "p0-t1-1")) == 0
    root = lab_env["runs"] / "test" / "p0-t1-1"
    assert "setup" not in read_json(root / "harness" / "run.json") and not (root / "harness" / "setup.log").exists()


def test_a_plan_sets_the_model_and_setup_per_run(lab_env, practice, tmp_path):
    from tests.conftest import calls

    scenario(lab_env, p5p_t1_1=["finish"], p5p_t1_2=["finish"])
    plan_path = write_plan(lab_env, practice, tmp_path, 10_000_000, ["p5p-t1-1", "p5p-t1-2"])
    plan = json.loads(open(plan_path).read())
    plan["runs"][0]["model"] = "claude-opus-5-5"
    plan["runs"][1].update(model="claude-fable-5-2", setup=["touch {run}/scratch/ready"])
    open(plan_path, "w").write(json.dumps(plan))
    assert stage.main([plan_path, "--poll-seconds", "0.2"]) == 0
    models = {c["cwd"].split("/")[-2]: c["argv"][c["argv"].index("--model") + 1] for c in calls(lab_env)}
    assert models == {"p5p-t1-1": "claude-opus-5-5", "p5p-t1-2": "claude-fable-5-2"}
    for rid, model in models.items():
        assert read_json(lab_env["runs"] / "test" / rid / "harness" / "run.json")["model"] == model
    assert (lab_env["runs"] / "test" / "p5p-t1-2" / "scratch" / "ready").exists()
    assert not (lab_env["runs"] / "test" / "p5p-t1-1" / "scratch" / "ready").exists()


def test_codebase_setup_becomes_a_plan_key(monkeypatch):
    monkeypatch.setattr(make_plan, "load_config", lambda name: {"run_setup": ["pnpm install --frozen-lockfile"]})
    assert make_plan.codebase_run_extras("hono") == {"setup": ["pnpm install --frozen-lockfile"]}
