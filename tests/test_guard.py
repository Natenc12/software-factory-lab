"""The guard keeps a run inside its sandbox, off the web, and away from GitHub except through `lab`."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from harness import guard
from harness.common import LAB_ROOT
from harness.sandbox import guard_config

HOME = os.path.realpath(os.path.expanduser("~"))


@pytest.fixture
def cfg(tmp_path):
    runs = tmp_path / "runs"
    box = runs / "stage" / "p1-t1-1"
    (box / "repo").mkdir(parents=True)
    (box / "harness").mkdir()
    (runs / "stage" / "p2-t1-1").mkdir()
    c = guard_config(box.resolve(), runs.resolve(), ["~/somewhere-private"])
    c["log"] = None
    return c


def deny(cfg, tool, inp, cwd=None):
    return guard.check(tool, inp, cwd or cfg["sandbox"] + "/repo", cfg)


@pytest.mark.parametrize(
    "cmd",
    [
        "gh pr list",
        "/opt/homebrew/bin/gh issue view 1",
        "git fetch origin",
        "git -C . pull",
        "git push origin HEAD:main",
        "git remote -v",
        "git ls-remote https://example.invalid/x",
        "git clone x y",
        "curl https://example.com",
        "bash -c 'gh api user'",
        "echo hi && gh pr view",
        "FOO=1 gh pr list",
        "env -i gh pr list",
        "cat $(echo x) | wget -q x",
        "git log --oneline; git push",
        "ls ../../p2-t1-1",
        "cat ../harness/run.json",
        "cd",
        "cd ~ && ls",
        "cat ~/repos/pipeline-bench/answers/owner.md",
        "ls ~/repos/grounded-class-tutor",
        "python -c \"print(open('/Users/someone/x').read())\"",
        "echo see https://github.com/x/grounded-class-tutor",
        f"cat {LAB_ROOT}/CHARTER.md",
        "cat ~/somewhere-private/notes.txt",
    ],
)
def test_bash_blocked(cfg, cmd):
    assert deny(cfg, "Bash", {"command": cmd}), cmd


@pytest.mark.parametrize(
    "cmd",
    [
        "git status",
        "git log --oneline origin/main..HEAD",
        "git commit -m 'Fix page offset; add test'",
        "uv run pytest -q",
        "cat ../TICKET.md",
        "lab pr open --title 'Fix paging' --body-file ../scratch/body.md",
        "lab pr checks",
        "ls /usr/bin | head",
        "python3 -c 'import sys; print(sys.version)'",
        "grep -rn hidden src/",
        "ls ~/.local/bin",
        "echo x > /dev/null",
    ],
)
def test_bash_allowed(cfg, cmd):
    assert deny(cfg, "Bash", {"command": cmd}) is None, cmd


def test_shell_outside_sandbox_must_cd_back(cfg):
    assert deny(cfg, "Bash", {"command": "ls"}, cwd=HOME)
    assert deny(cfg, "Bash", {"command": f"cd {cfg['sandbox']}/repo"}, cwd=HOME) is None


def test_file_tools(cfg):
    box = cfg["sandbox"]
    assert deny(cfg, "Read", {"file_path": f"{box}/repo/app.py"}) is None
    assert deny(cfg, "Read", {"file_path": "../TICKET.md"}) is None
    assert deny(cfg, "Write", {"file_path": f"{box}/scratch/notes.md"}) is None
    assert deny(cfg, "Read", {"file_path": f"{box}/harness/owner-log.jsonl"})
    assert deny(cfg, "Read", {"file_path": f"{box}/../p2-t1-1/repo/app.py"})
    assert deny(cfg, "Read", {"file_path": str(LAB_ROOT / "answers" / "x.md")})
    assert deny(cfg, "Read", {"file_path": f"{HOME}/.claude/skills/work-ticket/SKILL.md"})
    assert deny(cfg, "Write", {"file_path": "/usr/local/x.txt"})
    assert deny(cfg, "Read", {"file_path": "/srv/hidden/tests.py"})
    assert deny(cfg, "Edit", {"file_path": f"{HOME}/.bashrc"})
    assert deny(cfg, "Glob", {"pattern": f"{HOME}/repos/**/*.py"})
    assert deny(cfg, "WebFetch", {"url": "https://example.com"})
    assert deny(cfg, "WebSearch", {"query": "x"})
    assert deny(cfg, "SendMessage", {"to": "x"})
    assert deny(cfg, "mcp__github__get_issue", {})


def test_hook_prints_a_deny_decision(cfg, tmp_path):
    path = tmp_path / "guard.json"
    cfg["log"] = str(tmp_path / "guard.log")
    path.write_text(json.dumps(cfg))
    hook = os.path.join(os.path.dirname(guard.__file__), "guard.py")
    data = {"tool_name": "Bash", "tool_input": {"command": "gh pr list"}, "cwd": cfg["sandbox"] + "/repo"}
    out = subprocess.run([sys.executable, hook, str(path)], input=json.dumps(data), capture_output=True, text=True)
    decision = json.loads(out.stdout)["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny" and "lab" in decision["permissionDecisionReason"]
    data["tool_input"] = {"command": "git status"}
    out = subprocess.run([sys.executable, hook, str(path)], input=json.dumps(data), capture_output=True, text=True)
    assert out.stdout.strip() == "" and out.returncode == 0
    assert len((tmp_path / "guard.log").read_text().splitlines()) == 2


# ---- working directory: `cd` within a command (guard and scan) and across commands (scan) ----


def test_guard_follows_cd_within_a_command(cfg):
    box = cfg["sandbox"]
    import os as _os

    for d in ("repo/src/gct/api", "repo/tests/gct/api", "scratch/review"):
        _os.makedirs(f"{box}/{d}", exist_ok=True)
    ok = [
        "cd src/gct && ls ../../tests/gct/api",
        "cd src/gct/api; cat ../../../tests/gct/api/conftest.py",
        f"cd {box}/scratch/review && ../../repo/.venv/bin/python -c 'print(1)'",
        "cd ../scratch && cd review && ls ../../repo",
    ]
    for cmd in ok:
        assert deny(cfg, "Bash", {"command": cmd}) is None, cmd
    bad = [
        "cd src && cat ../../../p2-t1-1/repo/app.py",
        "cd .. && cd .. && ls p2-t1-1",
        "cd src/gct && ls ../../../harness",
        "cd / && cat Users/someone/x",
    ]
    for cmd in bad:
        assert deny(cfg, "Bash", {"command": cmd}), cmd
    # A `cd` the guard cannot follow keeps the last folder it knows, as before.
    assert deny(cfg, "Bash", {"command": "cd $D && cat ../../p2-t1-1/x"})


def _scan_folder(tmp_path, cfg, commands):
    """A run folder whose transcript runs `commands` as Bash calls; each item is (cmd, is_error, result, shell)."""
    from harness.scan import scan

    hdir = Path(cfg["sandbox"]) / "harness"
    (hdir / "guard.json").write_text(json.dumps(cfg))
    lines = []
    for i, (cmd, err, out, shell) in enumerate(commands):
        call = {"type": "tool_use", "id": f"t{i}", "name": "Bash", "input": {"command": cmd}}
        lines.append({"type": "assistant", "parent_tool_use_id": shell, "message": {"id": f"m{i}", "content": [call]}})
        res = {"type": "tool_result", "tool_use_id": f"t{i}", "content": out, "is_error": err}
        lines.append({"type": "user", "parent_tool_use_id": shell, "message": {"content": [res]}})
    (hdir / "transcript.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n")
    return scan(Path(cfg["sandbox"]))


def test_scan_follows_cd_across_commands_and_shells(cfg, tmp_path):
    box = cfg["sandbox"]
    import os as _os

    _os.makedirs(f"{box}/scratch/review", exist_ok=True)
    _os.makedirs(f"{box}/repo/src/gct", exist_ok=True)
    report = _scan_folder(
        tmp_path,
        cfg,
        [
            ("cd src/gct && ls ../../tests/gct/api", False, "", None),  # the stage 2b case, within a command
            (f"cd {box}/scratch/review", False, "", None),
            ("../../repo/.venv/bin/python -m pytest -q", True, "1 failed", None),  # carried from the last call
            ("cat ../TICKET.md", False, "", "toolu_agent"),  # a subagent's shell starts in the checkout
        ],
    )
    assert report["clean"] is True, report["offences"]
    assert report["offences"] == [] and report["could_not_resolve"] == []


def test_scan_still_catches_real_escapes_and_lists_unknowns(cfg, tmp_path):
    box = cfg["sandbox"]
    report = _scan_folder(
        tmp_path,
        cfg,
        [
            ("cd src && cat ../../../p2-t1-1/repo/app.py", False, "x = 1", None),
            ("cd $WORK && cat ../../notes.txt", False, "", None),
            ("cat ../../notes.txt", False, "", None),  # still unknown: the last cd could not be followed
            (f"cd {box}/repo", False, "", None),
            ("cat ../../p2-t1-1/repo/app.py", False, "x = 1", None),  # known again, and outside
            ("echo hi", False, f"Shell cwd was reset to {box}/scratch", None),
            ("cat ../TICKET.md", False, "", None),
        ],
    )
    assert report["clean"] is False
    assert [o["line"] for o in report["offences"]] == [1, 9]
    assert all("forbidden place" in o["reason"] for o in report["offences"])
    unknown = [u["input"]["command"] for u in report["could_not_resolve"]]
    assert unknown == ["cd $WORK && cat ../../notes.txt", "cat ../../notes.txt"]
