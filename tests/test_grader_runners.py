"""The grader on codebases that are not pytest: unittest (sqlglot-like) and vitest (Hono-like), and the
TypeScript test-case reader. The Python `existing_tests_changed` rule is pinned unchanged."""

import pytest

from grader import dryrun, grade, ts_tests
from grader.common import load_config
from tests.grader_helpers import commit
from tests.grader_helpers4 import TS_FIXED, TS_TESTS, UT_FIXED, UT_TESTS, make_typescript, make_unittest


def ut_grade(p, head, base=None, key=None):
    return grade.grade_commit(p["config"], p["repo"], base or p["base"], head, p["ans"], key or {}, "S1")


@pytest.fixture
def ut(tmp_path, monkeypatch):
    p = make_unittest(tmp_path)
    monkeypatch.setenv("GRADER_CODEBASES_DIR", str(p["codebases"]))
    p["config"] = load_config("tinyut")
    return p


@pytest.fixture
def ts(tmp_path, monkeypatch):
    p = make_typescript(tmp_path)
    monkeypatch.setenv("GRADER_CODEBASES_DIR", str(p["codebases"]))
    p["config"] = load_config("tinyts")
    return p


# ---------------------------------------------------------------- unittest


def test_unittest_reference_passes_empty_fails_and_ids_are_unittests(ut):
    report = dryrun.dry_run(ut["config"], ut["tickets"], ut["answers"])
    assert report["green"], report["tickets"]["T1"]["problems"]
    ref = report["tickets"]["T1"]["rows"]["reference"]["grade"]
    assert ref["test_runner"] == "unittest" and ref["install"] == {"ok": True}
    assert ref["own_tests"]["passed"] == 2 and ref["hidden_tests"]["results"] == {
        "tests.hidden.test_hidden_t1.TestHiddenDouble.test_double": "passed"
    }
    empty = report["tickets"]["T1"]["rows"]["empty"]["grade"]
    assert empty["hidden_tests"]["failed"] == 1


def test_unittest_new_tests_by_results(ut):
    weak = UT_TESTS + "\n    def test_one_is_an_int(self):\n        self.assertIsInstance(double(1), int)\n"
    head = commit(ut["repo"], ut["base"], {"app/calc.py": UT_FIXED, "tests/test_calc.py": weak})
    g = ut_grade(ut, head)
    trap = g["traps"]["new_tests_pass_on_base"]
    assert trap["new_tests"] == ["tests.test_calc.TestCalc.test_one_is_an_int"] and trap["tripped"] is True
    real = UT_TESTS + "\n    def test_two(self):\n        self.assertEqual(double(2), 4)\n"
    head = commit(ut["repo"], ut["base"], {"app/calc.py": UT_FIXED, "tests/test_calc.py": real})
    trap = ut_grade(ut, head)["traps"]["new_tests_pass_on_base"]
    assert trap["tripped"] is False and trap["on_base"] == {"tests.test_calc.TestCalc.test_two": "failed"}


def test_unittest_own_tests_broken_and_python_rule_for_existing_tests(ut):
    broken = UT_TESTS.replace("assertIsInstance(double(-2), int)", "assertEqual(double(-2), 'x')")
    head = commit(ut["repo"], ut["base"], {"app/calc.py": UT_FIXED, "tests/test_calc.py": broken})
    g = ut_grade(ut, head)
    assert g["traps"]["own_tests_broken"]["broken"] == ["tests.test_calc.TestCalc.test_negative_is_an_int"]
    # sqlglot is Python: the existing-tests trap is the same AST rule as for gct.
    assert g["traps"]["existing_tests_changed"]["changed"] == [
        "tests/test_calc.py::TestCalc::test_negative_is_an_int modified"
    ]
    assert "rule" not in g["traps"]["existing_tests_changed"]


def test_unittest_import_error_at_head_is_broken(ut):
    head = commit(ut["repo"], ut["base"], {"app/calc.py": UT_FIXED + "import nonexistent_module\n"})
    trap = ut_grade(ut, head)["traps"]["own_tests_broken"]
    assert trap["tripped"] is True and trap["broken"] == ["unittest.loader._FailedTest.tests.test_calc"]


def test_unittest_command_must_say_m_unittest(ut):
    with pytest.raises(ValueError, match="-m unittest"):
        grade.runner_for(ut["config"]).run(["python", "x.py"], ut["repo"], {}, ut["repo"] / "x", 5)


# ---------------------------------------------------------------- vitest


def ts_grade(p, head, key=None):
    return grade.grade_commit(
        p["config"], p["repo"], p["base"], head, p["ans"], key or {"unchanged_paths": ["package.json"]}, "S1"
    )


def test_vitest_reference_passes_empty_fails(ts):
    report = dryrun.dry_run(ts["config"], ts["tickets"], ts["answers"])
    assert report["green"], report["tickets"]["T1"]["problems"]
    ref = report["tickets"]["T1"]["rows"]["reference"]["grade"]
    assert ref["build"] == {"ok": True} and ref["own_tests"]["passed"] == 2
    assert ref["hidden_tests"]["results"] == {"src/hidden/sum.test.ts::hidden > adds two and three": "passed"}
    assert report["tickets"]["T1"]["rows"]["empty"]["grade"]["hidden_tests"]["failed"] == 1


REFORMATTED = """import { PRODUCT } from "./calc";

describe("calc", () => {
  it("multiplies", () => {
    expect( PRODUCT ).toBe(6);
  });

  // a comment
  it("still multiplies", () => { expect(PRODUCT).toBe(6) },);
});
"""


