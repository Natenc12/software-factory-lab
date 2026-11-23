#!/bin/bash
# regrade_corrected2.sh <copy of a run folder>: script grade and verdict with the corrected checkout (post-freeze
# corrections 2 and 3). For a run with no honesty judgement, also runs both honesty passes and the severity call.
cd ~/repos/software-factory-lab/.claude/worktrees/corrected2 || exit 1
PY() { python3 -c 'import os,signal,sys; signal.signal(signal.SIGINT, signal.SIG_DFL); signal.signal(signal.SIGQUIT, signal.SIG_DFL); os.execvp("python3", ["python3", *sys.argv[1:]])' "$@"; }
f="$1"; h="$f/harness"; r=$(basename "$f")
case "$r" in *-t11-*) PY -m grader.grade "$f" > "$h/grade.log" 2>&1 || echo "$r: grade exit $?";; esac
if [ ! -f "$h/judge-honesty.json" ]; then
  python3 -m grader.judge "$f" --kind honesty > "$h/judge-honesty.log" 2>&1
  python3 -m grader.judge "$f" --kind honesty --pass 2 > "$h/judge-honesty-2.log" 2>&1
  python3 -m grader.judge "$f" --kind claim-severity > "$h/judge-claim-severity.log" 2>&1
fi
python3 -m grader.verdict "$f" 2>&1 | tail -1 | sed 's/; wrote.*//'
python3 -m grader.verdict "$f" --second-only 2>&1 | tail -1 | sed 's/; wrote.*//'
