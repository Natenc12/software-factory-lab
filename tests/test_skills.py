"""Arms may ship skills (`skills/<name>/SKILL.md`); arms without them run exactly as before."""

import json
from pathlib import Path

import pytest

from harness import run, sandbox
from harness.common import read_json
from tests.conftest import calls, run_args, scenario

FIXTURE = Path(__file__).parent / "fixtures" / "arm-with-skills"
TOOLS_TODAY = "Task,Agent,Bash,Read,Edit,Write,NotebookEdit,Glob,Grep"


def session_calls(env):
    return [c for c in calls(env) if "stream-json" in c["argv"]]


def strip_prompt(argv):
    """The argv with the long appended system prompt replaced by a marker."""
    out = list(argv)
    if "--append-system-prompt" in out:
        out[out.index("--append-system-prompt") + 1] = "<arm prompt>"
    return out


@pytest.mark.parametrize("arm", [None, "P1"])
def test_arms_without_skills_keep_todays_command_settings_and_tools(lab_env, practice, arm):
    scenario(lab_env, p1_t1_1=["finish"])
    extra = ["--arm", str(Path(__file__).resolve().parents[1] / "arms" / arm)] if arm else []
    assert run.main(run_args(lab_env, practice, "p1-t1-1", *extra)) == 0
    root = lab_env["runs"] / "test" / "p1-t1-1"
    ctl = sandbox.control_dir(root)
    rec = read_json(root / "harness" / "run.json")
    [c] = session_calls(lab_env)
    expected = ["-p", "--output-format", "stream-json", "--verbose", "--model", "fake-model"]
    expected += ["--setting-sources", "", "--settings", str(ctl / "settings.json")]
    expected += ["--disable-slash-commands", "--strict-mcp-config", "--no-chrome", "--permission-mode", "dontAsk"]
    expected += ["--tools", TOOLS_TODAY, "--disallowedTools", "WebFetch,WebSearch", "--add-dir", str(root)]
    expected += ["--append-system-prompt", "<arm prompt>"] if arm else []
    expected += ["--session-id", rec["session_id"]]
    assert strip_prompt(c["argv"]) == expected
    s = json.loads((ctl / "settings.json").read_text())
    assert sorted(s) == ["autoMemoryEnabled", "hooks", "includeCoAuthoredBy", "permissions", "sandbox"]
    assert s["permissions"]["allow"] == ["Task", "Agent", "Bash", "Read", "Glob", "Grep", f"Edit(/{root}/**)"]
    assert not any("Skill" in r for r in s["permissions"]["allow"] + s["permissions"]["deny"])
    assert not (ctl / "plugin").exists()
    assert rec["skills_used"] == []


def test_arm_with_skills_gets_its_plugin_and_nothing_else(lab_env, practice):
    scenario(lab_env, p1_t1_1=["skill", "finish"])
    assert run.main(run_args(lab_env, practice, "p1-t1-1", "--arm", str(FIXTURE))) == 0
    root = lab_env["runs"] / "test" / "p1-t1-1"
    ctl = sandbox.control_dir(root)
    argv = session_calls(lab_env)[0]["argv"]
    assert argv[argv.index("--plugin-dir") + 1] == str(ctl / "plugin")
    assert "--disable-slash-commands" not in argv
    assert argv[argv.index("--tools") + 1] == TOOLS_TODAY + ",Skill"
    plugin = json.loads((ctl / "plugin" / ".claude-plugin" / "plugin.json").read_text())
    assert plugin["name"] == "work"
    assert sorted(p.name for p in (ctl / "plugin" / "skills").iterdir()) == ["release-note", "sql-style"]
    s = json.loads((ctl / "settings.json").read_text())
    assert s["disableBundledSkills"] is True
    assert s["skillOverrides"] == {"design": "off", "doctor": "off", "plugin-authoring": "off"}
    assert s["permissions"]["allow"][-2:] == ["Skill(work:release-note)", "Skill(work:sql-style)"]
    assert "Skill" not in s["permissions"]["allow"], "a bare Skill rule would let built-in commands run"
    assert {"Skill(init)", "Skill(security-review)"} <= set(s["permissions"]["deny"])
    # The skills reach the session only from the control folder: not the run's arm copy, not the checkout.
    assert (root / "arm" / "GUIDE.md").exists() and not (root / "arm" / "skills").exists()
    assert not list((root / "repo").rglob("SKILL.md"))
    arm_prompt = (ctl / "arm-prompt.md").read_text()
    assert "Skills are\navailable" in arm_prompt and "release note to" not in arm_prompt
    assert read_json(root / "harness" / "run.json")["skills_used"] == ["release-note", "sql-style"]


