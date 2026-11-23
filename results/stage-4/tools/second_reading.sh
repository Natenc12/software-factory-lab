#!/bin/bash
# second_reading.sh <run folder>: add the second reading to a graded run. Adds files; the first reading stays.
cd ~/repos/software-factory-lab || exit 1
f="$1"; h="$f/harness"; r=$(basename "$f")
ok() { python3 -c "import json,sys; sys.exit(0 if json.load(open(sys.argv[1])).get('valid') else 1)" "$1" 2>/dev/null; }
ok "$h/judge-honesty-2.json" || python3 -m grader.judge "$f" --kind honesty --pass 2 > "$h/judge-honesty-2.log" 2>&1
python3 -m grader.judge "$f" --kind claim-severity > "$h/judge-claim-severity.log" 2>&1
if [ ! -f "$h/second-picks.json" ]; then
  case "$f" in */stage-1/*) python3 -m grader.second_pick "$f" --import results/stage-1/second-reply-picks.jsonl > "$h/second-picks.log" 2>&1 ;; esac
  python3 -m grader.second_pick "$f" >> "$h/second-picks.log" 2>&1
fi
python3 -m grader.verdict "$f" --second-only 2>&1 | tail -1 | sed 's/; wrote.*//'
