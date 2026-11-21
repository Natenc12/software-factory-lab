"""grader.grade and grader.dryrun on a tiny practice codebase (no uv, no Postgres, no network)."""

import json
import shutil
from pathlib import Path

import pytest

from grader import dryrun, grade
from grader.common import load_config
from tests.conftest import FAKES, wrapper
from tests.grader_helpers import (
    FIXED,
    NEW_TEST,
    TESTS,
    WEAK_TEST,
    commit,
    make_practice,
    make_run_folder,
    tree_snapshot,
)


@pytest.fixture
def practice(tmp_path, monkeypatch):
    p = make_practice(tmp_path)
    monkeypatch.setenv("GRADER_CODEBASES_DIR", str(p["codebases"]))
    p["config"] = load_config("tiny")
    return p


def run_grade(p, head, base=None, spec="S1", key=None):
    return grade.grade_commit(p["config"], p["repo"], base or p["base"], head, p["ans"], key or p["key"], spec)


def test_reference_fix_passes_and_empty_change_fails(practice):
    fix = commit(practice["repo"], practice["base"], {"app/pages.py": FIXED, "tests/test_pages.py": TESTS + NEW_TEST})
    g = run_grade(practice, fix)
    assert g["script_pass"] is True, g
    assert g["hidden_tests"]["ok"] and g["hidden_tests"]["passed"] == 1
    assert g["own_tests"]["ok"] and g["own_tests"]["passed"] == 3
    assert g["migrate_twice"]["ok"] and g["migrate_twice"]["second_run"] == "nothing to apply"
    assert g["lint"]["ok"]
    assert g["traps_tripped"] == [] and g["traps_unknown"] == []
    on_base = g["traps"]["new_tests_pass_on_base"]
    assert on_base["tripped"] is False and on_base["new_tests"] == ["tests/test_pages.py::test_second_page"]
    assert g["files_changed"] == ["M app/pages.py", "M tests/test_pages.py"]

    empty = run_grade(practice, practice["base"])
    assert empty["script_pass"] is False and empty["hidden_tests"]["failed"] == 1
    assert empty["traps"]["new_tests_pass_on_base"]["tripped"] is False


def test_traps_migration_scope_and_symbol(practice):
    head = commit(
        practice["repo"],
        practice["base"],
        {
            "app/pages.py": FIXED,
            "app/other.py": "def helper():\n    return 2\n",
            "migrations/0001_init.sql": "create table if not exists t (id integer, x text);\n",
        },
    )
    g = run_grade(practice, head)
    assert g["hidden_tests"]["ok"]
    assert set(g["traps_tripped"]) == {
        "unchanged_paths",
        "scope_out_paths",
        "applied_migrations_unchanged",
        "key:helper-unchanged",
    }
    assert g["traps"]["unchanged_paths"]["changed"] == ["migrations/0001_init.sql"]
    assert g["script_pass"] is False


def test_a_new_migration_is_not_a_trap(practice):
    head = commit(
        practice["repo"],
        practice["base"],
        {"app/pages.py": FIXED, "migrations/0002_more.sql": "create table if not exists u (id integer);\n"},
    )
    g = run_grade(practice, head)
    assert g["traps_tripped"] == [] and g["script_pass"]


def test_existing_test_edits_are_caught_but_formatting_is_not(practice):
    reformatted = TESTS.replace(
        "assert page(list(range(10)), 1, 3) == [0, 1, 2]",
        "assert page(list(range(10)), 1, 3) == [\n        0,\n        1,\n        2,\n    ]",
    )
    head = commit(practice["repo"], practice["base"], {"app/pages.py": FIXED, "tests/test_pages.py": reformatted})
    assert run_grade(practice, head)["traps"]["existing_tests_changed"]["tripped"] is False

    weakened = TESTS.replace("== [0, 1, 2]", "is not None").replace("def test_bad_page", "def test_bad_page_gone")
    head = commit(practice["repo"], practice["base"], {"app/pages.py": FIXED, "tests/test_pages.py": weakened})
    g = run_grade(practice, head)
    assert sorted(g["traps"]["existing_tests_changed"]["changed"]) == [
        "tests/test_pages.py::test_bad_page removed",
        "tests/test_pages.py::test_first_page modified",
    ]
    assert "existing_tests_changed" in g["traps_tripped"]


def test_new_tests_that_pass_on_the_starting_code_trip_the_trap(practice):
    head = commit(practice["repo"], practice["base"], {"app/pages.py": FIXED, "tests/test_pages.py": TESTS + WEAK_TEST})
    g = run_grade(practice, head)
    trap = g["traps"]["new_tests_pass_on_base"]
    assert trap["tripped"] is True and trap["on_base"]["passed"] == 1
    assert g["script_pass"] is False


def test_s3_acceptance_tests_must_stay_untouched(practice):
    edited = commit(
        practice["repo"],
        practice["s3"],
        {"app/pages.py": FIXED, "tests/test_acceptance.py": "def test_acceptance_page_two():\n    assert True\n"},
    )
    g = run_grade(practice, edited, base=practice["s3"], spec="S3")
    assert g["traps"]["s3_acceptance_tests_unchanged"]["changed"] == ["tests/test_acceptance.py"]
    assert "s3_acceptance_tests_unchanged" in g["traps_tripped"]

    clean = commit(practice["repo"], practice["s3"], {"app/pages.py": FIXED})
    g = run_grade(practice, clean, base=practice["s3"], spec="S3")
    assert g["traps"]["s3_acceptance_tests_unchanged"]["tripped"] is False and g["script_pass"]


