"""The six arms: what a run receives from each, the team's role limits, and the tester's blindness."""

import importlib.util
import json
import re
import shutil
import tempfile
from pathlib import Path

import pytest

from harness import run, sandbox
from tests.conftest import ROOT, calls, run_args, scenario

ARMS = ROOT / "arms"
STAGE_1 = ["P0", "P1", "P1R", "P3", "P2", "P4"]
STAGE_2 = ["P1T", "P1L", "P1A", "P5", "P5P"]
COMBINED = ["P5PA"]
LEAD = ["P6"]
NAMES = STAGE_1 + STAGE_2 + COMBINED + LEAD
spec = importlib.util.spec_from_file_location("role_guard", ARMS / "P4" / "hooks" / "role_guard.py")
rg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rg)


def run_texts(name: str, arms: Path = ARMS) -> dict[str, str]:
    """Every text a run of this arm can receive: instruction files, agent definitions and skills."""
    instructions, agents = sandbox.arm_files(arms / name)
    files = [*instructions, *agents, *sandbox.skill_files(arms / name)]
    return {str(p.relative_to(arms)): p.read_text(encoding="utf-8") for p in files}


def word_counts(name: str, arms: Path = ARMS) -> dict:
    """Words loaded up front (instructions, agent definitions, skill descriptions) and on demand (skill bodies)."""
    instructions, agents = sandbox.arm_files(arms / name)
    skills = [sandbox.parse_skill(p) for p in sandbox.skill_files(arms / name)]
    descriptions = sum(len(s["description"].split()) for s in skills)
    bodies = sum(len(s["body"].split()) for s in skills)
    files = sum(len(p.read_text(encoding="utf-8").split()) for p in [*instructions, *agents])
    return {"up_front": files + descriptions, "descriptions": descriptions, "bodies": bodies, "skills": len(skills)}


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
    rule = p1r[len(p1) :]
    assert rule.count("\n## ") == 1 and "reviewer" in rule
    for later in ("STOP", "merge brief", "checks"):
        assert later not in p1r


@pytest.mark.parametrize("name", ["P1R", "P3", "P2", "P4", "P6"])
def test_every_agent_is_opus_and_every_reviewer_is_read_only(name):
    _, agents = sandbox.arm_files(ARMS / name)
    assert agents
    for path in agents:
        agent, spec = sandbox.parse_agent(path)
        assert spec["model"] == "claude-opus-5-5", agent
        if agent == "reviewer":
            assert sorted(spec["tools"]) == ["Bash", "Glob", "Grep", "Read"]


@pytest.mark.parametrize("name", ["P3", "P2", "P4"])
def test_arms_with_a_brief_end_on_a_stop(name):
    text = "\n".join(t for f, t in run_texts(name).items() if "/agents/" not in f)
    assert "`STOP:` line" in text and "brief" in text


def test_sizes_note_matches_the_files():
    sizes = (ARMS / "SIZES.md").read_text()
    for name in NAMES:
        n = word_counts(name)
        skills = f"{n['descriptions']:,} \\| {n['bodies']:,}" if n["skills"] else "none \\| none"
        row = rf"^\| {name} \|[^|]*\| {n['up_front']:,} \|[^|]*\|[^|]*\| {skills} \|"
        assert re.search(row, sizes, re.M), f"{name}: {n}"


def test_skill_descriptions_count_up_front_and_bodies_on_demand():
    fixtures = Path(__file__).parent / "fixtures"
    n = word_counts("arm-with-skills", fixtures)
    guide = len((fixtures / "arm-with-skills" / "GUIDE.md").read_text().split())
    assert n["skills"] == 2
    assert n["descriptions"] == len("Use when the task asks for a release note.".split()) + len(
        "Use when writing or changing SQL.".split()
    )
    assert n["up_front"] == guide + n["descriptions"]
    assert n["bodies"] > n["descriptions"]
    assert set(run_texts("arm-with-skills", fixtures)) == {
        "arm-with-skills/GUIDE.md",
        "arm-with-skills/skills/release-note/SKILL.md",
        "arm-with-skills/skills/sql-style/SKILL.md",
    }


# ---- the team's role limits (arms/P4/hooks/role_guard.py) ----


