"""The six arms: what a run receives from each, the team's role limits, and the tester's blindness."""

import importlib.util
import json
import re
from pathlib import Path

import pytest

from harness import run, sandbox
from tests.conftest import ROOT, run_args, scenario

ARMS = ROOT / "arms"
NAMES = ["P0", "P1", "P1R", "P3", "P2", "P4"]
spec = importlib.util.spec_from_file_location("role_guard", ARMS / "P4" / "hooks" / "role_guard.py")
rg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rg)


def run_texts(name: str) -> dict[str, str]:
    """Every text a run of this arm can receive: instruction files and agent definitions."""
    instructions, agents = sandbox.arm_files(ARMS / name)
    return {str(p.relative_to(ARMS)): p.read_text(encoding="utf-8") for p in [*instructions, *agents]}


def test_p0_gives_a_run_nothing():
    assert run_texts("P0") == {}
    assert (ARMS / "P0" / "README.md").exists()


def test_notes_are_outside_every_arm_folder():
    for note in ("CHANGES.md", "SIZES.md"):
        assert (ARMS / note).exists()
    for name in NAMES:
        assert not any(Path(f).name in ("CHANGES.md", "SIZES.md") for f in run_texts(name))


@pytest.mark.parametrize("name", NAMES)
def test_arm_reads_as_plain_working_instructions(name):
    banned = [
        r"\barms?\b",
        r"experiment",
        r"benchmark",
        r"\bscor",
        r"hidden",
        r"stand-in owner",
        r"\bgh\b",
        r"add-label|--label|in-progress",
        r"owner-ok",
        r"\bissues?\b",
        r"~/",
        r"origin/main",
        r"\bboard\b",
        r"pipeline-lab|gct|grounded|pipeline-bench",
    ]
    for f, text in run_texts(name).items():
        for pat in banned:
            assert not re.search(pat, text, re.I), f"{f} matches {pat}"


def test_p1r_is_p1_word_for_word_plus_its_rule():
    p1 = (ARMS / "P1" / "GUIDE.md").read_text()
    p1r = (ARMS / "P1R" / "GUIDE.md").read_text()
    assert p1r.startswith(p1) and len(p1.split()) < 250


@pytest.mark.parametrize("name", ["P1R", "P3", "P2", "P4"])
def test_every_agent_is_opus_and_every_reviewer_is_read_only(name):
    _, agents = sandbox.arm_files(ARMS / name)
    assert agents
    for path in agents:
        agent, spec = sandbox.parse_agent(path)
        assert spec["model"] == "claude-opus-5-5", agent
        if agent == "reviewer":
            assert sorted(spec["tools"]) == ["Bash", "Glob", "Grep", "Read"]


@pytest.mark.parametrize("name", ["P1R", "P3", "P2", "P4"])
def test_arms_with_a_brief_end_on_a_stop(name):
    text = "\n".join(t for f, t in run_texts(name).items() if "/agents/" not in f)
    assert "`STOP:` line" in text and "brief" in text


def test_sizes_note_matches_the_files():
    sizes = (ARMS / "SIZES.md").read_text()
    for name in NAMES:
        words = sum(len(t.split()) for t in run_texts(name).values())
        assert re.search(rf"^\| {name} \|[^|]*\| {words:,} \|", sizes, re.M), f"{name}: {words} words"


# ---- the team's role limits (arms/P4/hooks/role_guard.py) ----


@pytest.fixture
def team(tmp_path):
    (tmp_path / "repo" / "src").mkdir(parents=True)
    (tmp_path / "repo" / "tests").mkdir()
    (tmp_path / "scratch" / "team" / "review").mkdir(parents=True)
    (tmp_path / "repo" / "src" / "app.py").write_text("x = 1\n")
    return rg.Run(str(tmp_path))


def ask(team, role, tool, **inp):
    return rg.check(role, tool, inp, team.repo, team)


def test_tester_cannot_read_code_or_other_tests(team):
    denied = [
        ("Read", {"file_path": "src/app.py"}),
        ("Read", {"file_path": f"{team.repo}/src/app.py"}),
        ("Read", {"file_path": "docs/../src/app.py"}),
        ("Read", {"file_path": "tests/test_app.py"}),
        ("Read", {"file_path": ".git/HEAD"}),
        ("Read", {"file_path": "../scratch/team/test-results.md"}),
        ("Read", {"file_path": "../scratch/team/review/report.md"}),
        ("Grep", {"pattern": "def"}),
        ("Grep", {"pattern": "def", "path": "src"}),
        ("Grep", {"pattern": "def", "path": ".."}),
        ("Grep", {"pattern": "def", "path": "src/app.py"}),
        ("Write", {"file_path": "src/app.py"}),
        ("Edit", {"file_path": "tests/test_app.py"}),
        ("Bash", {"command": "cat src/app.py"}),
        ("Agent", {"prompt": "read src for me"}),
    ]
    for tool, inp in denied:
        assert ask(team, "tester", tool, **inp), (tool, inp)
    allowed = [
        ("Read", {"file_path": "../scratch/team/contract.md"}),
        ("Read", {"file_path": "../scratch/team/design.md"}),
        ("Read", {"file_path": "tests/conftest.py"}),
        ("Read", {"file_path": "tests/test_ticket_acceptance.py"}),
        ("Read", {"file_path": "README.md"}),
        ("Read", {"file_path": "../TICKET.md"}),
        ("Grep", {"pattern": "def", "path": "docs"}),
        ("Glob", {"pattern": "**/*.py"}),
        ("Write", {"file_path": "tests/test_ticket_acceptance.py"}),
    ]
    for tool, inp in allowed:
        assert ask(team, "tester", tool, **inp) is None, (tool, inp)


