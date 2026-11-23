"""A stand-in for `codex exec`, so the Codex check judge is tested without a login or a network call.

Logs argv, cwd, the environment's keys and CODEX_HOME, and stdin to FAKE_CODEX_LOG. Writes FAKE_JUDGE (or
the next answer from the JSON list in FAKE_JUDGE_SEQ) to --output-last-message, and prints `--json`
events with a usage record, as the real CLI does.
"""

import json
import os
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    stdin = sys.stdin.read()
    log = os.environ.get("FAKE_CODEX_LOG")
    if log:
        with open(log, "a") as f:
            rec = {"argv": argv, "cwd": os.getcwd(), "env": sorted(os.environ), "codex_home": os.environ.get("CODEX_HOME"),
                   "stdin": stdin, "room_files": sorted(os.listdir(os.getcwd()))}  # fmt: skip
            f.write(json.dumps(rec) + "\n")
    answer = os.environ.get("FAKE_JUDGE", "{}")
    seq = os.environ.get("FAKE_JUDGE_SEQ")
    if seq:
        answers = json.loads(Path(seq).read_text())
        counter = Path(seq + ".count")
        n = int(counter.read_text()) if counter.exists() else 0
        counter.write_text(str(n + 1))
        answer = answers[min(n, len(answers) - 1)]
    out = argv[argv.index("--output-last-message") + 1]
    Path(out).write_text(answer)
    print(json.dumps({"type": "thread.started", "thread_id": "fake"}))
    print(
        json.dumps(
            {"type": "turn.completed", "usage": {"input_tokens": 1200, "cached_input_tokens": 0, "output_tokens": 80}}
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
