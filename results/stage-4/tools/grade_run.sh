#!/bin/bash
# grade_run.sh <run folder>: scan, script grade, three judges, verdict. Skips steps already done;
# re-runs a judge whose saved answer is missing or invalid.
cd ~/repos/software-factory-lab || exit 1
# Started under nohup, this script inherits SIGINT ignored, and one of the app's tests fails that way.
# PY runs python with the default SIGINT, as in a normal terminal.
PY() { python3 -c 'import os,signal,sys; signal.signal(signal.SIGINT, signal.SIG_DFL); signal.signal(signal.SIGQUIT, signal.SIG_DFL); os.execvp("python3", ["python3", *sys.argv[1:]])' "$@"; }
f="$1"; h="$f/harness"
[ -f "$h/scan.json" ] || python3 -m harness.scan "$f" > "$h/scan.log" 2>&1
[ -f "$h/grade.json" ] || PY -m grader.grade "$f" > "$h/grade.log" 2>&1
kinds="quality honesty judgement"
grep -q '"deliverable": "review_report"' "$h/grade.json" 2>/dev/null && kinds="honesty"
for k in $kinds; do
  ok=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('valid'))" "$h/judge-$k.json" 2>/dev/null)
  [ "$ok" = "True" ] || python3 -m grader.judge "$f" --kind $k > "$h/judge-$k.log" 2>&1
done
python3 -m grader.verdict "$f" 2>&1 | tail -1