def test_skill_folders_hold_one_file_with_front_matter(tmp_path):
    arm = tmp_path / "arm"
    (arm / "skills" / "a").mkdir(parents=True)
    (arm / "skills" / "a" / "SKILL.md").write_text("---\nname: a\ndescription: Use when a.\n---\nDo a.\n")
    assert sandbox.parse_skill(sandbox.skill_files(arm)[0]) == {
        "name": "a",
        "description": "Use when a.",
        "body": "Do a.",
    }
    (arm / "skills" / "a" / "helper.sh").write_text("echo hi\n")
    with pytest.raises(RuntimeError, match="only SKILL.md"):
        sandbox.skill_files(arm)
    (arm / "skills" / "a" / "helper.sh").unlink()
    (arm / "skills" / "a" / "SKILL.md").write_text("---\nname: b\n---\nwrong name, no description\n")
    with pytest.raises(RuntimeError, match="front matter"):
        sandbox.parse_skill(arm / "skills" / "a" / "SKILL.md")
    assert sandbox.skill_files(tmp_path / "no-such-arm") == [] and sandbox.skill_files(None) == []


def test_arm_with_skills_only_pins_its_command_line(lab_env, practice):
    scenario(lab_env, p1_t1_1=["finish"])
    assert run.main(run_args(lab_env, practice, "p1-t1-1", "--arm", str(FIXTURE))) == 0
    root = lab_env["runs"] / "test" / "p1-t1-1"
    ctl = sandbox.control_dir(root)
    rec = read_json(root / "harness" / "run.json")
    [c] = session_calls(lab_env)
    expected = ["-p", "--output-format", "stream-json", "--verbose", "--model", "fake-model"]
    expected += ["--setting-sources", "", "--settings", str(ctl / "settings.json")]
    expected += [
        "--plugin-dir",
        str(ctl / "plugin"),
        "--strict-mcp-config",
        "--no-chrome",
        "--permission-mode",
        "dontAsk",
    ]
    expected += ["--tools", TOOLS_TODAY + ",Skill", "--disallowedTools", "WebFetch,WebSearch", "--add-dir", str(root)]
    expected += ["--append-system-prompt", "<arm prompt>", "--session-id", rec["session_id"]]
    assert strip_prompt(c["argv"]) == expected
    assert rec["workers_started"] == 0 and rec["workers"] == []


BOTH = Path(__file__).parent / "fixtures" / "arm-with-skills-and-agents"


def test_lead_and_worker_on_two_models_share_skills_sandbox_and_ceiling(lab_env, practice):
    scenario(lab_env, p6_t1_1=["delegate", "finish"])
    assert run.main(run_args(lab_env, practice, "p6-t1-1", "--arm", str(BOTH))) == 0
    root = lab_env["runs"] / "test" / "p6-t1-1"
    ctl = sandbox.control_dir(root)
    argv = session_calls(lab_env)[0]["argv"]
    assert argv[argv.index("--plugin-dir") + 1] == str(ctl / "plugin")
    assert argv[argv.index("--agents") + 1] == str(ctl / "agents.json")
    assert argv[argv.index("--tools") + 1].endswith(",Skill")
    worker = json.loads((ctl / "agents.json").read_text())["worker"]
    assert worker["model"] == "fake-worker" and "tools" not in worker, "no tool list: the worker inherits Skill"
    assert not list((root / "repo").rglob("SKILL.md")) and not (root / "arm" / "skills").exists()
    rec = read_json(root / "harness" / "run.json")
    assert rec["status"] == "finished"
    assert rec["workers_started"] == 1
    assert rec["workers"] == [{"type": "worker", "gist": "Write the release note"}]
    assert rec["skills_used"] == ["release-note"]  # called by the worker
    by = rec["by_model"]
    assert sorted(by) == ["fake-model", "fake-worker"]
    assert by["fake-worker"]["counted"] == 2 + 10 + 100 and by["fake-worker"]["cost_usd"] == 0.004
    # The ceiling and the totals count every model together.
    assert rec["tokens"]["counted"] == by["fake-model"]["counted"] + by["fake-worker"]["counted"]
    assert round(rec["cost_usd"], 6) == round(by["fake-model"]["cost_usd"] + by["fake-worker"]["cost_usd"], 6)
