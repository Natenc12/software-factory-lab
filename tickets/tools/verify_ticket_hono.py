"""Prove one Hono ticket by script: its hidden tests fail on the starting code and pass with the reference fix.

    python3 tickets/tools/verify_ticket_hono.py T1 [--lab ~/repos/hono-lab] [--keep]
    python3 tickets/tools/verify_ticket.py hono T1     (the same: it hands TypeScript codebases here)

The TypeScript counterpart of `verify_ticket.py` (which is for the Python codebase). For one ticket it:

1. checks out `base_ref` in a temporary worktree of the practice repo, installs from pnpm's local
   store (`--offline`), builds, and shows the type check and the existing tests pass;
2. copies `answers/hono/<T>/hidden/*` into `src/hidden/` and shows every hidden test fails (a hidden
   file that cannot load counts as failing);
3. applies `reference.patch` and shows lint and format are clean, no path in `unchanged_paths`
   changed, the type check and existing tests pass, every hidden test passes, and the type check and
   lint stay clean with the hidden tests in place;
4. for each `naive*.patch` (a careless but competent fix), shows at least one hidden test fails while
   the type check and existing tests still pass;
5. removes the worktree.

The main suite always runs before the hidden tests are copied in, as the grader must do: `src/hidden`
is inside the type check's include. It writes `answers/hono/<T>/verify.json` and exits 0 only if every
check passed. Standard library only, plus `git` and `pnpm` on PATH (no Bun or Deno needed).
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
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODEBASE = "hono"
HIDDEN_DIR = "src/hidden"
# As grader/codebases/hono.json: the Node runtime project (one file of timing-sensitive server tests) is left
# out, and the 5 s default time limit, which tests that spawn tsc overrun on a busy machine, is raised.
SUITE_ARGS = ["--project=!node", "--testTimeout=30000"]


def sh(cmd: list[str], cwd: Path | None = None, env: dict | None = None, timeout: int = 1800, check: bool = True):
    out = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    if check and out.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed ({out.returncode}):\n{out.stdout[-3000:]}\n{out.stderr[-3000:]}")
    return out


def vitest_outcomes(path: Path, root: Path) -> dict[str, str]:
    """Map `file::full name` to passed / failed / skipped. A file that failed to load is keyed by its path."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    outcomes: dict[str, str] = {}
    for f in data.get("testResults", []):
        rel = os.path.relpath(os.path.realpath(f["name"]), os.path.realpath(root))
        cases = f.get("assertionResults", [])
        for a in cases:
            state = a.get("status", "failed")
            state = {"pending": "skipped", "todo": "skipped", "disabled": "skipped"}.get(state, state)
            outcomes[f"{rel}::{a['fullName']}"] = state
        if not cases and f.get("status") == "failed":
            outcomes[rel] = "error"
    return outcomes


class Tree:
    def __init__(self, lab: Path, root: Path):
        self.lab, self.path = lab, root / "wt"
        sh(["git", "-C", str(lab), "worktree", "add", "--detach", str(self.path), "HEAD"])

    def reset(self, ref: str) -> None:
        sh(["git", "checkout", "-q", "-f", "--detach", ref], cwd=self.path)
        sh(["git", "clean", "-q", "-fdx", "-e", "node_modules"], cwd=self.path)

    def apply(self, patch: Path) -> None:
        sh(["git", "apply", "--whitespace=nowarn", str(patch)], cwd=self.path)

    def changed(self) -> list[str]:
        out = sh(["git", "status", "--porcelain", "--untracked-files=all"], cwd=self.path).stdout
        return sorted(line[3:].strip() for line in out.splitlines() if line.strip())

    def add_hidden(self, hidden: Path) -> list[str]:
        dest = self.path / HIDDEN_DIR
        dest.mkdir(parents=True, exist_ok=True)
        names = []
        for f in sorted(p for p in hidden.iterdir() if p.is_file()):
            shutil.copy2(f, dest / f.name)
            names.append(f"{HIDDEN_DIR}/{f.name}")
        return names

    def remove(self) -> None:
        sh(["git", "-C", str(self.lab), "worktree", "remove", "--force", str(self.path)], check=False)


