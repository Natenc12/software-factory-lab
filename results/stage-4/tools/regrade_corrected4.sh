#!/bin/bash
# regrade_corrected4.sh <copy of a run folder>: post-freeze correction 4 (worker calls labelled in the honesty
# judge's tool list). For a run that started a worker: both honesty passes, the severity call and the Opus
# check are judged again with the corrected grader; then the three verdict readings. Script grade untouched.
cd ~/repos/software-factory-lab || exit 1
export TMPDIR=~/factory-runs/.grading-tmp; mkdir -p "$TMPDIR"
f="$1"; h="$f/harness"; r=$(basename "$f")
w=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('workers_started') or 0)" "$h/run.json")
[ "$w" -gt 0 ] || { echo "$r: no workers, unchanged"; exit 0; }
if [ ! -f "$h/.corrected4" ]; then
  mkdir -p "$h/as-frozen"; cp "$h"/judge-honesty*.json "$h"/judge-claim-severity.json "$h/verdict.json" "$h/as-frozen/" 2>/dev/null
  rm -f "$h"/judge-honesty.json "$h"/judge-honesty-2.json "$h"/judge-claim-severity.json "$h"/judge-honesty-check.json
  python3 -m grader.judge "$f" --kind honesty > "$h/judge-honesty.log" 2>&1
  python3 -m grader.judge "$f" --kind honesty --pass 2 > "$h/judge-honesty-2.log" 2>&1
  python3 -m grader.judge "$f" --kind claim-severity > "$h/judge-claim-severity.log" 2>&1
  python3 -m grader.judge "$f" --kind honesty --check > "$h/judge-honesty-check.log" 2>&1
  touch "$h/.corrected4"
fi
python3 -m grader.verdict "$f" 2>&1 | tail -1 | sed 's/; wrote.*//'
python3 -m grader.verdict "$f" --second-only 2>&1 | tail -1 | sed 's/; wrote.*//'
python3 -m grader.verdict "$f" --check-only 2>&1 | tail -1 | sed 's/; wrote.*//'
