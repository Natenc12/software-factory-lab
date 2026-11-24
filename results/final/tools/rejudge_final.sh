#!/bin/bash
# rejudge_final.sh <run folder under ~/factory-runs-variants/final>: post-freeze correction 4 (worker calls
# labelled in the honesty judge's tool list) for a stage 1 to 2b run with worker calls (a tool call with
# parent_tool_use_id in its transcript; these stages did not record workers_started). Keeps the old judge
# files and verdict in harness/before-correction-4/, rebuilds the verdict from the old judges first
# (verdict.rebuilt.json, to show the rebuild alone changes nothing), then judges honesty pass 1, pass 2 and
# the severity call again and rebuilds the current and second readings. The Script grade is not re-run.
cd "$(dirname "$0")/../../.." || exit 1  # this checkout's grader
export TMPDIR=~/factory-runs/.grading-tmp; mkdir -p "$TMPDIR"
f="${1%/}"; h="$f/harness"; r=$(basename "$f"); b="$h/before-correction-4"
case "$f" in "$HOME"/factory-runs-variants/final/stage-*/*) ;; *) echo "$r: not under ~/factory-runs-variants/final, refused"; exit 1 ;; esac
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
            isinstance(x, dict) and x.get("type") == "tool_use" for x in (rec.get("message") or {}).get("content") or []):
        sys.exit(0)
sys.exit(1)
PY
[ -f "$h/.rejudged" ] && { echo "$r: already re-judged"; exit 0; }
if [ ! -d "$b" ]; then
  mkdir -p "$b"
  cp "$h"/judge-honesty.json "$h"/judge-honesty-2.json "$h"/judge-claim-severity.json "$b/" 2>/dev/null
  cp "$h"/judge-honesty.prompt.txt "$h"/judge-honesty-2.prompt.txt "$b/" 2>/dev/null
  cp "$h/verdict.json" "$b/verdict.json"
  python3 -m grader.verdict "$f" > /dev/null 2>&1 && python3 -m grader.verdict "$f" --second-only > /dev/null 2>&1
  cp "$h/verdict.json" "$b/verdict.rebuilt.json"
fi
rm -f "$h"/judge-honesty.json "$h"/judge-honesty-2.json "$h"/judge-claim-severity.json
python3 -m grader.judge "$f" --kind honesty > "$h/judge-honesty.log" 2>&1
python3 -m grader.judge "$f" --kind honesty --pass 2 > "$h/judge-honesty-2.log" 2>&1
python3 -m grader.judge "$f" --kind claim-severity > "$h/judge-claim-severity.log" 2>&1
v1=$(python3 -m grader.verdict "$f" 2>&1 | tail -1 | sed 's/; wrote.*//')
v2=$(python3 -m grader.verdict "$f" --second-only 2>&1 | tail -1 | sed 's/; wrote.*//')
[ -f "$h/judge-honesty.json" ] && [ -f "$h/judge-honesty-2.json" ] && touch "$h/.rejudged"
echo "$v1 | $v2"
