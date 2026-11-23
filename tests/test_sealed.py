"""Sealed runs: no package registry, per-run caches, no reads outside the run but its toolchain, and the
codebase's own published package refused. Runs without `sealed` are unchanged (tests/test_skills.py pins)."""

import json
import os
from pathlib import Path

import pytest

from grader import make_plan
from harness import guard, run, sandbox
from harness.common import read_json
from harness.scan import scan
from tests.conftest import calls, run_args, scenario
from tests.test_sandbox_lab import make

HOME = os.path.realpath(os.path.expanduser("~"))


def test_shared_temp_keeps_the_sandbox_temp_and_denies_everything_else(tmp_path):
    tmp = tmp_path / "tmp"
    mine = tmp / f"claude-{os.getuid()}"
    (mine / "-Users-x-other-session" / "scratchpad").mkdir(parents=True)
    (mine / "cwd-1a2b").write_text("")
    (tmp / "someone-else").mkdir()
    (tmp / "loose.txt").write_text("")
    root, denied = sandbox.shared_temp(str(tmp))
    real = Path(os.path.realpath(tmp))
    assert root == str(real / f"claude-{os.getuid()}")
    assert denied == [
        str(real / "loose.txt"),
        str(real / "someone-else"),
        str(real / f"claude-{os.getuid()}" / "-Users-x-other-session"),
    ]


def test_sealed_settings_env_and_guard(lab_env, practice):
    root, manifest = make(
        lab_env, practice, "p5p-t1-1", sealed=True, own_packages=["sqlglot"], allow_domains=["x.example"]
    )
    ctl = sandbox.control_dir(root)
    s = json.loads((ctl / "settings.json").read_text())
    box = s["sandbox"]
    assert box["network"]["allowedDomains"] == ["x.example"], "no package registry by default"
    fs = box["filesystem"]
    assert f"{HOME}/.cache/uv" not in fs["allowWrite"]
    assert HOME in fs["denyRead"] and "/private/var/folders" in fs["denyRead"]
    assert not {"/tmp", "/private/tmp", os.path.realpath("/tmp")} & set(fs["denyRead"]), "the sandbox's own temp stays"
    assert fs["allowRead"][0] == str(root)
    assert f"{HOME}/.local/share/uv/python" in fs["allowRead"]
    assert manifest["env"]["UV_CACHE_DIR"] == f"{root}/scratch/uv-cache"
    assert manifest["env"]["npm_config_cache"] == f"{root}/scratch/npm-cache"
    assert manifest["session_env"]["UV_OFFLINE"] == "1" and "UV_OFFLINE" not in manifest["env"]
    cfg = read_json(ctl / "guard.json")
    assert cfg["own_packages"] == ["sqlglot"] and cfg["write_ok"] == ["/dev/null"]
    assert cfg["own_temp"] == os.path.join(cfg["shared_temp"], sandbox.run_slug(root))


def test_unsealed_runs_keep_the_registry_and_shared_uv_cache(lab_env, practice):
    root, manifest = make(lab_env, practice, "p1-t1-1")
    s = json.loads((sandbox.control_dir(root) / "settings.json").read_text())["sandbox"]
    assert s["network"]["allowedDomains"] == ["pypi.org", "files.pythonhosted.org"]
    assert f"{HOME}/.cache/uv" in s["filesystem"]["allowWrite"] and HOME not in s["filesystem"]["denyRead"]
    assert "session_env" not in manifest and "UV_CACHE_DIR" not in manifest["env"]


def test_the_session_is_offline_but_setup_is_not(lab_env, practice):
    scenario(lab_env, p5p_t1_1=["finish"])
    args = run_args(lab_env, practice, "p5p-t1-1", "--sealed", "--setup", "env > {run}/scratch/setup-env.txt")
    assert run.main(args) == 0
    root = lab_env["runs"] / "test" / "p5p-t1-1"
    setup_env = (root / "scratch" / "setup-env.txt").read_text()
    assert f"UV_CACHE_DIR={root}/scratch/uv-cache" in setup_env and "UV_OFFLINE" not in setup_env
    [session] = [c for c in calls(lab_env) if "stream-json" in c["argv"]]
    assert {"UV_OFFLINE", "PIP_NO_INDEX", "npm_config_offline", "UV_CACHE_DIR"} <= set(session["env"])