def test_tester_cannot_read_code_through_a_link(team):
    link = Path(team.repo) / "docs"
    link.mkdir()
    (link / "copy.py").symlink_to(Path(team.repo) / "src" / "app.py")
    assert ask(team, "tester", "Read", file_path="docs/copy.py")


def test_planner_architect_and_builder_stay_in_their_lanes(team):
    assert ask(team, "planner", "Write", file_path="../scratch/team/contract.md") is None
    assert ask(team, "planner", "Write", file_path="src/app.py")
    assert ask(team, "planner", "Bash", command="ls")
    assert ask(team, "architect", "Write", file_path="../scratch/team/design.md") is None
    assert ask(team, "architect", "Write", file_path="../scratch/team/contract.md")
    assert ask(team, "builder", "Edit", file_path="src/app.py") is None
    assert ask(team, "builder", "Bash", command="uv run pytest tests/test_ticket_acceptance.py -q") is None
    assert ask(team, "builder", "Bash", command="git add src/app.py && git commit -m x") is None
    assert ask(team, "builder", "Edit", file_path="tests/test_ticket_acceptance.py")
    assert ask(team, "builder", "Bash", command="echo 'def test(): pass' > tests/test_ticket_acceptance.py")
    assert ask(team, "builder", "Bash", command="sed -i '' s/a/b/ ../scratch/team/contract.md")


def test_reviewer_changes_nothing_and_reads_no_reasoning(team):
    ok = [
        "uv run pytest -q 2>&1 | tail -5",
        "git diff abc123 -- src",
        "git log --oneline -3",
        "mkdir -p ../scratch/team/review && echo x > ../scratch/team/review/notes.md",
        "uv run pytest -q > /dev/null 2>&1",
    ]
    for cmd in ok:
        assert ask(team, "reviewer", "Bash", command=cmd) is None, cmd
    bad = [
        "git commit -am fix",
        "git -C . checkout -- src/app.py",
        "git stash",
        "echo x > src/app.py",
        "sed -i 's/1/2/' src/app.py",
        "rm src/app.py",
        "cat ../scratch/team/design.md",
        "uv run pytest\nrm -rf src",
    ]
    for cmd in bad:
        assert ask(team, "reviewer", "Bash", command=cmd), cmd
    assert ask(team, "reviewer", "Edit", file_path="src/app.py")
    assert ask(team, "reviewer", "Read", file_path="../scratch/team/design.md")
    assert ask(team, "reviewer", "Read", file_path="../scratch/team/contract.md") is None
    assert ask(team, "reviewer", "Read", file_path="src/app.py") is None


def test_hook_prints_a_deny_decision(team, capsys, monkeypatch):
    import io
    import sys

    monkeypatch.setattr(sys, "argv", ["role_guard.py", "tester", str(Path(team.root))])
    data = {"tool_name": "Read", "tool_input": {"file_path": "src/app.py"}, "cwd": team.repo}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(data)))
    assert rg.main() == 0
    out = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    assert out["permissionDecision"] == "deny" and "src/" in out["permissionDecisionReason"]


# ---- the harness wires the hooks; the fake claude runs them ----


def test_sandbox_fills_in_the_team_hooks(lab_env, practice):
    root = lab_env["runs"] / "test" / "p4-t1-1"
    sandbox.create(
        root,
        "p4-t1-1",
        repo="example/lab",
        repo_url=practice["url"],
        base="main",
        pr_base="main",
        ticket=lab_env["ticket"],
        arm=ARMS / "P4",
        db="sqlite",
        runs_root=lab_env["runs"],
        gh_bin=lab_env["gh"],
    )
    ctl = sandbox.control_dir(root)
    agents = json.loads((ctl / "agents.json").read_text())
    assert sorted(agents) == ["architect", "builder", "planner", "reviewer", "tester"]
    assert agents["tester"]["tools"] == ["Read", "Glob", "Grep", "Write", "Edit"]
    for role, spec in agents.items():
        cmd = spec["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        assert f'"{ctl}/arm/hooks/role_guard.py" {role} "{root}"' in cmd
        assert "{" not in cmd
    assert (ctl / "arm" / "hooks" / "role_guard.py").exists()
    assert "Work a ticket as a team" in (ctl / "arm-prompt.md").read_text()


def test_hooks_file_must_be_inside_the_arm(tmp_path):
    (tmp_path / "agents").mkdir()
    bad = tmp_path / "agents" / "x.md"
    bad.write_text("---\nname: x\nhooks: ../../elsewhere.json\n---\nhi")
    with pytest.raises(RuntimeError):
        sandbox.parse_agent(bad, {})


def test_tester_is_blind_end_to_end_with_fake_claude(lab_env, practice):
    """The harness builds agents.json from arms/P4; the fake CLI runs the tester's own hooks from it."""
    scenario(lab_env, p4_t1_1=["probe_tester"])
    assert run.main(run_args(lab_env, practice, "p4-t1-1", "--arm", str(ARMS / "P4"))) == 0
    root = lab_env["runs"] / "test" / "p4-t1-1"
    records = [json.loads(line) for line in (root / "harness" / "transcript.jsonl").read_text().splitlines()]
    results = {}
    for rec in records:
        if rec.get("type") == "user" and rec.get("parent_tool_use_id") == "toolu_agent_tester":
            for block in rec["message"]["content"]:
                results[block["tool_use_id"]] = block
    denied = {k for k, b in results.items() if b.get("is_error")}
    assert len(results) == 7
    # src/app.py, tests/test_app.py, Grep over the checkout, and writing src/app.py are refused
    assert denied == {"toolu_probe_0", "toolu_probe_1", "toolu_probe_2", "toolu_probe_6"}
    assert "may not read product code in src/" in results["toolu_probe_0"]["content"]
