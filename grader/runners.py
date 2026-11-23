"""Test runners the grader can read, chosen by a codebase config's `test_runner`.

- `pytest` (default, gct and pipeline-lab): JUnit XML plus the short summary's node ids. Unchanged.
- `unittest` (sqlglot): the config's test command holds `-m unittest`; the grader swaps that for
  grader/unittest_json.py, run by the same interpreter, which writes every test's outcome as JSON.
  Test ids are unittest's dotted ids (`tests.test_x.TestX.test_y`).
- `vitest` (hono): the config's test command (for example `pnpm test`, which ends in `vp test --run`) gets
  `--reporter=json --outputFile=<file>` appended. Test ids are `<file>::<describe> > ... > <test>`.

Every runner returns the same counts: passed, failed, errors, skipped, exit_code, ok, failing_nodes
(ids to re-run), not_passing, `ran` (the tests got as far as running) and, for unittest and vitest,
`results` (id -> passed|failed|error|skipped) for the checks that work from results.
"""

import json
import os
import shutil
from pathlib import Path

from grader.common import run_cmd, tail

HERE = Path(__file__).resolve().parent


def finish(counts: dict, results: dict[str, str], code: int, out: str, produced: bool) -> dict:
    for status in results.values():
        key = {"passed": "passed", "failed": "failed", "error": "errors", "skipped": "skipped"}[status]
        counts[key] += 1
    bad = [k for k, v in results.items() if v in ("failed", "error")]
    counts["failing_nodes"] = bad[:500]
    counts["results"] = results
    counts["ran"] = produced and code in (0, 1)
    if not produced:
        counts["errors"] += 1
    if not counts["ran"] or counts["errors"]:
        counts["output_tail"] = tail(out)
    counts["ok"] = code == 0 and produced and counts["failed"] == 0 and counts["errors"] == 0 and counts["passed"] > 0
    if bad:
        counts["not_passing"] = bad[:50]
    return counts


class Pytest:
    name = "pytest"

    def run(self, cmd: list[str], cwd: Path, env: dict, out: Path, timeout: int, targets=()) -> dict:
        from grader.grade import pytest_counts

        return pytest_counts([*cmd, *targets], cwd, env, out.with_suffix(".xml"), timeout)

    def targets(self, ids) -> list[str]:
        return list(ids)

    def exists_on(self, repo, commit, node: str) -> bool:
        from grader.grade import node_exists

        return node_exists(repo, commit, node)

    def file_of(self, node: str, files) -> str | None:
        return node.partition("::")[0]

    def file_targets(self, files) -> list[str]:
        return list(files)


class Unittest:
    name = "unittest"

    def run(self, cmd: list[str], cwd: Path, env: dict, out: Path, timeout: int, targets=()) -> dict:
        if "unittest" not in cmd or cmd.index("unittest") == 0 or cmd[cmd.index("unittest") - 1] != "-m":
            raise ValueError(f"a unittest command must contain `-m unittest`: {cmd}")
        k = cmd.index("unittest")
        helper = out.parent / "unittest_json.py"
        if not helper.exists():
            shutil.copy(HERE / "unittest_json.py", helper)
        result = out.with_suffix(".json")
        result.unlink(missing_ok=True)
        args = list(targets) if targets else cmd[k + 1 :]
        r = run_cmd([*cmd[: k - 1], str(helper), "--out", str(result), *args], cwd=cwd, env=env, timeout=timeout)
        counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "exit_code": r["code"]}
        results: dict[str, str] = {}
        produced = result.exists()
        if produced:
            for t in json.loads(result.read_text(encoding="utf-8")).get("tests", []):
                results[t["id"]] = t["status"]
        return finish(counts, results, r["code"], r["out"] + r["err"], produced)

    def targets(self, ids) -> list[str]:
        return [i for i in ids if not i.startswith("unittest.loader.")]

    def module_file(self, node: str, files) -> str | None:
        name = node.removeprefix("unittest.loader._FailedTest.")
        parts = name.split(".")
        for k in range(len(parts), 0, -1):
            path = "/".join(parts[:k]) + ".py"
            if path in files:
                return path
        return None

    def exists_on(self, repo, commit, node: str) -> bool:
        from grader.grade import tree_files

        return self.module_file(node, set(tree_files(repo, commit))) is not None

    def file_of(self, node: str, files) -> str | None:
        return self.module_file(node, set(files))

    def file_targets(self, files) -> list[str]:
        return [f.removesuffix(".py").replace("/", ".") for f in files]


class Vitest:
    name = "vitest"

    def run(self, cmd: list[str], cwd: Path, env: dict, out: Path, timeout: int, targets=()) -> dict:
        result = out.with_suffix(".json")
        result.unlink(missing_ok=True)
        r = run_cmd([*cmd, *targets, "--reporter=json", f"--outputFile={result}"], cwd=cwd, env=env, timeout=timeout)
        counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "exit_code": r["code"]}
        results: dict[str, str] = {}
        produced = result.exists()
        if produced:
            root = os.path.realpath(cwd)
            for f in json.loads(result.read_text(encoding="utf-8")).get("testResults", []):
                rel = os.path.relpath(os.path.realpath(f.get("name", "")), root)
                cases = f.get("assertionResults") or []
                if f.get("status") == "failed" and not cases:
                    results[rel] = "error"  # the file itself failed (import, syntax, setup)
                for a in cases:
                    tid = f"{rel}::" + " > ".join([*(a.get("ancestorTitles") or []), a.get("title", "")])
                    status = {"passed": "passed", "failed": "failed"}.get(a.get("status"), "skipped")
                    if results.get(tid) not in ("failed", "error"):  # a file run by two projects: any failure counts
                        results[tid] = status
        return finish(counts, results, r["code"], r["out"] + r["err"], produced)

    def targets(self, ids) -> list[str]:
        return sorted({i.partition("::")[0] for i in ids})

    def exists_on(self, repo, commit, node: str) -> bool:
        from grader.grade import blob

        return blob(repo, commit, node.partition("::")[0]) is not None

    def file_of(self, node: str, files) -> str | None:
        return node.partition("::")[0]

    def file_targets(self, files) -> list[str]:
        return list(files)


RUNNERS = {"pytest": Pytest, "unittest": Unittest, "vitest": Vitest}


def runner_for(cfg: dict):
    name = cfg.get("test_runner", "pytest")
    if name not in RUNNERS:
        raise ValueError(f"unknown test_runner {name!r}; use one of {', '.join(RUNNERS)}")
    return RUNNERS[name]()