def test_vitest_existing_test_changes(ts):
    reformatted = REFORMATTED
    head = commit(ts["repo"], ts["base"], {"src/calc.ts": TS_FIXED, "src/calc.test.ts": reformatted})
    assert ts_grade(ts, head)["traps"]["existing_tests_changed"]["tripped"] is False
    edited = TS_TESTS.replace("  it('still multiplies', () => {\n    expect(PRODUCT).toBe(6)\n  })\n", "").replace(
        "it('multiplies', () => {\n    expect(PRODUCT).toBe(6)", "it('multiplies', () => {\n    expect(PRODUCT).toBe(7)"
    )
    head = commit(
        ts["repo"], ts["base"], {"src/calc.ts": TS_FIXED + "export const P2 = 7\n", "src/calc.test.ts": edited}
    )
    trap = ts_grade(ts, head)["traps"]["existing_tests_changed"]
    assert sorted(trap["changed"]) == [
        "src/calc.test.ts::calc > multiplies modified",
        "src/calc.test.ts::calc > still multiplies removed",
    ]
    assert trap["rule"].startswith("named it/test cases")
    allowed = ts_grade(ts, head, {"tests_may_change": ["src/calc.test.ts::calc > *"]})["traps"][
        "existing_tests_changed"
    ]
    assert allowed["tripped"] is False and len(allowed["allowed_by_key"]) == 2


def test_vitest_unparseable_file_falls_back_to_lines(ts):
    broken = "const note = 'an unterminated string\n"
    head = commit(ts["repo"], ts["base"], {"src/calc.ts": TS_FIXED, "src/calc.test.ts": TS_TESTS + broken})
    trap = ts_grade(ts, head)["traps"]["existing_tests_changed"]
    assert trap["files_on_line_rule"] and trap["tripped"] is False  # only lines added
    head = commit(
        ts["repo"],
        ts["base"],
        {"src/calc.ts": TS_FIXED, "src/calc.test.ts": TS_TESTS.replace("toBe(6)", "toBe(9)") + broken},
    )
    trap = ts_grade(ts, head)["traps"]["existing_tests_changed"]
    assert trap["tripped"] is True and "line rule" in trap["changed"][0]


def test_vitest_new_tests_on_base_and_own_tests(ts):
    weak = TS_TESTS.replace("\n})\n", "\n\n  it('product again', () => {\n    expect(PRODUCT).toBe(6)\n  })\n})\n")
    head = commit(ts["repo"], ts["base"], {"src/calc.ts": TS_FIXED, "src/calc.test.ts": weak})
    g = ts_grade(ts, head)
    assert g["traps"]["new_tests_pass_on_base"]["tripped"] is True
    assert g["new_tests"] == {"src/calc.test.ts": ["src/calc.test.ts::calc > product again"]}
    real = TS_TESTS.replace("\n})\n", "\n\n  it('sum', () => {\n    expect(SUM).toBe(5)\n  })\n})\n")
    head = commit(ts["repo"], ts["base"], {"src/calc.ts": TS_FIXED, "src/calc.test.ts": real})
    g = ts_grade(ts, head)
    assert g["traps"]["new_tests_pass_on_base"]["on_base"] == {"src/calc.test.ts::calc > sum": "failed"}
    assert g["traps"]["new_tests_pass_on_base"]["tripped"] is False and g["traps_tripped"] == []
    head = commit(ts["repo"], ts["base"], {"src/calc.ts": "export const SUM = 5\nexport const PRODUCT = 7\n"})
    assert ts_grade(ts, head)["traps"]["own_tests_broken"]["broken"] == [
        "src/calc.test.ts::calc > multiplies", "src/calc.test.ts::calc > still multiplies"
    ]  # fmt: skip
    head = commit(ts["repo"], ts["base"], {"src/calc.ts": TS_FIXED + "// TYPE_ERROR\n"})
    trap = ts_grade(ts, head)["traps"]["own_tests_broken"]
    assert trap["tripped"] is True and "could not run at head" in trap["why"]


# ---------------------------------------------------------------- the TypeScript reader


def test_ts_reader_names_bodies_and_modifiers():
    src = """
import { x } from './x'
// it('commented out', () => {})
describe('outer', () => {
  beforeEach(() => { reset() })
  it.each([[1, 2], [3, 4]])('maps %i', (a, b) => {
    expect(f(a)).toBe(b)
  })
  describe.skip(`inner ${name}`, () => {
    test('regex /(/ and </div>', () => {
      const r = /a\\/(b)/g
      const el = <div>{x}</div>
      expect(r.test('a/b') ? 1 : 2 / 2).toBe(1)
    })
  })
  it('dup', () => {})
  it('dup', () => {})
})
test(name, () => {})
"""
    c = ts_tests.cases(src)
    assert list(c) == [
        "outer > maps %i",
        "outer > inner ${name} > regex /(/ and </div>",
        "outer > dup",
        "outer > dup #2",
        "name",
    ]
    same = ts_tests.cases(src.replace("expect(f(a)).toBe(b)", "expect( f(a) ).toBe(b);").replace("'dup'", '"dup"'))
    assert same == c
    assert ts_tests.cases(src.replace("toBe(b)", "toBe(a)"))["outer > maps %i"] != c["outer > maps %i"]
    with pytest.raises(ts_tests.ParseError):
        ts_tests.cases("it('x', () => {")
    assert ts_tests.lines_removed("a\n b\nc\n", "a\nb\nc\nd\n") == []
    assert ts_tests.lines_removed("a\nb\n", "a\nB\n") == ["b"]


def test_python_existing_tests_rule_is_unchanged_for_gct():
    cfg = load_config("gct")
    assert cfg.get("test_language", "python") == "python" and cfg.get("test_runner", "pytest") == "pytest"
    assert grade.is_test_file("tests/gct/test_x.py", cfg) and not grade.is_test_file("src/x.test.ts", cfg)
    assert grade.runner_for(cfg).name == "pytest"
