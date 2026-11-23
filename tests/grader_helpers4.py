"""Tiny practice codebases for the grader's other runners: unittest (Python) and vitest (TypeScript).

The TypeScript one is graded through tests/fakes/fake_vitest.py, which stands in for `pnpm test`.
"""

import json
import sys
from pathlib import Path

from tests.grader_helpers import G, commit, sh, write

FAKES = Path(__file__).parent / "fakes"

UT_BUGGY = "def double(n):\n    return n + n + 1\n"
UT_FIXED = "def double(n):\n    return n + n\n"
UT_TESTS = """import unittest

from app.calc import double


class TestCalc(unittest.TestCase):
    def test_zero_is_an_int(self):
        self.assertIsInstance(double(0), int)

    def test_negative_is_an_int(self):
        self.assertIsInstance(double(-2), int)
"""
UT_HIDDEN = """import unittest

from app.calc import double


class TestHiddenDouble(unittest.TestCase):
    def test_double(self):
        self.assertEqual([double(n) for n in (0, 1, 5)], [0, 2, 10])
"""

TS_BUGGY = "export const SUM = 4\nexport const PRODUCT = 6\n"
TS_FIXED = "export const SUM = 5\nexport const PRODUCT = 6\n"
TS_TESTS = """import { PRODUCT } from './calc'

describe('calc', () => {
  it('multiplies', () => {
    expect(PRODUCT).toBe(6)
  })

  it('still multiplies', () => {
    expect(PRODUCT).toBe(6)
  })
})
"""
TS_HIDDEN = """import { SUM } from '../calc'

describe('hidden', () => {
  it('adds two and three', () => {
    expect(SUM).toBe(5)
  })
})
"""


def make_repo(tmp: Path, name: str, files: dict) -> tuple[Path, str]:
    repo = tmp / name
    repo.mkdir()
    sh("git", "init", "-q", "-b", "main", cwd=repo)
    write(repo, files)
    sh(*G, "add", "-A", cwd=repo)
    sh(*G, "commit", "-qm", "base", cwd=repo)
    return repo, sh("git", "rev-parse", "HEAD", cwd=repo)


def packages(tmp: Path, codebase: str, cfg: dict, hidden: dict, key: dict, base: str, fix_patch: str) -> dict:
    codebases = tmp / "codebases"
    codebases.mkdir(exist_ok=True)
    (codebases / f"{codebase}.json").write_text(json.dumps(cfg))
    pkg = tmp / "tickets" / codebase / "T1"
    pkg.mkdir(parents=True)
    (pkg / "S1.md").write_text("# fixture\n")
    meta = {"id": "T1", "repo": cfg["repo"], "base_ref": base, "db": "none", "deliverable": "pull_request",
            "spec_words": {"S1": 2}}  # fmt: skip
    (pkg / "meta.json").write_text(json.dumps(meta))
    ans = tmp / "answers" / codebase / "T1"
    (ans / "hidden").mkdir(parents=True)
    for n, text in hidden.items():
        (ans / "hidden" / n).write_text(text)
    (ans / "key.json").write_text(json.dumps(key))
    (ans / "reference.patch").write_text(fix_patch)
    return {"codebases": codebases, "tickets": tmp / "tickets", "answers": tmp / "answers", "ans": ans, "cfg": cfg}


def make_unittest(tmp: Path) -> dict:
    repo, base = make_repo(
        tmp,
        "ut",
        {"app/__init__.py": "", "app/calc.py": UT_BUGGY, "tests/__init__.py": "", "tests/test_calc.py": UT_TESTS},
    )
    cfg = {
        "name": "tinyut",
        "repo": "example/tinyut",
        "local_clone": str(repo),
        "db": "none",
        "env": {"PATH": "{repo}/bin:{PATH}", "TINY_FLAG": "1"},
        "install": [["{python}", "-c", "import os; os.makedirs('bin', exist_ok=True)"]],
        "test_runner": "unittest",
        "test": ["{python}", "-m", "unittest"],
        "test_dirs": ["tests"],
        "hidden_dir": "tests/hidden",
        "hidden_test_cmd": "{python} -m unittest discover -s tests/hidden -t .",
        "timeout_seconds": 120,
    }
    fix = commit(repo, base, {"app/calc.py": UT_FIXED})
    patch = sh("git", "diff", base, fix, cwd=repo) + "\n"
    key = {"unchanged_paths": ["app/__init__.py"]}
    p = packages(tmp, "tinyut", cfg, {"__init__.py": "", "test_hidden_t1.py": UT_HIDDEN}, key, base, patch)
    return {**p, "repo": repo, "base": base}


def make_typescript(tmp: Path) -> dict:
    repo, base = make_repo(tmp, "ts", {"src/calc.ts": TS_BUGGY, "src/calc.test.ts": TS_TESTS, "package.json": "{}\n"})
    cfg = {
        "name": "tinyts",
        "repo": "example/tinyts",
        "local_clone": str(repo),
        "db": "none",
        "install": [["{python}", "-c", "pass"]],
        "build": [["{python}", "-c", "pass"]],
        "test_runner": "vitest",
        "test_language": "typescript",
        "test": [sys.executable, str(FAKES / "fake_vitest.py")],
        "test_dirs": ["src"],
        "hidden_dir": "src/hidden",
        "hidden_test_cmd": f"{sys.executable} {FAKES / 'fake_vitest.py'} src/hidden/sum.test.ts",
        "timeout_seconds": 120,
    }
    fix = commit(repo, base, {"src/calc.ts": TS_FIXED})
    patch = sh("git", "diff", base, fix, cwd=repo) + "\n"
    p = packages(tmp, "tinyts", cfg, {"sum.test.ts": TS_HIDDEN}, {"unchanged_paths": ["package.json"]}, base, patch)
    return {**p, "repo": repo, "base": base}
