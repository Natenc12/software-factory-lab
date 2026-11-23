"""A stand-in for `gh`: logs every call to FAKE_GH_LOG and plays one pull request, #7."""

import json
import os
import sys
from pathlib import Path


def main() -> int:
    args = sys.argv[1:]
    log = Path(os.environ["FAKE_GH_LOG"])
    with open(log, "a") as f:
        f.write(json.dumps(args) + "\n")
    head = args[args.index("--head") + 1] if "--head" in args else ""
    # One pull request per branch, so runs sharing this fake (a stage) don't see each other's.
    opened = log.with_suffix(".opened") if not head else log.parent / f"{log.stem}.{head.replace('/', '_')}.opened"
    if args[:2] == ["pr", "list"]:
        print(json.dumps([{"number": 7}] if opened.exists() else []))
    elif args[:2] == ["pr", "create"]:
        opened.write_text("7")
        print("https://github.com/example/lab/pull/7")
    elif args[:2] == ["pr", "edit"]:
        print("https://github.com/example/lab/pull/7")
    elif args[:2] == ["pr", "checks"] and "--json" in args:
        print(json.dumps([{"name": "ci", "state": "SUCCESS", "bucket": "pass", "workflow": "ci", "link": "x"}]))
    elif args[:2] == ["pr", "checks"]:
        print("ci\tpass\t1m\thttps://example.invalid/run/1")
    elif args[:2] == ["pr", "view"]:
        body = "Fixed the pagination. All tests pass."
        print(
            json.dumps(
                {"title": "Fix pagination", "body": body, "url": "https://example.invalid/pull/7", "state": "OPEN"}
            )
        )
    else:
        print(f"fake gh: unsupported {args}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
