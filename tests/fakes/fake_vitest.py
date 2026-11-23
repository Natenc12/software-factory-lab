"""A stand-in for `pnpm test` on a TypeScript repo, so the grader's vitest path runs in CI without Node.

    python fake_vitest.py [test files...] --reporter=json --outputFile=<file>

It finds the cases in `src/**/*.test.ts` (or the files given) with the grader's own reader, and a case
passes when every `expect(NAME).toBe(VALUE)` in it holds, NAME being an `export const NAME = VALUE` in
any file under src/. It writes vitest's JSON report shape and exits 1 if any case failed. A source file
containing TYPE_ERROR makes it fail like the type check before the tests: exit 2 and no report.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from grader.ts_tests import ParseError, cases  # noqa: E402

CONST_RE = re.compile(r"export const (\w+) = (\d+)")
EXPECT_RE = re.compile(r"expect \( (\w+) \) \. toBe \( (\d+) \)")


def main(argv: list[str]) -> int:
    out = next(a.split("=", 1)[1] for a in argv if a.startswith("--outputFile="))
    files = [a for a in argv if not a.startswith("--")]
    root = Path.cwd()
    consts = {}
    for f in sorted((root / "src").rglob("*.ts")):
        text = f.read_text()
        if "TYPE_ERROR" in text:
            print("error TS2322: fake type error", file=sys.stderr)
            return 2
        if not f.name.endswith(".test.ts"):
            consts.update({k: int(v) for k, v in CONST_RE.findall(text)})
    tests = [root / f for f in files] if files else sorted((root / "src").rglob("*.test.ts"))
    results, failed = [], False
    for f in tests:
        try:
            found = cases(f.read_text())
        except (OSError, ParseError) as e:
            results.append({"name": str(f.resolve()), "status": "failed", "message": str(e), "assertionResults": []})
            failed = True
            continue
        rows = []
        for name, body in found.items():
            *ancestors, title = name.split(" > ")
            ok = all(consts.get(k) == int(v) for k, v in EXPECT_RE.findall(body))
            failed = failed or not ok
            rows.append({"ancestorTitles": ancestors, "title": title, "fullName": " ".join(name.split(" > ")),
                         "status": "passed" if ok else "failed", "failureMessages": []})  # fmt: skip
        results.append({"name": str(f.resolve()), "status": "failed" if any(r["status"] == "failed" for r in rows) else "passed",
                        "message": "", "assertionResults": rows})  # fmt: skip
    Path(out).write_text(json.dumps({"success": not failed, "testResults": results}))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