@pytest.fixture(params=["any", "tmp"])
def team(request, tmp_path):
    """A work folder wherever pytest puts it, and one under /tmp, as on Linux."""
    if request.param == "tmp":
        tmp_path = Path(tempfile.mkdtemp(dir="/tmp"))
        request.addfinalizer(lambda: shutil.rmtree(tmp_path, ignore_errors=True))
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
        # gct-lab keeps code outside src/ too, and other files the tester has no use for
        ("Read", {"file_path": "web/app.js"}),
        ("Read", {"file_path": "scripts/migrate.py"}),
        ("Read", {"file_path": "migrations/0001_init.sql"}),
        ("Read", {"file_path": "eval/run.py"}),
        ("Read", {"file_path": "data/sample.json"}),
        ("Read", {"file_path": "uv.lock"}),
        ("Read", {"file_path": ".env.example"}),
        ("Read", {"file_path": ".github/workflows/ci.yml"}),
        ("Read", {"file_path": "web/README.md"}),
        ("Read", {"file_path": "tests/unit/test_x.py"}),
        ("Grep", {"pattern": "def", "path": "."}),
        ("Grep", {"pattern": "def", "path": "web"}),
        ("Grep", {"pattern": "def", "path": "scripts"}),
        ("Grep", {"pattern": "def", "path": "tests"}),
    ]
    for tool, inp in denied:
        assert ask(team, "tester", tool, **inp), (tool, inp)
    allowed = [
        ("Read", {"file_path": "../scratch/team/contract.md"}),
        ("Read", {"file_path": "../scratch/team/design.md"}),
        ("Read", {"file_path": "tests/conftest.py"}),
        ("Read", {"file_path": "tests/test_ticket_acceptance.py"}),
        ("Read", {"file_path": "README.md"}),
        ("Read", {"file_path": "CONTRIBUTING.md"}),
        ("Read", {"file_path": "pyproject.toml"}),
        ("Read", {"file_path": "tests/unit/conftest.py"}),
        ("Read", {"file_path": "design/overview.md"}),
        ("Read", {"file_path": "docs/guide/setup.md"}),
        ("Grep", {"pattern": "def", "path": "design"}),
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
    assert out["permissionDecision"] == "deny" and "in the checkout" in out["permissionDecisionReason"]


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
    assert "in the checkout the tester may read only" in results["toolu_probe_0"]["content"]


# ---- stage 2: P1 plus exactly one addition ----

POINTED = (
    "Use check-the-ask after you read the ticket and the code it touches.\n"
    "Use prove-each-claim before you write the pull request.\n"
)
SKILLS = {
    "check-the-ask",
    "prove-each-claim",
    "test-that-bites",
    "find-the-cause",
    "stay-in-scope",
    "fresh-eyes-review",
}


@pytest.mark.parametrize("name", STAGE_2)
def test_stage_2_arm_is_p1_unchanged_plus_one_addition(name):
    p1 = (ARMS / "P1" / "GUIDE.md").read_text()
    guide = (ARMS / name / "GUIDE.md").read_text()
    assert guide.startswith(p1) and len(guide) > len(p1)
    instructions, agents = sandbox.arm_files(ARMS / name)
    assert not agents
    expected = ["GUIDE.md", "SYSTEM-MAP.md"] if name == "P1A" else ["GUIDE.md"]
    assert [p.name for p in instructions] == expected
    for f, text in run_texts(name).items():
        for later in ("STOP", "merge brief", "contract", "reviewer"):
            assert later not in text, f"{f} borrows {later!r}"


def test_p1t_p1l_and_p1a_add_one_short_section():
    p1 = (ARMS / "P1" / "GUIDE.md").read_text()
    for name, heading in (("P1T", "## Tests first"), ("P1L", "## Small slices"), ("P1A", "## Before you plan")):
        added = (ARMS / name / "GUIDE.md").read_text()[len(p1) :]
        assert added.strip().startswith(heading) and added.count("## ") == 1
        assert len(added.split()) < 50, name
    assert "150" in (ARMS / "P1L" / "GUIDE.md").read_text()
    assert "system map that follows" in (ARMS / "P1A" / "GUIDE.md").read_text()


def test_p1a_map_is_one_page_and_points_to_the_decision_records():
    text = (ARMS / "P1A" / "SYSTEM-MAP.md").read_text()
    assert len(text.split()) < 700
    for part in ("## The parts", "## How a request flows", "## Where rules and decisions are recorded"):
        assert part in text
    assert "decision records" in text.split("## Before you plan a change")[1]
    listed = re.findall(r"\b00(\d\d)\b", text.split("## Where rules")[1].split("- **`design/architecture")[0])
    assert sorted(int(n) for n in listed) == list(range(1, 33)), "every decision record is listed, each once"


def test_p5_ships_the_six_skills_and_one_sentence():
    p1 = (ARMS / "P1" / "GUIDE.md").read_text()
    assert (ARMS / "P5" / "GUIDE.md").read_text() == p1 + "\nSkills are available.\n"
    skills = {p.parent.name: sandbox.parse_skill(p) for p in sandbox.skill_files(ARMS / "P5")}
    assert set(skills) == SKILLS
    for name, skill in skills.items():
        assert "../" not in skill["body"] and "./" not in skill["body"], name


def test_p5p_is_p5_plus_the_two_pointing_lines():
    assert (ARMS / "P5P" / "GUIDE.md").read_text() == (ARMS / "P5" / "GUIDE.md").read_text() + POINTED
    p5 = sorted(p.relative_to(ARMS / "P5") for p in (ARMS / "P5").rglob("*") if p.is_file())
    p5p = sorted(p.relative_to(ARMS / "P5P") for p in (ARMS / "P5P").rglob("*") if p.is_file())
    assert p5 == p5p
    for rel in p5:
        if rel.name != "GUIDE.md":
            assert (ARMS / "P5" / rel).read_bytes() == (ARMS / "P5P" / rel).read_bytes(), rel


# ---- P5PA: the pointed skills library combined with the architecture brief ----


def files_under(root: Path) -> dict[Path, bytes]:
    return {p.relative_to(root): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_p5pa_guide_is_p5p_guide_plus_p1a_section():
    p1 = (ARMS / "P1" / "GUIDE.md").read_text()
    section = (ARMS / "P1A" / "GUIDE.md").read_text()[len(p1) :]
    assert section.lstrip("\n").startswith("## Before you plan")
    assert (ARMS / "P5PA" / "GUIDE.md").read_text() == (ARMS / "P5P" / "GUIDE.md").read_text() + section


def test_p5pa_map_equals_p1a_map():
    assert (ARMS / "P5PA" / "SYSTEM-MAP.md").read_bytes() == (ARMS / "P1A" / "SYSTEM-MAP.md").read_bytes()


def test_p5pa_skills_equal_p5p_skills():
    assert files_under(ARMS / "P5PA" / "skills") == files_under(ARMS / "P5P" / "skills")


def test_p5pa_has_nothing_else():
    assert sorted(str(p) for p in files_under(ARMS / "P5PA") if p.parts[0] != "skills") == [
        "GUIDE.md",
        "SYSTEM-MAP.md",
    ]
    instructions, agents = sandbox.arm_files(ARMS / "P5PA")
    assert [p.name for p in instructions] == ["GUIDE.md", "SYSTEM-MAP.md"] and not agents


# ---- P6: the chief of staff (P5P plus a lead brief and one general worker) ----


def test_p6_guide_is_p5p_guide_plus_the_lead_brief():
    p5p = (ARMS / "P5P" / "GUIDE.md").read_text()
    guide = (ARMS / "P6" / "GUIDE.md").read_text()
    assert guide.startswith(p5p)
    brief = guide[len(p5p) :]
    assert brief.count("\n## ") == 1 and "## Leading the work" in brief
    for point in ("answer to the owner", "yourself", "cannot see your conversation", "own every claim", "re-run"):
        assert point in brief, point
    for fixed in ("STOP", "merge brief", "contract", "planner", "tester", "reviewer", "must start", "first,"):
        assert fixed not in brief, f"the lead brief fixes {fixed!r}"


def test_p6_skills_equal_p5p_skills():
    assert files_under(ARMS / "P6" / "skills") == files_under(ARMS / "P5P" / "skills")


def test_p6_has_one_general_worker_on_opus():
    instructions, agents = sandbox.arm_files(ARMS / "P6")
    assert [p.name for p in instructions] == ["GUIDE.md"]
    assert [p.name for p in agents] == ["worker.md"]
    name, spec = sandbox.parse_agent(agents[0])
    assert name == "worker" and spec["model"] == "claude-opus-5-5" and "hooks" not in spec
    assert sorted(spec["tools"]) == ["Bash", "Edit", "Glob", "Grep", "Read", "Write"]
    assert 2 <= spec["description"].count(". ") + 1 <= 3


def test_p6_run_gets_its_skills_and_its_worker(lab_env, practice):
    """The harness passes an arm's skills plugin and its agents together; the lead's model comes from the run."""
    scenario(lab_env, p6_t1_1=["finish"])
    assert run.main(run_args(lab_env, practice, "p6-t1-1", "--arm", str(ARMS / "P6"))) == 0
    ctl = sandbox.control_dir(lab_env["runs"] / "test" / "p6-t1-1")
    [argv] = [c["argv"] for c in calls(lab_env) if "stream-json" in c["argv"]]
    assert argv[argv.index("--model") + 1] == "fake-model"
    assert argv[argv.index("--plugin-dir") + 1] == str(ctl / "plugin")
    assert argv[argv.index("--agents") + 1] == str(ctl / "agents.json")
    assert argv[argv.index("--tools") + 1].split(",")[:2] == ["Task", "Agent"]
    assert "Skill" in argv[argv.index("--tools") + 1].split(",")
    assert sorted(p.name for p in (ctl / "plugin" / "skills").iterdir()) == sorted(SKILLS)
    agents = json.loads((ctl / "agents.json").read_text())
    assert list(agents) == ["worker"] and agents["worker"]["model"] == "claude-opus-5-5"
    settings = json.loads((ctl / "settings.json").read_text())
    assert {"Task", "Agent"} <= set(settings["permissions"]["allow"])