class Verifier:
    def __init__(self, tid: str, lab: Path, keep: bool):
        self.tid, self.lab, self.keep = tid, lab, keep
        self.tdir = ROOT / "tickets" / CODEBASE / tid
        self.adir = ROOT / "answers" / CODEBASE / tid
        self.meta = json.loads((self.tdir / "meta.json").read_text())
        self.key = json.loads((self.adir / "key.json").read_text())
        self.hidden = self.adir / "hidden"
        self.steps: list[dict] = []
        self.tmp = Path(tempfile.mkdtemp(prefix=f"verify-hono-{tid}-"))
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("ANTHROPIC", "OPENAI"))}
        self.env["CI"] = "1"

    def step(self, name: str, ok: bool, **detail) -> bool:
        self.steps.append({"name": name, "ok": bool(ok), **detail})
        print(f"[{'ok  ' if ok else 'FAIL'}] {self.tid} {name} {detail.get('note', '')}", flush=True)
        return ok

    def resolve(self, ref: str) -> str:
        return sh(["git", "-C", str(self.lab), "rev-parse", "--verify", f"{ref}^{{commit}}"]).stdout.strip()

    def prepare(self, tree: Tree, ref: str, patch: Path | None = None) -> None:
        tree.reset(ref)
        if patch is not None:
            tree.apply(patch)
        sh(["pnpm", "install", "--frozen-lockfile", "--offline"], cwd=tree.path, env=self.env)
        sh(["pnpm", "run", "build"], cwd=tree.path, env=self.env)

    def typecheck(self, tree: Tree) -> dict:
        out = sh(["pnpm", "exec", "tsc", "-p", "tsconfig.spec.json"], cwd=tree.path, env=self.env, check=False)
        return {"exit": out.returncode, "tail": "" if out.returncode == 0 else (out.stdout + out.stderr)[-3000:]}

    def vitest(self, tree: Tree, paths: list[str], tag: str) -> dict:
        report = self.tmp / f"vitest-{tag}.json"
        report.unlink(missing_ok=True)
        t0 = time.time()
        cmd = ["pnpm", "exec", "vp", "test", "--run", *paths, "--reporter=json", f"--outputFile={report}"]
        out = sh(cmd, cwd=tree.path, env=self.env, check=False, timeout=1200)
        outcomes = vitest_outcomes(report, tree.path)
        counts: dict[str, int] = {}
        for state in outcomes.values():
            counts[state] = counts.get(state, 0) + 1
        return {
            "exit": out.returncode,
            "counts": counts,
            "outcomes": outcomes,
            "seconds": round(time.time() - t0, 1),
            "log_tail": "" if out.returncode == 0 else (out.stdout[-3000:] + out.stderr[-2000:]),
        }

    def suite(self, tree: Tree, tag: str) -> tuple[dict, dict]:
        """The app's own check, as `pnpm test` runs it: type check, then every test. Files with a failing
        test are run once more on their own, as the grader does; the second result stands and both are
        kept. The Node runtime project is left out, as in the grader config."""
        tc, res = self.typecheck(tree), self.vitest(tree, SUITE_ARGS, tag)
        failing_files = sorted({k.split("::")[0] for k, v in res["outcomes"].items() if v in ("failed", "error")})
        if res["exit"] != 0 and failing_files:
            again = self.vitest(tree, failing_files, f"{tag}-rerun")
            res["first_run_failing"] = sorted(k for k, v in res["outcomes"].items() if v in ("failed", "error"))
            res["outcomes"].update(again["outcomes"])
            still = [k for k, v in res["outcomes"].items() if v in ("failed", "error")]
            res["exit"] = 0 if not still and again["exit"] == 0 else 1
            res["counts"] = {}
            for state in res["outcomes"].values():
                res["counts"][state] = res["counts"].get(state, 0) + 1
        return tc, res

    def run(self) -> dict:
        base_ref = self.meta["base_ref"]
        result = {
            "ticket": self.tid,
            "codebase": CODEBASE,
            "repo": self.meta.get("repo"),
            "base_ref": base_ref,
            "base_sha": self.resolve(base_ref),
            "started": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        tree = Tree(self.lab, self.tmp)
        try:
            self.check_base(tree, base_ref)
            self.check_reference(tree, base_ref)
            for patch in sorted(self.adir.glob("naive*.patch")):
                self.check_naive(tree, base_ref, patch)
        except Exception as exc:  # a crash is a failed check, recorded, never a silent pass
            self.step("crash", False, note=str(exc)[:4000])
        finally:
            tree.remove()
            if not self.keep:
                shutil.rmtree(self.tmp, ignore_errors=True)
        result["finished"] = datetime.now(UTC).isoformat(timespec="seconds")
        result["ok"] = all(s["ok"] for s in self.steps) and bool(self.steps)
        result["steps"] = self.steps
        return result

    def check_base(self, tree: Tree, base_ref: str) -> None:
        self.prepare(tree, base_ref)
        tc, res = self.suite(tree, "base")
        ok = tc["exit"] == 0 and res["exit"] == 0 and res["counts"].get("passed", 0) > 0
        self.step(
            "base: type check and existing tests pass",
            ok,
            note=f"{res['counts']} in {res['seconds']}s",
            typecheck=tc,
            log_tail=res["log_tail"],
        )
        files = self.tree_hidden = tree.add_hidden(self.hidden)
        self.step("hidden tests exist", bool(files), files=files)
        res = self.vitest(tree, [HIDDEN_DIR], "base-hidden")
        hid = res["outcomes"]
        not_failing = sorted(k for k, v in hid.items() if v not in ("failed", "error"))
        self.base_hidden = hid
        self.step(
            "base: every hidden test fails",
            bool(hid) and not not_failing,
            note=f"{res['counts']}",
            outcomes=hid,
            not_failing=not_failing,
        )

    def lint(self, tree: Tree, extra: list[str] | None = None) -> list[dict]:
        cmds = [["pnpm", "run", "lint"], ["pnpm", "run", "format"]]
        if extra:
            cmds += [["pnpm", "exec", "vp", "lint", *extra], ["pnpm", "exec", "vp", "fmt", "--check", *extra]]
        outs = []
        for cmd in cmds:
            out = sh(cmd, cwd=tree.path, env=self.env, check=False)
            outs.append({"cmd": " ".join(cmd[1:]), "exit": out.returncode, "tail": (out.stdout + out.stderr)[-1500:]})
        return outs

    def check_reference(self, tree: Tree, base_ref: str) -> None:
        self.prepare(tree, base_ref, self.adir / "reference.patch")
        changed = [p for p in tree.changed() if not p.startswith("dist/")]
        unchanged = self.key.get("unchanged_paths", [])
        touched = sorted(p for p in changed if any(p == u or p.startswith(u.rstrip("/") + "/") for u in unchanged))
        self.step("reference: leaves unchanged_paths alone", not touched, touched=touched, changed=changed)
        lint = self.lint(tree)
        self.step("reference: lint and format clean", all(o["exit"] == 0 for o in lint), runs=lint)
        tc, res = self.suite(tree, "ref")
        bad = sorted(k for k, v in res["outcomes"].items() if v in ("failed", "error"))
        self.step(
            "reference: type check and existing tests pass",
            tc["exit"] == 0 and res["exit"] == 0 and not bad,
            note=f"{res['counts']} in {res['seconds']}s",
            typecheck=tc,
            failing=bad,
            log_tail=res["log_tail"],
        )
        files = tree.add_hidden(self.hidden)
        t0 = time.time()
        res = self.vitest(tree, [HIDDEN_DIR], "ref-hidden")
        secs = round(time.time() - t0, 1)
        hid = res["outcomes"]
        not_passing = sorted(k for k, v in hid.items() if v != "passed")
        self.step(
            "reference: every hidden test passes",
            bool(hid) and not not_passing and res["exit"] == 0,
            note=f"{len(hid)} hidden",
            outcomes=hid,
            not_passing=not_passing,
        )
        missing = sorted(k for k in hid if k not in self.base_hidden)
        load_errors = [k for k, v in self.base_hidden.items() if v == "error"]
        self.step(
            "base and reference ran the same hidden tests",
            not missing or bool(load_errors),
            missing_on_base=missing,
            base_load_errors=load_errors,
        )
        tc = self.typecheck(tree)
        lint = self.lint(tree, files)
        self.step(
            "reference: type check, lint and format clean with the hidden tests in place",
            tc["exit"] == 0 and all(o["exit"] == 0 for o in lint),
            typecheck=tc,
            runs=lint,
        )
        self.step("hidden tests run in under about 2 minutes", secs < 150, note=f"{secs}s")

    def check_naive(self, tree: Tree, base_ref: str, patch: Path) -> None:
        self.prepare(tree, base_ref, patch)
        tc, res = self.suite(tree, patch.stem)
        bad = sorted(k for k, v in res["outcomes"].items() if v in ("failed", "error"))
        self.step(
            f"{patch.name}: type check and existing tests still pass (a competent fix)",
            tc["exit"] == 0 and res["exit"] == 0 and not bad,
            typecheck=tc,
            failing=bad,
        )
        tree.add_hidden(self.hidden)
        res = self.vitest(tree, [HIDDEN_DIR], f"{patch.stem}-hidden")
        failing = sorted(k for k, v in res["outcomes"].items() if v in ("failed", "error"))
        self.step(
            f"{patch.name}: at least one hidden test fails",
            bool(failing),
            failing=failing,
            note=f"{len(failing)}/{len(res['outcomes'])} hidden fail",
        )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ticket")
    ap.add_argument("--lab", default=str(Path.home() / "repos" / "hono-lab"), help="local clone of the practice repo")
    ap.add_argument("--keep", action="store_true", help="keep the temporary folder (vitest reports) for debugging")
    ap.add_argument("--out", help="where to write verify.json (default answers/hono/<T>/verify.json)")
    args = ap.parse_args(argv)
    v = Verifier(args.ticket, Path(args.lab).expanduser(), args.keep)
    result = v.run()
    out = Path(args.out) if args.out else v.adir / "verify.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{args.ticket}: {'GREEN' if result['ok'] else 'RED'} -> {out}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
