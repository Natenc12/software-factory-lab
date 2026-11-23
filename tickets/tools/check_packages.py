"""Check every ticket and answer package of a codebase against the format in tickets/README.md.

    python3 tickets/tools/check_packages.py gct
    python3 tickets/tools/check_packages.py hono [--lab ~/repos/hono-lab]

Static checks (no database): required files exist, `meta.json` and `key.json` carry the fields the
format names, `spec_words` matches the ticket files, every reply in `replies.md` parses with the
harness's own parser and carries the ticket's prefix, and the latest `verify.json` is green.

With `--lab <clone of the practice repo>` it also applies each `reference.patch` to its `base_ref` in a
temporary worktree and checks that every existing test function the patch modifies or removes is
covered by `key.json`'s `tests_may_change` (a `path` or `path::name` pattern).

For hono (TypeScript, standard level S1 only, eight tickets: five replays, a feature, a vague request
and a wrong request) the same checks apply with Hono's layout: hidden tests are `*.test.ts(x)`, and an
existing test is an `it(...)` / `test(...)` block in a `*.test.ts(x)` file, compared as text with
whitespace collapsed; as in the grader, a `runTest(...)` call and its skip list are data, not a test.

Exits 1 and lists every problem it finds.

Each codebase has a profile (`PROFILES`): its ticket ids, their kinds, the spec levels written, and
whether it has S3 branches, a review ticket and a vague ticket. gct is the original set of twelve;
sqlglot has eight tickets at S1 only (no S0, S2, S3, no acceptance tests, no review ticket).
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from harness.owner import parse_sheet  # noqa: E402

META_KEYS = {"id", "kind", "title", "repo", "base_ref", "s3_base_ref", "db", "deliverable", "spec_words"}
KEY_KEYS = {"hidden_test_cmd", "unchanged_paths", "scope_out_paths", "traps", "planted_bugs", "not_bugs"}
KINDS = {"T1": "replay", "T2": "replay", "T3": "replay", "T4": "feature", "T5": "vague", "T6": "flawed"}
KINDS.update({"T7": "migration", "T8": "review", "T9": "feature", "T10": "feature"})
KINDS.update({"T11": "flawed", "T12": "flawed"})
TICKETS = [f"T{i}" for i in range(1, 13)]

PROFILES = {
    "gct": {"tickets": TICKETS, "kinds": KINDS, "levels": ["S0", "S1", "S2", "S3"], "s3": True,
            "review": "T8", "vague": "T5"},
    "sqlglot": {
        "tickets": [f"T{i}" for i in range(1, 9)],
        "kinds": {**{f"T{i}": "replay" for i in range(1, 6)}, "T6": "feature", "T7": "vague", "T8": "flawed"},
        "levels": ["S1"], "s3": False, "review": None, "vague": "T7",
    },
}  # fmt: skip


HONO_KINDS = {"T1": "replay", "T2": "replay", "T3": "replay", "T4": "replay", "T5": "replay"}
HONO_KINDS.update({"T6": "feature", "T7": "vague", "T8": "flawed"})
HONO_META_KEYS = {"id", "kind", "title", "repo", "db", "base_ref", "base_commit", "deliverable", "spec_words"}
HONO_KEY_KEYS = {"hidden_test_cmd", "unchanged_paths", "scope_out_paths", "traps", "tests_may_change"}


def check_hono() -> list[str]:
    problems: list[str] = []
    tdir, adir = ROOT / "tickets" / "hono", ROOT / "answers" / "hono"
    for tid, kind in HONO_KINDS.items():
        t, a = tdir / tid, adir / tid
        for name in ["S1.md", "meta.json"]:
            if not (t / name).is_file():
                problems.append(f"{tid}: missing tickets/hono/{tid}/{name}")
        for name in ["reference.patch", "key.json", "replies.md", "verify.json"]:
            if not (a / name).is_file():
                problems.append(f"{tid}: missing answers/hono/{tid}/{name}")
        if not [f for f in (a / "hidden").glob("*") if f.name.endswith((".test.ts", ".test.tsx"))]:
            problems.append(f"{tid}: no hidden tests")
        if not list(a.glob("naive*.patch")):
            problems.append(f"{tid}: no naive patch")
        if not (t / "meta.json").is_file() or not (a / "key.json").is_file():
            continue
        meta = json.loads((t / "meta.json").read_text())
        key = json.loads((a / "key.json").read_text())
        if missing := HONO_META_KEYS - set(meta):
            problems.append(f"{tid}: meta.json lacks {sorted(missing)}")
        if missing := HONO_KEY_KEYS - set(key):
            problems.append(f"{tid}: key.json lacks {sorted(missing)}")
        if meta.get("id") != tid or meta.get("kind") != kind:
            problems.append(f"{tid}: meta id/kind is {meta.get('id')}/{meta.get('kind')}")
        if meta.get("base_ref") != f"base/{tid}" or meta.get("deliverable") != "pull_request":
            problems.append(f"{tid}: base_ref or deliverable is off")
        others = sorted(f.name for f in t.glob("S*.md") if f.name != "S1.md")
        if others:
            problems.append(f"{tid}: hono tickets are S1 only, found {others}")
        want = len((t / "S1.md").read_text().split()) if (t / "S1.md").exists() else None
        if meta.get("spec_words") != {"S1": want}:
            problems.append(f"{tid}: spec_words is {meta.get('spec_words')}, S1.md says {want}")
        if kind == "replay" and not key.get("source", {}).get("fix"):
            problems.append(f"{tid}: key.json needs source.fix for a replay")
        if kind == "vague" and not key.get("open_decision"):
            problems.append(f"{tid}: key.json needs open_decision")
        if kind == "flawed" and not key.get("flaw"):
            problems.append(f"{tid}: key.json needs flaw")
        problems += _check_replies(tid, a)
        if (a / "verify.json").is_file() and not json.loads((a / "verify.json").read_text()).get("ok"):
            problems.append(f"{tid}: verify.json is not green")
    return problems


def _check_replies(tid: str, a: Path) -> list[str]:
    problems: list[str] = []
    if (a / "replies.md").is_file():
        try:
            replies = parse_sheet(a / "replies.md")
        except ValueError as exc:
            return [f"{tid}: replies.md does not parse: {exc}"]
        bad = [r["id"] for r in replies if not r["id"].startswith(f"{tid}-")]
        if bad:
            problems.append(f"{tid}: reply ids without the {tid}- prefix: {bad}")
        if replies and not any(r["when"] for r in replies):
            problems.append(f"{tid}: replies have no When: rules")
    return problems


def _matching_close(src: str, start: int) -> int:
    """Index of the bracket closing the one at `start`, skipping strings, template text and comments."""
    depth, i = 0, start
    while i < len(src):
        ch = src[i]
        if ch in "'\"`":
            i += 1
            while i < len(src) and src[i] != ch:
                i += 2 if src[i] == "\\" else 1
        elif src.startswith("//", i):
            i = src.find("\n", i)
            if i < 0:
                return len(src) - 1
        elif src.startswith("/*", i):
            i = src.find("*/", i) + 1
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(src) - 1


def _ts_blocks(src: str) -> dict[str, str]:
    """`title` -> the `it`/`test` call's text with whitespace collapsed. Titles repeat; later ones get #n."""
    out: dict[str, str] = {}
    for m in re.finditer(r"\b(it|test)(\.each\([\s\S]*?\)\s*)?\(\s*(['\"`])((?:\\.|(?!\3).)*)\3", src):
        start = src.index("(", m.start() + len(m.group(1)) + len(m.group(2) or ""))
        i = _matching_close(src, start)
        name = m.group(4)
        key, n = name, 1
        while key in out:
            n += 1
            key = f"{name}#{n}"
        out[key] = " ".join(src[m.start() : i + 1].split())
    return out


