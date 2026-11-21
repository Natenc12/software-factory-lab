"""Dry run: every ticket's reference fix must grade as passing, and an empty change as failing.

    python -m grader.dryrun <codebase> [--tickets-root tickets] [--answers-root answers] [--only T1]
                            [--out results/dryrun-<codebase>.json] [--keep]

For each ticket under <tickets root>/<codebase>/ with a meta.json, the dry run takes the starting
commit (`base_ref`), applies `reference.patch` from the answer package as one commit, and grades it
exactly as a run is graded. It also grades the starting commit itself (the empty change). When the
ticket has an `s3_base_ref`, the reference fix is graded on that base too, as an S3 run would be.

Green means: reference -> hidden tests pass, no trap tripped, own tests and migrations pass;
empty -> hidden tests do not pass. The source repo is the codebase's local clone, cloned into a
temporary folder; refs it lacks are fetched from GitHub into that temporary clone only.
Exit code 0 when every ticket is green, 1 otherwise, 2 on a usage error.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from grader.common import ANSWERS_ROOT, TICKETS_ROOT, load_config, now_iso, read_json, write_json
from grader.grade import git, grade_commit


def source_repo(cfg: dict, refs: list[str], tmp: Path) -> tuple[Path, dict]:
    """A private clone holding every ref the dry run needs. Returns (repo, {ref: commit})."""
    local = Path(str(cfg.get("local_clone") or "")).expanduser()
    src = tmp / "src"
    if local.is_dir():
        subprocess.run(
            ["git", "clone", "--quiet", "--no-checkout", str(local), str(src)], check=True, capture_output=True
        )
    else:
        subprocess.run(["git", "init", "--quiet", str(src)], check=True)
    found = {}
    for ref in refs:
        for cand in (ref, f"origin/{ref}", f"refs/remotes/origin/{ref}"):
            sha = git(src, "rev-parse", "--verify", "--quiet", f"{cand}^{{commit}}", check=False).strip()
            if sha:
                found[ref] = sha
                break
        if ref not in found and cfg.get("repo"):
            gh = shutil.which("gh") or "gh"
            url = f"https://github.com/{cfg['repo']}.git"
            p = subprocess.run(
                ["git", "-C", str(src), "-c", "credential.helper=", "-c", f"credential.helper=!{gh} auth git-credential",
                 "fetch", "--quiet", "--no-tags", url, ref],
                capture_output=True, text=True,
            )  # fmt: skip
            if p.returncode == 0:
                found[ref] = git(src, "rev-parse", "FETCH_HEAD").strip()
    return src, found


def commit_patch(src: Path, base: str, patch: Path, tmp: Path, name: str) -> str:
    """Apply the patch on `base` in a scratch worktree of `src` and return the new commit."""
    wt = tmp / f"apply-{name}"
    git(src, "worktree", "add", "--quiet", "--detach", str(wt), base)
    try:
        p = subprocess.run(
            ["git", "-C", str(wt), "apply", "--index", str(patch.resolve())], capture_output=True, text=True
        )
        if p.returncode != 0:
            raise RuntimeError(f"reference.patch does not apply on {base[:12]}: {p.stderr.strip()[:300]}")
        g = ["-c", "user.name=grader", "-c", "user.email=grader@example.invalid"]
        git(wt, *g, "commit", "--quiet", "--no-verify", "-m", f"reference fix ({name})")
        return git(wt, "rev-parse", "HEAD").strip()
    finally:
        git(src, "worktree", "remove", "--force", str(wt), check=False)


def judge_reference(g: dict) -> list[str]:
    """Why a reference grade is not green (empty list when it is)."""
    why = []
    if g.get("error"):
        why.append(f"error: {g['error']}")
    hidden = g.get("hidden_tests") or {}
    if not hidden.get("ok"):
        why.append(f"hidden tests not passing ({hidden.get('passed', 0)} passed, {hidden.get('failed', 0)} failed, "
                   f"{hidden.get('errors', 0)} errors)")  # fmt: skip
    if g.get("traps_tripped"):
        why.append(f"traps tripped: {', '.join(g['traps_tripped'])}")
    if g.get("traps_unknown"):
        why.append(f"traps not evaluated: {', '.join(g['traps_unknown'])}")
    if not (g.get("own_tests") or {}).get("ok"):
        why.append("own tests not passing")
    if g.get("migrate_twice") is not None and not g["migrate_twice"].get("ok"):
        why.append("migrations twice not ok")
    return why


def judge_empty(g: dict) -> list[str]:
    hidden = g.get("hidden_tests")
    if g.get("error"):
        return [f"error: {g['error']}"]
    if not hidden:
        return ["no hidden tests ran"]
    if hidden.get("ok") or g.get("script_pass"):
        return ["the empty change grades as passing: the hidden tests do not test the ticket"]
    return []


def dry_run(cfg: dict, tickets_root: Path, answers_root: Path, only=None, keep=False) -> dict:
    tickets = sorted(p.parent for p in (tickets_root / cfg["name"]).glob("T*/meta.json"))
    if only:
        tickets = [t for t in tickets if t.name in only]
    out = {"codebase": cfg["name"], "time": now_iso(), "tickets": {}, "green": bool(tickets)}
    if not tickets:
        out["error"] = f"no tickets with meta.json under {tickets_root / cfg['name']}"
        return out
    metas = {t.name: read_json(t / "meta.json") for t in tickets}
    refs = sorted({r for m in metas.values() for r in (m.get("base_ref"), m.get("s3_base_ref")) if r})
    tmp = Path(tempfile.mkdtemp(prefix=f"dryrun-{cfg['name']}-"))
    try:
        src, found = source_repo(cfg, refs, tmp)
        for t in tickets:
            name, meta = t.name, metas[t.name]
            answers = answers_root / cfg["name"] / name
            key = read_json(answers / "key.json", {}) or {}
            row: dict = {"rows": {}}
            problems = []
            if not key:
                problems.append("key.json missing")
            if not (answers / "reference.patch").is_file():
                problems.append("reference.patch missing")
            base = found.get(meta.get("base_ref"))
            if not base:
                problems.append(f"base_ref {meta.get('base_ref')!r} not found")
            if not problems:
                cases = [("empty", "S1", base, base)]
                try:
                    cases.insert(
                        0, ("reference", "S1", base, commit_patch(src, base, answers / "reference.patch", tmp, name))
                    )
                except RuntimeError as e:
                    problems.append(str(e))
                s3 = meta.get("s3_base_ref")
                if s3 and meta.get("deliverable", "pull_request") == "pull_request":
                    if s3 not in found:
                        problems.append(f"s3_base_ref {s3!r} not found")
                    else:
                        try:
                            s3_ref = commit_patch(src, found[s3], answers / "reference.patch", tmp, f"{name}-s3")
                            cases.append(("reference_s3", "S3", found[s3], s3_ref))
                        except RuntimeError as e:
                            problems.append(f"S3: {e}")
                for case, spec, b, h in cases:
                    g = grade_commit(cfg, src, b, h, answers, key, spec, keep=keep, label=f"dry_{name}_{case}")
                    why = judge_empty(g) if case == "empty" else judge_reference(g)
                    row["rows"][case] = {"green": not why, "why": why, "grade": g}
                    problems += [f"{case}: {w}" for w in why]
            row["green"] = not problems
            row["problems"] = problems
            out["tickets"][name] = row
            out["green"] = out["green"] and row["green"]
    finally:
        if not keep:
            shutil.rmtree(tmp, ignore_errors=True)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m grader.dryrun", description=__doc__.split("\n\n")[0])
    ap.add_argument("codebase", help="config name under grader/codebases/ (gct, pipeline-lab) or a path")
    ap.add_argument("--tickets-root", default=str(TICKETS_ROOT))
    ap.add_argument("--answers-root", default=str(ANSWERS_ROOT))
    ap.add_argument("--only", action="append", help="ticket id to check (repeatable)")
    ap.add_argument("--out", help="write the full report here (JSON)")
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args(argv)
    cfg = load_config(a.codebase)
    report = dry_run(cfg, Path(a.tickets_root), Path(a.answers_root), a.only, a.keep)
    if a.out:
        write_json(Path(a.out), report)
    if report.get("error"):
        print(report["error"])
    for name, row in report["tickets"].items():
        print(f"{name}: {'GREEN' if row['green'] else 'RED'}" + "".join(f"\n  - {p}" for p in row["problems"]))
    print(f"dry run {cfg['name']}: {'GREEN' if report['green'] else 'RED'}")
    return 0 if report["green"] else 1


if __name__ == "__main__":
    sys.exit(main())
