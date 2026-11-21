"""Join the common reply sheet with one ticket's replies into the one sheet a run's reply judge gets.

    python -m grader.build_sheet <codebase> <ticket> [--out sheet.md] [--answers-root answers]

The common replies come first (the first one, `default`, is the judge's fallback), then the ticket's own
replies from answers/<codebase>/<ticket>/replies.md. Ticket reply ids must start with the ticket id
(`T5-open-decision`); all ids must be unique. The result is checked with the harness's own parser.
Prints the sheet when --out is not given.
"""

import argparse
import re
import sys
import tempfile
from pathlib import Path

from grader.common import ANSWERS_ROOT
from harness.owner import parse_sheet

COMMON = ANSWERS_ROOT / "reply-sheet-common.md"


def blocks(text: str) -> str:
    """The `## ...` blocks of a sheet, without its preamble."""
    m = re.search(r"^##[ \t]+", text, re.M)
    return text[m.start() :].strip() if m else ""


def build(codebase: str, ticket: str, answers_root: Path = ANSWERS_ROOT, common: Path | None = None) -> str:
    if common is None:
        own_common = Path(answers_root) / "reply-sheet-common.md"
        common = own_common if own_common.is_file() else COMMON
    common = Path(common)
    replies = Path(answers_root) / codebase / ticket / "replies.md"
    head = common.read_text(encoding="utf-8")
    sheet = (
        f"<!-- built by grader.build_sheet from {common.name} and {codebase}/{ticket}/replies.md -->\n" + head.strip()
    )
    own = []
    if replies.is_file():
        tblocks = blocks(replies.read_text(encoding="utf-8"))
        if tblocks:
            sheet += "\n\n" + tblocks  # no heading: it would join the reply text above it
            with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
                f.write(tblocks + "\n")
            try:
                own = [r["id"] for r in parse_sheet(Path(f.name))]
            finally:
                Path(f.name).unlink()
    bad = [i for i in own if not i.startswith(f"{ticket}-")]
    if bad:
        raise ValueError(f"{replies}: ticket reply ids must start with '{ticket}-': {bad}")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(sheet + "\n")
    try:
        parsed = parse_sheet(Path(f.name))  # raises on duplicate ids or a reply without text
    finally:
        Path(f.name).unlink()
    if parsed[0]["id"] != "default":
        raise ValueError("the first reply must be `default`: the reply judge falls back to it")
    return sheet + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m grader.build_sheet", description=__doc__.split("\n\n")[0])
    ap.add_argument("codebase")
    ap.add_argument("ticket")
    ap.add_argument("--out")
    ap.add_argument("--answers-root", default=str(ANSWERS_ROOT))
    ap.add_argument("--common", help=f"default {COMMON.relative_to(ANSWERS_ROOT.parent)}")
    a = ap.parse_args(argv)
    try:
        sheet = build(a.codebase, a.ticket, Path(a.answers_root), Path(a.common) if a.common else COMMON)
    except (OSError, ValueError) as e:
        print(f"build_sheet: {e}", file=sys.stderr)
        return 2
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(sheet, encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        sys.stdout.write(sheet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
