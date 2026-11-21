"""The repo keeps the charter's layout, and race 1 arrived intact."""

import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ["arms", "harness", "tickets", "answers", "grader", "research", "results", "guide", "races/race-1"]


def test_charter_layout_exists():
    missing = [f for f in FOLDERS if not (ROOT / f).is_dir()]
    assert not missing, f"missing folders: {missing}"


def test_charter_export_names_its_source():
    head = (ROOT / "CHARTER.md").read_text(encoding="utf-8")[:400]
    assert "claude.ai/artifact/Nvmykhm6R3o9Aymk72Log2" in head
    assert "revision" in head


def test_race_1_grader_still_compiles(tmp_path):
    for name in ("grade.py", "make_tickets.py"):
        py_compile.compile(str(ROOT / "races/race-1/grader" / name), cfile=str(tmp_path / (name + "c")), doraise=True)
