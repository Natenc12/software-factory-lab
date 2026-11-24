"""make_final_root.py: build ~/factory-runs-variants/final, every stage's graded records in their latest
corrected state, for the re-judging under post-freeze correction 4 and for grader.profiles.

    python3 results/final/tools/make_final_root.py [--dest ~/factory-runs-variants/final]

Sources (read only): stages 1, the confirm round, 2 and 2b from ~/factory-runs-variants/combined2 (the root
results/stage-2/RESULTS.md and results/stage-2b/RESULTS.md use for the corrected gradings; 2b as graded),
stage 4 from ~/factory-runs-variants/corrected4. Per run it copies records only: harness/ and the top-level
files. No repo clone, no scratch folder, no arm copy. Two exceptions, single files copied from the run's own
folder so the judges and the verdict read what they read before (grader.common.page_rel): the page a final
message names (two P3 runs name scratch/brief.html) and a review ticket's report (scratch/review.md). With
--extras-only it adds those files to runs already in the destination. A run already there is otherwise left alone.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(LAB))

from grader.common import final_message, page_rel, read_json  # noqa: E402
from harness.stream import find_page  # noqa: E402

VARIANTS = Path.home() / "factory-runs-variants"
SOURCES = {
    "stage-1": "combined2",
    "stage-1-confirm": "combined2",
    "stage-2": "combined2",
    "stage-2b": "combined2",
    "stage-4-hono": "corrected4",
    "stage-4-sqlglot": "corrected4",
}
SKIP = {"repo", "scratch", "arm"}


def copy_extras(src: Path, dst: Path) -> str | None:
    """The page and the review report for a run already copied (files already there are left alone)."""
    hdir = dst / "harness"
    own = Path((read_json(hdir / "run.json") or {}).get("sandbox") or src)
    for rel in (
        page_rel((read_json(hdir / "grade.json") or {}).get("review_report"), hdir),
        page_rel(find_page(final_message(hdir)), hdir),
    ):
        if rel and not os.path.isabs(rel) and (own / rel).is_file() and not (dst / rel).exists():
            (dst / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(own / rel, dst / rel)
            return rel
    return None


def copy_run(src: Path, dst: Path) -> str | None:
    dst.mkdir(parents=True)
    for p in src.iterdir():
        if p.name in SKIP:
            continue
        if p.is_dir() and not p.is_symlink():
            shutil.copytree(p, dst / p.name, symlinks=True)
        elif p.is_file():
            shutil.copy2(p, dst / p.name)
    hdir = dst / "harness"
    own = Path((read_json(hdir / "run.json") or {}).get("sandbox") or src)
    copied = None
    report = page_rel((read_json(hdir / "grade.json") or {}).get("review_report"), hdir)
    if report and not os.path.isabs(report) and (own / report).is_file():
        (dst / report).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(own / report, dst / report)
        copied = report
    rel = page_rel(find_page(final_message(hdir)), hdir)
    if not rel or os.path.isabs(os.path.expanduser(rel)):
        return copied
    for sub, base in (("repo", own / "repo"), ("", own)):
        page = Path(os.path.realpath(base / rel))
        if page.is_file() and str(page).startswith(str(own) + "/"):
            target = dst / sub / rel if sub else dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(page, target)
            return str(target.relative_to(dst))
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dest", default=str(VARIANTS / "final"))
    ap.add_argument(
        "--extras-only", action="store_true", help="only add pages and review reports to runs already copied"
    )
    a = ap.parse_args(argv)
    dest = Path(os.path.expanduser(a.dest))
    for stage, name in SOURCES.items():
        src_stage = VARIANTS / name / stage
        made = pages = 0
        for src in sorted(p for p in src_stage.iterdir() if (p / "harness" / "run.json").is_file()):
            dst = dest / stage / src.name
            if dst.exists():
                if a.extras_only and copy_extras(src, dst):
                    pages += 1
                continue
            if copy_run(src, dst):
                pages += 1
            made += 1
        total = sum(1 for p in (dest / stage).iterdir() if p.is_dir())
        print(f"{stage}: from {name}, {made} copied now, {total} in all, {pages} page or report files copied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
