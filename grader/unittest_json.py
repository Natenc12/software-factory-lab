"""Run unittest like `python -m unittest ...` and write every test's outcome as JSON.

    <python> unittest_json.py --out results.json [unittest arguments: names, files or `discover ...`]

Standard library only, so it runs under the practice repo's own interpreter (the grader copies it
outside the repo and calls it in place of `-m unittest`). The JSON is
`{"tests": [{"id": ..., "status": passed|failed|error|skipped, "message": ...}], "successful": bool}`.
A module that fails to import is reported by unittest itself as a test named
`unittest.loader._FailedTest.<module>` with status `error`. Exit code 0 when every test passed, else 1.
"""

import json
import sys
import unittest

RANK = {"passed": 0, "skipped": 0, "failed": 2, "error": 3}


class Recorder(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes: dict[str, dict] = {}

    def _put(self, test, status, err=None):
        tid = test.id()
        old = self.outcomes.get(tid)
        if old and RANK[old["status"]] >= RANK[status]:
            return
        message = self._exc_info_to_string(err, test)[-2000:] if err else ""
        self.outcomes[tid] = {"id": tid, "status": status, "message": message}

    def addSuccess(self, test):
        super().addSuccess(test)
        self._put(test, "passed")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._put(test, "failed", err)

    def addError(self, test, err):
        super().addError(test, err)
        self._put(test, "error", err)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._put(test, "skipped")

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self._put(test, "passed")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self._put(test, "failed")

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            failed = issubclass(err[0], test.failureException)
            self._put(test, "failed" if failed else "error", err)


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] != "--out":
        print("usage: unittest_json.py --out results.json [unittest arguments]", file=sys.stderr)
        return 2
    out, args = argv[1], argv[2:]
    runner = unittest.TextTestRunner(resultclass=Recorder, verbosity=0)
    sys.path.insert(0, "")
    program = unittest.main(module=None, argv=["python -m unittest", *args], testRunner=runner, exit=False)
    result = program.result
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"tests": list(result.outcomes.values()), "successful": result.wasSuccessful()}, f)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