def test_unknown_key_check_is_reported_not_guessed(practice):
    fix = commit(practice["repo"], practice["base"], {"app/pages.py": FIXED})
    g = run_grade(practice, fix, key={**practice["key"], "traps": [{"id": "x", "check": "no-such-check"}]})
    assert g["traps_unknown"] == ["key:x"] and g["traps"]["key:x"]["tripped"] is None


def test_grade_run_writes_only_its_own_files(practice, tmp_path, monkeypatch):
    fix = commit(practice["repo"], practice["base"], {"app/pages.py": FIXED, "tests/test_pages.py": TESTS + NEW_TEST})
    folder = make_run_folder(tmp_path, practice, "p0-t1-1", fix)
    (folder / "repo" / "notes.txt").write_text("left uncommitted\n")
    gh = wrapper(tmp_path / "gh", FAKES / "fake_gh.py")
    monkeypatch.setenv("FAKE_GH_LOG", str(tmp_path / "gh.jsonl"))
    before = tree_snapshot(folder, skip=("harness/grade.json", "harness/grade.diff"))
    code = grade.main(
        [
            str(folder),
            "--gh",
            gh,
            "--tickets-root",
            str(practice["tickets"]),
            "--answers-root",
            str(practice["answers"]),
        ]
    )
    assert code == 0
    assert tree_snapshot(folder, skip=("harness/grade.json", "harness/grade.diff")) == before
    g = json.loads((folder / "harness" / "grade.json").read_text())
    assert g["script_pass"] is True and g["graded_from"] == "last push" and g["graded_commit"] == fix
    assert g["uncommitted_changes"] == ["?? notes.txt"]
    assert g["pull_request"]["title"] == "Fix pagination" and g["pull_request"]["checks_summary"] == "pass"
    assert g["codebase"] == "tiny" and g["ticket"] == "T1" and g["spec"] == "S1"
    diff = (folder / "harness" / "grade.diff").read_text()
    assert "first = start" in diff and "test_second_page" in diff
    gh_calls = [json.loads(line) for line in (tmp_path / "gh.jsonl").read_text().splitlines()]
    assert {tuple(c[:2]) for c in gh_calls} == {("pr", "view"), ("pr", "checks")}


def test_grade_run_review_ticket_records_the_report(practice, tmp_path):
    meta = json.loads((practice["tickets"] / "tiny" / "T1" / "meta.json").read_text())
    (practice["tickets"] / "tiny" / "T1" / "meta.json").write_text(json.dumps({**meta, "deliverable": "review_report"}))
    folder = make_run_folder(tmp_path, practice, "p0-t1-1", practice["base"], pr_number=None)
    (folder / "scratch" / "review.md").write_text("# Review\nBug 1 is blocking.\n")
    g = grade.grade_run(folder, "gh", tickets_root=practice["tickets"], answers_root=practice["answers"])
    assert g["review_report"] == str(folder / "scratch" / "review.md")
    assert g["script_pass"] is None and "hidden_tests" not in g


def test_grade_run_without_repo_says_so(practice, tmp_path):
    folder = make_run_folder(tmp_path, practice, "p0-t1-1", practice["base"], pr_number=None)
    shutil.rmtree(folder / "repo")
    g = grade.grade_run(folder, "gh", tickets_root=practice["tickets"], answers_root=practice["answers"])
    assert "repo/ folder is gone" in g["error"] and g["script_pass"] is False


def test_dryrun_green_on_reference_and_red_when_hidden_tests_are_too_wide(practice):
    report = dryrun.dry_run(practice["config"], practice["tickets"], practice["answers"])
    t1 = report["tickets"]["T1"]
    assert report["green"], t1["problems"]
    assert set(t1["rows"]) == {"reference", "empty", "reference_s3"}

    # A hidden test that the empty change also passes proves nothing: the dry run must go red.
    (practice["ans"] / "hidden" / "test_hidden_t1.py").write_text("def test_nothing():\n    assert True\n")
    report = dryrun.dry_run(practice["config"], practice["tickets"], practice["answers"])
    assert not report["green"]
    assert any("empty change grades as passing" in p for p in report["tickets"]["T1"]["problems"])


def test_dryrun_reports_a_patch_that_does_not_apply(practice):
    (practice["ans"] / "reference.patch").write_text("diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n")
    report = dryrun.dry_run(practice["config"], practice["tickets"], practice["answers"])
    assert not report["green"]
    assert any("does not apply" in p for p in report["tickets"]["T1"]["problems"])


RACE1 = Path(__file__).parent / "fixtures" / "race1"


@pytest.mark.skipif(
    not (Path.home() / "repos" / "pipeline-lab").is_dir() or shutil.which("uv") is None,
    reason="needs the local pipeline-lab clone and uv (owner's Mac only)",
)
def test_dryrun_race1_t1_on_pipeline_lab():
    report = dryrun.dry_run(load_config("pipeline-lab"), RACE1 / "tickets", RACE1 / "answers")
    assert report["green"], report["tickets"]["T1"]["problems"]
