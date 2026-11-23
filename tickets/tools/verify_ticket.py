"""Prove one ticket by script: its hidden tests fail on the starting code and pass with the reference fix.

    python3 tickets/tools/verify_ticket.py gct T1 [--lab ~/repos/gct-lab] [--keep]

For one ticket it:

1. checks out `base_ref` in a temporary worktree of the practice repo, with its own new Postgres
   database (named `author_...`, `vector` extension created, migrations applied twice);
2. shows the app's existing tests pass there (`CI=1`, so a database test fails instead of skipping);
3. copies `answers/<codebase>/<T>/hidden/*.py` into `tests/hidden/` and shows every hidden test fails;
4. applies `reference.patch` on a fresh database and shows the hidden tests and the existing tests all
   pass, lint and format are clean, and no path in `key.json`'s `unchanged_paths` changed;
5. for each `naive*.patch` (a careless but competent fix), shows at least one hidden test fails with it
   while the existing tests still pass;
6. for a ticket with `s3_base_ref`: checks the S3 branch is `base_ref` plus one commit that only adds
   tests, shows those acceptance tests fail on the S3 branch, pass with the reference fix, and pass with
   `naive-s3.patch` (or `naive.patch`) while at least one hidden test still fails, so the hidden tests
   check beyond them;
7. removes the worktree and drops every database it made.

It writes `answers/<codebase>/<T>/verify.json` and exits 0 only if every check passed.
Standard library only, plus `git`, `uv` and `psql` on PATH.

Codebases other than gct (sqlglot so far) take their commands from the grader's config,
`grader/codebases/<codebase>.json`: its `env`, `install` (run in each checkout, which keeps its
virtual environment in the repo folder), `test` (a pytest command), `lint` and `hidden_dir`. They have
no database, so step 1 makes none, and there are no migrations. The practice clone defaults to
`~/repos/<codebase>-lab`.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST_CMD = ["uv", "run", "--locked", "pytest", "-q", "-m", "not live", "-p", "no:cacheprovider"]


def sh(cmd: list[str], cwd: Path | None = None, env: dict | None = None, timeout: int = 1800, check: bool = True):
    out = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    if check and out.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed ({out.returncode}):\n{out.stdout[-3000:]}\n{out.stderr[-3000:]}")
    return out


# ---------- Postgres ----------


def psql(sql: str, db: str = "postgres") -> str:
    return sh(["psql", "-X", "-q", "-At", "-v", "ON_ERROR_STOP=1", "-d", db, "-c", sql]).stdout.strip()


def pg_url(name: str) -> str:
    sock = psql("SHOW unix_socket_directories").split(",")[0].strip()
    port = psql("SHOW port")
    return f"postgresql:///{name}?host={sock}&port={port}"


def create_db(name: str) -> str:
    assert name.startswith("author_"), name
    psql(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
    psql(f'CREATE DATABASE "{name}"')
    psql("CREATE EXTENSION IF NOT EXISTS vector", db=name)
    return pg_url(name)


def drop_db(name: str) -> None:
    assert name.startswith("author_"), name
    psql(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


# ---------- pytest results ----------


def junit_outcomes(path: Path) -> dict[str, str]:
    """Map each test id (file::name) to passed / failed / error / skipped. A collection error is keyed by file."""
    if not path.exists():
        return {}
    outcomes: dict[str, str] = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        cls, name = case.get("classname", ""), case.get("name", "")
        file = case.get("file") or (cls.replace(".", "/") + ".py" if cls else "")
        key = f"{cls}::{name}" if cls else name
        state = "passed"
        for child in case:
            if child.tag in ("failure", "error"):
                state = "failed" if child.tag == "failure" else "error"
            elif child.tag == "skipped" and state == "passed":
                state = "skipped"
        outcomes[key] = state
        if not cls and file:
            outcomes[key] = state
    return outcomes


def run_pytest(wt: Path, env: dict, args: list[str], tag: str, cmd: list[str] | None = None) -> dict:
    xml = wt.parent / f"junit-{tag}.xml"
    xml.unlink(missing_ok=True)
    t0 = time.time()
    base_cmd = cmd if cmd is not None else TEST_CMD
    out = sh(base_cmd + [f"--junitxml={xml}", *args], cwd=wt, env=env, check=False, timeout=3600)
    outcomes = junit_outcomes(xml)
    counts: dict[str, int] = {}
    for state in outcomes.values():
        counts[state] = counts.get(state, 0) + 1
    tail = (out.stdout.strip().splitlines() or [""])[-1]
    return {
        "exit": out.returncode,
        "counts": counts,
        "outcomes": outcomes,
        "summary": tail,
        "seconds": round(time.time() - t0, 1),
        "log_tail": "" if out.returncode == 0 else (out.stdout[-4000:] + out.stderr[-2000:]),
    }


def hidden_outcomes(res: dict) -> dict[str, str]:
    return {k: v for k, v in res["outcomes"].items() if "hidden" in k.split("::")[0]}


def collect_ids(wt: Path, env: dict, paths: list[str], cmd: list[str] | None = None) -> list[str]:
    out = sh((cmd if cmd is not None else TEST_CMD) + ["--collect-only", *paths], cwd=wt, env=env, check=False)
    return [line.strip() for line in out.stdout.splitlines() if "::" in line]


# ---------- worktree ----------


class Tree:
    def __init__(self, lab: Path, root: Path, name: str):
        self.lab, self.path = lab, root / name
        sh(["git", "-C", str(lab), "worktree", "add", "--detach", str(self.path), "HEAD"])

    def reset(self, ref: str) -> None:
        sh(["git", "checkout", "-q", "-f", "--detach", ref], cwd=self.path)
        sh(["git", "clean", "-q", "-fdx", "-e", ".venv"], cwd=self.path)

    def apply(self, patch: Path) -> None:
        sh(["git", "apply", "--whitespace=nowarn", str(patch)], cwd=self.path)

    def changed(self) -> list[str]:
        out = sh(["git", "status", "--porcelain", "--untracked-files=all"], cwd=self.path).stdout
        return sorted(line[3:].strip() for line in out.splitlines() if line.strip())

    def add_hidden(self, hidden: Path, hidden_dir: str = "tests/hidden") -> list[str]:
        dest = self.path / hidden_dir
        dest.mkdir(parents=True, exist_ok=True)
        names = []
        for f in sorted(hidden.glob("*.py")):
            shutil.copy2(f, dest / f.name)
            names.append(f"{hidden_dir}/{f.name}")
        return names

    def remove(self) -> None:
        sh(["git", "-C", str(self.lab), "worktree", "remove", "--force", str(self.path)], check=False)


# ---------- the checks ----------


class Verifier:
    def __init__(self, codebase: str, tid: str, lab: Path, keep: bool):
        self.codebase, self.tid, self.lab, self.keep = codebase, tid, lab, keep
        self.tdir = ROOT / "tickets" / codebase / tid
        self.adir = ROOT / "answers" / codebase / tid
        self.meta = json.loads((self.tdir / "meta.json").read_text())
        self.key = json.loads((self.adir / "key.json").read_text())
        self.hidden = self.adir / "hidden"
        self.ref_patch = self.adir / "reference.patch"
        self.naive_patch = self.adir / "naive.patch"
        self.dbs: list[str] = []
        self.steps: list[dict] = []
        self.tmp = Path(tempfile.mkdtemp(prefix=f"verify-{tid}-"))
        self.env_base = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "OPENAI_API_KEY")}
        # Codebases other than gct: commands from the grader's config, no database.
        self.cfg = None
        if codebase != "gct":
            self.cfg = json.loads((ROOT / "grader" / "codebases" / f"{codebase}.json").read_text())
        self.hidden_dir = (self.cfg or {}).get("hidden_dir", "tests/hidden")
        self.test_cmd = list(self.cfg["test"]) + ["-p", "no:cacheprovider"] if self.cfg else None
        # UV_PYTHON matches the practice repo's own CI. gct-lab does not compile on Python 3.13+ (a lone
        # surrogate in a docstring), and with no .python-version uv would otherwise pick the newest one.
        if self.cfg:
            self.env_base.update({k: str(v) for k, v in (self.cfg.get("env") or {}).items()})
        else:
            self.env_base.update(
                {
                    "CI": "1",
                    "OPENAI_API_KEY": "",
                    "GCT_STAGING_DIR": str(self.tmp / "staging"),
                    "UV_PYTHON": os.environ.get("VERIFY_UV_PYTHON", "3.10"),
                }
            )

    def step(self, name: str, ok: bool, **detail) -> bool:
        self.steps.append({"name": name, "ok": bool(ok), **detail})
        mark = "ok  " if ok else "FAIL"
        print(f"[{mark}] {self.tid} {name} {detail.get('note', '')}", flush=True)
        return ok

    def fresh_db(self, phase: str) -> dict:
        if self.cfg:
            return dict(self.env_base)
        name = f"author_{self.codebase}_{self.tid.lower()}_{phase}_{os.getpid()}"
        url = create_db(name)
        self.dbs.append(name)
        return {**self.env_base, "DATABASE_URL": url}

    def prepare(self, tree: Tree, ref: str, phase: str, patch: Path | None = None) -> dict:
        tree.reset(ref)
        if patch is not None:
            tree.apply(patch)
        env = self.fresh_db(phase)
        if self.cfg:
            if self.cfg.get("install"):
                sh(list(self.cfg["install"]), cwd=tree.path, env=env)
            return env
        sh(["uv", "sync", "--locked", "--extra", "dev", "-q"], cwd=tree.path, env=env)
        for _ in range(2):
            sh(["uv", "run", "--locked", "python", "scripts/migrate.py"], cwd=tree.path, env=env)
        return env

    def pytest(self, tree: Tree, env: dict, args: list[str], tag: str) -> dict:
        return run_pytest(tree.path, env, args, tag, self.test_cmd)

    def lint_cmds(self, files: list[str] | None = None) -> list[list[str]]:
        """The tree's lint commands, or with `files` the same checks on those files only."""
        if self.cfg:
            cmds = [list(c) for c in self.cfg.get("lint") or []]
            return [[*c, *files] for c in cmds] if files else cmds
        if files:
            return [
                ["uv", "run", "--locked", "ruff", "check", *files],
                ["uv", "run", "--locked", "ruff", "format", "--check", *files],
            ]
        return [["uv", "run", "--locked", "ruff", "check"], ["uv", "run", "--locked", "ruff", "format", "--check", "."]]

    def resolve(self, ref: str) -> str:
        return sh(["git", "-C", str(self.lab), "rev-parse", "--verify", f"{ref}^{{commit}}"]).stdout.strip()

    def run(self) -> dict:
        started = datetime.now(UTC).isoformat(timespec="seconds")
        base_ref = self.meta["base_ref"]
        s3_ref = self.meta.get("s3_base_ref")
        result = {
            "ticket": self.tid,
            "codebase": self.codebase,
            "repo": self.meta.get("repo"),
            "base_ref": base_ref,
            "base_sha": self.resolve(base_ref),
            "s3_base_ref": s3_ref,
            "s3_sha": self.resolve(s3_ref) if s3_ref else None,
            "started": started,
        }
        tree = Tree(self.lab, self.tmp, "wt")
        try:
            self.check_base(tree, base_ref)
            self.check_reference(tree, base_ref)
            for patch in sorted(self.adir.glob("naive*.patch")):
                self.check_naive(tree, base_ref, patch)
            if s3_ref:
                self.check_s3(tree, base_ref, s3_ref)
        except Exception as exc:  # a crash is a failed check, recorded, never a silent pass
            self.step("crash", False, note=str(exc)[:4000])
        finally:
            tree.remove()
            for name in self.dbs:
                try:
                    drop_db(name)
                except Exception as exc:
                    self.step("drop-db", False, note=f"{name}: {exc}")
            if not self.keep:
                shutil.rmtree(self.tmp, ignore_errors=True)
        result["finished"] = datetime.now(UTC).isoformat(timespec="seconds")
        result["databases_dropped"] = self.dbs
        result["ok"] = all(s["ok"] for s in self.steps) and bool(self.steps)
        result["steps"] = self.steps
        return result

    def check_base(self, tree: Tree, base_ref: str) -> None:
        env = self.prepare(tree, base_ref, "base")
        res = self.pytest(tree, env, [], "base-existing")
        ok = res["exit"] == 0 and res["counts"].get("passed", 0) > 0
        self.step(
            "base: existing tests pass",
            ok,
            note=res["summary"],
            counts=res["counts"],
            seconds=res["seconds"],
            log_tail=res["log_tail"],
        )
        files = tree.add_hidden(self.hidden, self.hidden_dir)
        self.step("hidden tests exist", bool(files), files=files)
        res = self.pytest(tree, env, [self.hidden_dir], "base-hidden")
        hid = hidden_outcomes(res)
        not_failing = sorted(k for k, v in hid.items() if v not in ("failed", "error"))
        self.base_hidden = hid
        self.step(
            "base: every hidden test fails",
            bool(hid) and not not_failing,
            note=res["summary"],
            outcomes=hid,
            not_failing=not_failing,
            seconds=res["seconds"],
        )

    def check_reference(self, tree: Tree, base_ref: str) -> None:
        env = self.prepare(tree, base_ref, "ref", self.ref_patch)
        changed = tree.changed()
        unchanged = self.key.get("unchanged_paths", [])
        touched = sorted(p for p in changed if any(p == u or p.startswith(u.rstrip("/") + "/") for u in unchanged))
        self.step("reference: leaves unchanged_paths alone", not touched, touched=touched, changed=changed)
        # Lint the patched tree as the app's CI does, before the hidden tests are copied in.
        self.tree_lint = []
        for cmd in self.lint_cmds():
            out = sh(cmd, cwd=tree.path, env=env, check=False)
            self.tree_lint.append(
                {"cmd": " ".join(cmd[-4:]), "exit": out.returncode, "tail": (out.stdout + out.stderr)[-1500:]}
            )
        hidden_files = tree.add_hidden(self.hidden, self.hidden_dir)
        ids = collect_ids(tree.path, env, [self.hidden_dir], self.test_cmd)
        self.hidden_ids = ids
        res = self.pytest(tree, env, [], "ref-all")
        hid = hidden_outcomes(res)
        bad = sorted(k for k, v in hid.items() if v != "passed")
        self.step(
            "reference: every hidden test passes",
            bool(hid) and not bad and len(hid) == len(ids),
            note=f"{len(hid)} hidden, {len(ids)} collected",
            outcomes=hid,
            not_passing=bad,
        )
        others = {k: v for k, v in res["outcomes"].items() if k not in hid}
        bad_other = sorted(k for k, v in others.items() if v in ("failed", "error"))
        self.step(
            "reference: existing tests pass",
            res["exit"] == 0 and not bad_other,
            note=res["summary"],
            counts=res["counts"],
            failing=bad_other,
            seconds=res["seconds"],
            log_tail=res["log_tail"],
        )
        # The base tree's ids must line up with the patched tree's, or "every hidden test fails" proved less.
        base_keys = set(self.base_hidden)
        missing = sorted(k for k in hid if k not in base_keys)
        collection_errors = [k for k, v in self.base_hidden.items() if v == "error" and "::" not in k]
        self.step(
            "base and reference ran the same hidden tests",
            not missing or bool(collection_errors),
            missing_on_base=missing,
            base_collection_errors=collection_errors,
        )
        outs = list(self.tree_lint)
        for cmd in self.lint_cmds(hidden_files):
            out = sh(cmd, cwd=tree.path, env=env, check=False)
            outs.append({"cmd": " ".join(cmd[-4:]), "exit": out.returncode, "tail": (out.stdout + out.stderr)[-1500:]})
        self.step(
            "reference: lint and format clean (tree and hidden tests)", all(o["exit"] == 0 for o in outs), runs=outs
        )
        t0 = time.time()
        res = self.pytest(tree, env, [self.hidden_dir], "ref-hidden-timing")
        secs = round(time.time() - t0, 1)
        self.step("hidden tests run in under about 2 minutes", res["exit"] == 0 and secs < 150, note=f"{secs}s")

    def check_naive(self, tree: Tree, base_ref: str, patch: Path) -> None:
        env = self.prepare(tree, base_ref, patch.stem.replace("-", "_"), patch)
        tree.add_hidden(self.hidden, self.hidden_dir)
        res = self.pytest(tree, env, [], f"{patch.stem}-all")
        hid = hidden_outcomes(res)
        failing = sorted(k for k, v in hid.items() if v in ("failed", "error"))
        others_bad = sorted(k for k, v in res["outcomes"].items() if k not in hid and v in ("failed", "error"))
        self.step(
            f"{patch.name}: at least one hidden test fails",
            bool(failing),
            failing=failing,
            note=f"{len(failing)}/{len(hid)} hidden fail",
        )
        self.step(f"{patch.name}: existing tests still pass (a competent fix)", not others_bad, failing=others_bad)

    def check_s3(self, tree: Tree, base_ref: str, s3_ref: str) -> None:
        base_sha, s3_sha = self.resolve(base_ref), self.resolve(s3_ref)
        parent = self.resolve(f"{s3_ref}^")
        added = sh(["git", "-C", str(self.lab), "diff", "--name-status", base_sha, s3_sha]).stdout.split("\n")
        added = [line.split("\t") for line in added if line.strip()]
        only_tests = all(st == "A" and p.startswith("tests/") for st, p in added)
        accept = [p for _, p in added]
        self.step(
            "s3: branch is base_ref plus one commit that only adds tests",
            parent == base_sha and only_tests and bool(accept),
            files=accept,
        )
        env = self.prepare(tree, s3_ref, "s3base")
        res = self.pytest(tree, env, accept, "s3-base")
        fails = res["counts"].get("failed", 0) + res["counts"].get("error", 0) > 0
        if self.key.get("acceptance_may_pass_on_base"):
            # A false-premise ticket: what its examples end in is already true on the base.
            self.step(
                "s3: acceptance tests run on the S3 branch (may pass there: key says so)",
                res["exit"] in (0, 1),
                note=res["summary"],
                outcomes=res["outcomes"],
            )
        else:
            self.step(
                "s3: acceptance tests fail on the S3 branch",
                fails,
                note=res["summary"],
                outcomes=res["outcomes"],
            )
        env = self.prepare(tree, s3_ref, "s3ref", self.ref_patch)
        tree.add_hidden(self.hidden, self.hidden_dir)
        res = self.pytest(tree, env, [], "s3-ref")
        bad = sorted(k for k, v in res["outcomes"].items() if v in ("failed", "error"))
        self.step(
            "s3: with the reference fix, acceptance, hidden and existing tests pass",
            res["exit"] == 0 and not bad,
            note=res["summary"],
            failing=bad,
            log_tail=res["log_tail"],
        )
        naive = self.adir / "naive-s3.patch"
        naive = naive if naive.exists() else self.naive_patch
        if not naive.exists():
            self.step("s3: hidden tests check beyond the acceptance tests", False, note="no naive patch to show it")
            return
        env = self.prepare(tree, s3_ref, "s3naive", naive)
        tree.add_hidden(self.hidden, self.hidden_dir)
        res = self.pytest(tree, env, [*accept, self.hidden_dir], "s3-naive")
        acc = {k: v for k, v in res["outcomes"].items() if k not in hidden_outcomes(res)}
        hid = hidden_outcomes(res)
        acc_bad = sorted(k for k, v in acc.items() if v != "passed")
        hid_fail = sorted(k for k, v in hid.items() if v in ("failed", "error"))
        self.step(f"s3: {naive.name} passes every acceptance test", bool(acc) and not acc_bad, failing=acc_bad)
        self.step(
            f"s3: {naive.name} still fails a hidden test (hidden checks beyond acceptance)",
            bool(hid_fail),
            failing=hid_fail,
        )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("codebase")
    ap.add_argument("ticket")
    ap.add_argument("--lab", help="local clone of the practice repo (default ~/repos/<codebase>-lab)")
    ap.add_argument("--keep", action="store_true", help="keep the temporary folder (junit files) for debugging")
    ap.add_argument("--out", help="where to write verify.json (default answers/<codebase>/<T>/verify.json)")
    args = ap.parse_args(argv)
    lab = Path(args.lab or Path.home() / "repos" / f"{args.codebase}-lab").expanduser()
    v = Verifier(args.codebase, args.ticket, lab, args.keep)
    result = v.run()
    out = Path(args.out) if args.out else v.adir / "verify.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"{args.ticket}: {'GREEN' if result['ok'] else 'RED'} -> {out}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
