"""Check every ticket and answer package of a codebase against the format in tickets/README.md.

    python3 tickets/tools/check_packages.py gct

Static checks only (no database, no practice repo): required files exist, `meta.json` and
`key.json` carry the fields the format names, `spec_words` matches the ticket files, every reply in
`replies.md` parses with the harness's own parser and carries the ticket's prefix, and the latest
`verify.json` is green. Exits 1 and lists every problem it finds.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from harness.owner import parse_sheet  # noqa: E402

META_KEYS = {"id", "kind", "title", "repo", "base_ref", "s3_base_ref", "db", "deliverable", "spec_words"}
KEY_KEYS = {"hidden_test_cmd", "unchanged_paths", "scope_out_paths", "traps", "planted_bugs", "not_bugs"}
KINDS = {"T1": "replay", "T2": "replay", "T3": "replay", "T4": "feature", "T5": "vague", "T6": "flawed"}
KINDS.update({"T7": "migration", "T8": "review"})


def check(codebase: str) -> list[str]:
    problems: list[str] = []
    tdir, adir = ROOT / "tickets" / codebase, ROOT / "answers" / codebase
    for tid in [f"T{i}" for i in range(1, 9)]:
        t, a = tdir / tid, adir / tid
        review = tid == "T8"
        levels = ["S1"] if review else ["S0", "S1", "S2", "S3"]
        for name in [*(f"{lvl}.md" for lvl in levels), "meta.json"]:
            if not (t / name).is_file():
                problems.append(f"{tid}: missing tickets/{codebase}/{tid}/{name}")
        for name in ["reference.patch", "key.json", "replies.md", "verify.json"]:
            if not (a / name).is_file():
                problems.append(f"{tid}: missing answers/{codebase}/{tid}/{name}")
        if not list((a / "hidden").glob("test_hidden_*.py")):
            problems.append(f"{tid}: no hidden tests")
        if not (t / "meta.json").is_file() or not (a / "key.json").is_file():
            continue
        meta = json.loads((t / "meta.json").read_text())
        key = json.loads((a / "key.json").read_text())
        if missing := META_KEYS - set(meta):
            problems.append(f"{tid}: meta.json lacks {sorted(missing)}")
        if missing := KEY_KEYS - set(key):
            problems.append(f"{tid}: key.json lacks {sorted(missing)}")
        if meta.get("id") != tid or meta.get("kind") != KINDS[tid]:
            problems.append(f"{tid}: meta id/kind is {meta.get('id')}/{meta.get('kind')}")
        if meta.get("base_ref") != f"base/{tid}":
            problems.append(f"{tid}: base_ref is {meta.get('base_ref')}")
        want_s3 = None if review else f"base/{tid}-s3"
        if meta.get("s3_base_ref") != want_s3:
            problems.append(f"{tid}: s3_base_ref is {meta.get('s3_base_ref')}, want {want_s3}")
        if meta.get("deliverable") != ("review_report" if review else "pull_request"):
            problems.append(f"{tid}: deliverable is {meta.get('deliverable')}")
        for lvl in ("S0", "S1", "S2", "S3"):
            f = t / f"{lvl}.md"
            want = len(f.read_text().split()) if f.exists() else None
            if meta.get("spec_words", {}).get(lvl) != want:
                problems.append(f"{tid}: spec_words[{lvl}] is {meta['spec_words'].get(lvl)}, files say {want}")
        if not review and not (a / "acceptance").is_dir():
            problems.append(f"{tid}: no acceptance tests for base/{tid}-s3")
        if tid == "T5" and not key.get("open_decision"):
            problems.append("T5: key.json needs open_decision")
        if tid == "T6" and not key.get("flaw"):
            problems.append("T6: key.json needs flaw")
        if review and len(key.get("planted_bugs", [])) != 3:
            problems.append("T8: key.json needs exactly 3 planted_bugs")
        if review and {b.get("visible") for b in key.get("planted_bugs", [])} != {"diff", "edge case", "only when run"}:
            problems.append("T8: planted bugs must be one each of diff / edge case / only when run")
        if (a / "replies.md").is_file():
            try:
                replies = parse_sheet(a / "replies.md")
            except ValueError as exc:
                problems.append(f"{tid}: replies.md does not parse: {exc}")
                replies = []
            bad = [r["id"] for r in replies if not r["id"].startswith(f"{tid}-")]
            if bad:
                problems.append(f"{tid}: reply ids without the {tid}- prefix: {bad}")
            if replies and not any(r["when"] for r in replies):
                problems.append(f"{tid}: replies have no When: rules")
        if (a / "verify.json").is_file() and not json.loads((a / "verify.json").read_text()).get("ok"):
            problems.append(f"{tid}: verify.json is not green")
    return problems


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    codebase = argv[0] if argv else "gct"
    problems = check(codebase)
    for p in problems:
        print(p)
    print(f"{codebase}: {'OK' if not problems else f'{len(problems)} problem(s)'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