def check(codebase: str) -> list[str]:
    problems: list[str] = []
    tdir, adir = ROOT / "tickets" / codebase, ROOT / "answers" / codebase
    prof = PROFILES.get(codebase, PROFILES["gct"])
    kinds = prof["kinds"]
    for tid in prof["tickets"]:
        t, a = tdir / tid, adir / tid
        review = tid == prof["review"]
        levels = ["S1"] if review else prof["levels"]
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
        if meta.get("id") != tid or meta.get("kind") != kinds[tid]:
            problems.append(f"{tid}: meta id/kind is {meta.get('id')}/{meta.get('kind')}")
        if meta.get("base_ref") != f"base/{tid}":
            problems.append(f"{tid}: base_ref is {meta.get('base_ref')}")
        want_s3 = None if review or not prof["s3"] else f"base/{tid}-s3"
        if meta.get("s3_base_ref") != want_s3:
            problems.append(f"{tid}: s3_base_ref is {meta.get('s3_base_ref')}, want {want_s3}")
        if meta.get("deliverable") != ("review_report" if review else "pull_request"):
            problems.append(f"{tid}: deliverable is {meta.get('deliverable')}")
        for lvl in ("S0", "S1", "S2", "S3"):
            f = t / f"{lvl}.md"
            want = len(f.read_text().split()) if f.exists() else None
            if meta.get("spec_words", {}).get(lvl) != want:
                problems.append(f"{tid}: spec_words[{lvl}] is {meta['spec_words'].get(lvl)}, files say {want}")
        if not review and prof["s3"] and not (a / "acceptance").is_dir():
            problems.append(f"{tid}: no acceptance tests for base/{tid}-s3")
        if tid == prof["vague"] and not key.get("open_decision"):
            problems.append(f"{tid}: key.json needs open_decision")
        if kinds[tid] == "flawed" and not key.get("flaw"):
            problems.append(f"{tid}: key.json needs flaw")
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


