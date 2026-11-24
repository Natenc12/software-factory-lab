"""The winning checklist (`checklist/`) is arm P5P as tested, packaged as the Claude Code plugin `work`."""

import json
from pathlib import Path

from harness import sandbox

ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "checklist"
P5P = ROOT / "arms" / "P5P"


def files(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_six_skills_are_p5p_byte_for_byte():
    shipped = files(CHECKLIST / "skills")
    tested = files(P5P / "skills")
    assert {k: v for k, v in shipped.items() if not k.startswith("work-ticket/")} == tested
    assert len(tested) == 6


def test_the_guide_is_p5p_guide_byte_for_byte_behind_new_front_matter():
    text = (CHECKLIST / "skills" / "work-ticket" / "SKILL.md").read_text(encoding="utf-8")
    head, sep, body = text[3:].partition("\n---\n")
    assert text.startswith("---\n") and sep
    assert body == (P5P / "GUIDE.md").read_text(encoding="utf-8")
    skill = sandbox.parse_skill(CHECKLIST / "skills" / "work-ticket" / "SKILL.md")
    assert skill["name"] == "work-ticket" and "do #N" in skill["description"]


def test_every_skill_loads_as_the_harness_loads_them():
    names = sorted(p.parent.name for p in sandbox.skill_files(CHECKLIST))
    assert names == sorted(["work-ticket", *(p.parent.name for p in sandbox.skill_files(P5P))])
    for path in sandbox.skill_files(CHECKLIST):
        sandbox.parse_skill(path)


def test_plugin_and_marketplace_name_it_work_as_the_runs_did():
    plugin = json.loads((CHECKLIST / ".claude-plugin" / "plugin.json").read_text())
    assert plugin["name"] == sandbox.SKILL_PLUGIN == "work"
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    [entry] = market["plugins"]
    assert entry["name"] == "work" and entry["source"] == "./checklist"


def test_only_skills_and_notes_ship():
    top = sorted(p.name for p in CHECKLIST.iterdir())
    assert top == [".claude-plugin", "CHANGES-FROM-WORK-TICKET.md", "README.md", "UNTESTED-IDEAS.md", "skills"]
    assert "not tested here" in (CHECKLIST / "CHANGES-FROM-WORK-TICKET.md").read_text()
    ideas = (CHECKLIST / "UNTESTED-IDEAS.md").read_text()
    assert sum(1 for line in ideas.splitlines() if line[:2] in {f"{n}." for n in range(1, 10)}) <= 5
