#!/bin/bash
# regrade_workers_early.sh <copy of a run folder>: post-freeze correction 4 (worker calls labelled in the
# honesty judge's tool list) for a stage 1 to 2b run. Stages before 4 did not record workers_started in
# run.json, so a worker is found in the transcript (a tool call with parent_tool_use_id). For such a run:
# both honesty passes and the severity call are judged again, then the current and second readings.
# The Script grade and the other judges are untouched. Run only on a copy (make_variant5.sh).
cd ~/repos/software-factory-lab || exit 1
export TMPDIR=~/factory-runs/.grading-tmp; mkdir -p "$TMPDIR"
f="$1"; h="$f/harness"; r=$(basename "$f")
case "$f" in */factory-runs-variants/corrected5/*) ;; *) echo "$r: not a corrected5 copy, refused"; exit 1 ;; esac
python3 - "$h/verdict.json" <<'PY' || { echo "$r: discarded, skipped"; exit 0; }
import json, sys; sys.exit(1 if json.load(open(sys.argv[1])).get("discarded") else 0)
PY
python3 - "$h/transcript.jsonl" <<'PY' || { echo "$r: no worker calls, unchanged"; exit 0; }
import json, sys
for line in open(sys.argv[1], errors="replace"):
    try:
        rec = json.loads(line)
    except ValueError:
        continue
    if rec.get("type") == "assistant" and rec.get("parent_tool_use_id") and any(
            isinstance(b, dict) and b.get("type") == "tool_use" for b in (rec.get("message") or {}).get("content") or []):
        sys.exit(0)
sys.exit(1)
PY
if [ ! -f "$h/.corrected5" ]; then
  mkdir -p "$h/before-correction-4"
  cp "$h"/judge-honesty.json "$h"/judge-honesty-2.json "$h"/judge-claim-severity.json "$h/verdict.json" "$h/before-correction-4/" 2>/dev/null
  rm -f "$h"/judge-honesty.json "$h"/judge-honesty-2.json "$h"/judge-claim-severity.json
  python3 -m grader.judge "$f" --kind honesty > "$h/judge-honesty.log" 2>&1
  python3 -m grader.judge "$f" --kind honesty --pass 2 > "$h/judge-honesty-2.log" 2>&1
  python3 -m grader.judge "$f" --kind claim-severity > "$h/judge-claim-severity.log" 2>&1
  touch "$h/.corrected5"
fi
python3 -m grader.verdict "$f" 2>&1 | tail -1 | sed 's/; wrote.*//'
python3 -m grader.verdict "$f" --second-only 2>&1 | tail -1 | sed 's/; wrote.*//'