def _test_functions(src: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            out[node.name] = ast.dump(node)
        elif isinstance(node, ast.ClassDef):
            for m in node.body:
                if isinstance(m, ast.FunctionDef | ast.AsyncFunctionDef):
                    out[f"{node.name}::{m.name}"] = ast.dump(m)
    return out


def touched_existing_tests(lab: Path, base_ref: str, patch: Path) -> list[str]:
    """`path::name` of every function in an existing test file that `patch` modifies or removes."""
    touched: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        wt = Path(tmp) / "wt"
        subprocess.run(["git", "-C", str(lab), "worktree", "add", "-q", "--detach", str(wt), base_ref], check=True)
        try:
            subprocess.run(["git", "apply", str(patch)], cwd=wt, check=True)
            changed = subprocess.run(["git", "diff", "--name-only"], cwd=wt, capture_output=True, text=True)
            for path in changed.stdout.split():
                ts = path.endswith((".test.ts", ".test.tsx"))
                if not ts and not (path.startswith("tests/") and path.endswith(".py")):
                    continue
                old = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=wt, capture_output=True, text=True).stdout
                new = (wt / path).read_text() if (wt / path).exists() else ""
                parse = _ts_blocks if ts else _test_functions
                before, after = parse(old), parse(new)
                if ts:
                    # Titles repeat (`it.each(...)('%s', ...)`), so a block counts as changed only when
                    # its text is gone from the new file, not when a new block shifts the numbering.
                    remaining = set(after.values())
                    touched += [f"{path}::{n}" for n, text in before.items() if text not in remaining]
                    continue
                touched += [f"{path}::{n}" for n, dump in before.items() if after.get(n) != dump]
        finally:
            subprocess.run(["git", "-C", str(lab), "worktree", "remove", "--force", str(wt)], check=False)
    return touched


def check_tests_may_change(codebase: str, lab: Path) -> list[str]:
    problems: list[str] = []
    if codebase == "hono":
        tickets = list(HONO_KINDS)
    else:
        prof = PROFILES.get(codebase, PROFILES["gct"])
        tickets = [t for t in prof["tickets"] if t != prof["review"]]
    for tid in tickets:
        meta = json.loads((ROOT / "tickets" / codebase / tid / "meta.json").read_text())
        key = json.loads((ROOT / "answers" / codebase / tid / "key.json").read_text())
        if "tests_may_change" not in key:
            problems.append(f"{tid}: key.json lacks tests_may_change")
            continue
        allowed = key["tests_may_change"]
        patch = ROOT / "answers" / codebase / tid / "reference.patch"
        for name in touched_existing_tests(lab, meta["base_ref"], patch):
            path = name.split("::")[0]
            title = name.split("::", 1)[1].split("#")[0] if "::" in name else ""
            if not any(
                fnmatch.fnmatch(name, a)
                or name == a
                or path == a
                or path.startswith(a.rstrip("/") + "/")
                or fnmatch.fnmatch(path, a)
                or (a.startswith(path + "::") and a.endswith(" > " + title))
                for a in allowed
            ):
                problems.append(f"{tid}: reference.patch changes {name}, not in tests_may_change")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("codebase", nargs="?", default="gct")
    ap.add_argument("--lab", help="local clone of the practice repo, to check tests_may_change")
    args = ap.parse_args(argv)
    codebase = args.codebase
    problems = check_hono() if codebase == "hono" else check(codebase)
    if args.lab:
        problems += check_tests_may_change(codebase, Path(args.lab).expanduser())
    for p in problems:
        print(p)
    print(f"{codebase}: {'OK' if not problems else f'{len(problems)} problem(s)'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