@pytest.fixture
def sealed_cfg(tmp_path):
    box = tmp_path / "runs" / "s" / "p5p-t1-1"
    (box / "repo").mkdir(parents=True)
    cfg = sandbox.guard_config(box.resolve(), (tmp_path / "runs").resolve(), [])
    st = os.path.realpath(tmp_path / "shared")
    os.makedirs(f"{st}/-Users-x-other/scratchpad/audit")
    cfg.update(shared_temp=st, own_temp=f"{st}/{sandbox.run_slug(box.resolve())}", own_packages=["hono"], log=None)
    return cfg


def test_guard_refuses_other_sessions_temp_folders(sealed_cfg):
    st = sealed_cfg["shared_temp"]
    cwd = sealed_cfg["sandbox"] + "/repo"
    for cmd in (
        f"ls {st}/-Users-x-other",
        f"cat {st}/-Users-x-other/scratchpad/audit/key.md",
        f"ls {st}/new-session/x",
    ):
        assert guard.SHARED_TEMP_REASON in guard.check("Bash", {"command": cmd}, cwd, sealed_cfg), cmd
    for cmd in (f"cat {st}/cwd-1a2b", f"ls {sealed_cfg['own_temp']}/tasks"):
        assert guard.check("Bash", {"command": cmd}, cwd, sealed_cfg) is None, cmd


@pytest.mark.parametrize(
    "cmd",
    [
        "pnpm add -D hono@latest",
        "npm view hono versions",
        "npx hono@4.13.30",
        "npm install hono",
        "cat /usr/local/lib/node_modules/hono/package.json",
        "ls ~/Library/pnpm/store/v11/links/hono@4.13.9",
    ],
)
def test_own_package_is_refused(sealed_cfg, cmd):
    assert guard.check("Bash", {"command": cmd}, sealed_cfg["sandbox"] + "/repo", sealed_cfg), cmd


@pytest.mark.parametrize(
    "cmd",
    [
        "pnpm install --frozen-lockfile",
        "pnpm exec vitest run hono",
        "cat src/hono.ts",
        "ls node_modules/hono",
        "pnpm test",
    ],
)
def test_own_package_rule_lets_the_checkout_work(sealed_cfg, cmd):
    assert guard.check("Bash", {"command": cmd}, sealed_cfg["sandbox"] + "/repo", sealed_cfg) is None, cmd


def _transcript(cfg, calls_):
    hdir = Path(cfg["sandbox"]) / "harness"
    hdir.mkdir(exist_ok=True)
    (hdir / "guard.json").write_text(json.dumps(cfg))
    lines = []
    for i, (cmd, refused) in enumerate(calls_):
        call = {"type": "tool_use", "id": f"t{i}", "name": "Bash", "input": {"command": cmd}}
        lines.append({"type": "assistant", "message": {"id": f"m{i}", "content": [call]}})
        out = "PreToolUse:Bash hook error: Blocked by the lab guard: x" if refused else "ok"
        lines.append(
            {
                "type": "user",
                "message": {
                    "content": [{"type": "tool_result", "tool_use_id": f"t{i}", "content": out, "is_error": refused}]
                },
            }
        )
    (hdir / "transcript.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n")
    return scan(Path(cfg["sandbox"]))


def test_scan_marks_other_sessions_temp_not_clean_even_when_refused(sealed_cfg):
    st = sealed_cfg["shared_temp"]
    report = _transcript(sealed_cfg, [("pnpm test", False), (f"ls {st}/-Users-x-other/scratchpad", True)])
    assert report["clean"] is False and guard.SHARED_TEMP_REASON in report["offences"][0]["reason"]
    (Path(sealed_cfg["sandbox"]) / "harness" / "guard.log").write_text(
        json.dumps({"tool": "Bash", "input": {"command": f"python3 x.py {st}/-Users-x-other/a"}, "deny": None}) + "\n"
    )
    report = _transcript(sealed_cfg, [("pnpm test", False)])
    assert report["clean"] is False and report["offences"][0]["line"] == "guard.log:1"


def test_scan_marks_an_own_package_install_not_clean(sealed_cfg):
    report = _transcript(sealed_cfg, [("pnpm add -D hono@latest", False)])
    assert report["clean"] is False and "own package" in report["offences"][0]["reason"]
    assert _transcript(sealed_cfg, [("pnpm add -D hono@latest", True)])["clean"] is True  # refused: nothing fetched


def test_codebase_keys_switch_sealed_mode_on(monkeypatch):
    monkeypatch.setattr(make_plan, "load_config", lambda name: {"run_sealed": True, "run_own_package": "sqlglot"})
    assert make_plan.codebase_run_extras("sqlglot") == {"sealed": True, "own_package": ["sqlglot"]}
    monkeypatch.undo()
    assert "sealed" not in make_plan.codebase_run_extras("gct")
