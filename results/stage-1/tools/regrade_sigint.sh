#!/bin/bash
# regrade_sigint.sh <run folder>: script grade again with the default SIGINT, keep the first grade beside it.
cd ~/repos/software-factory-lab || exit 1
PY() { python3 -c 'import os,signal,sys; signal.signal(signal.SIGINT, signal.SIG_DFL); signal.signal(signal.SIGQUIT, signal.SIG_DFL); os.execvp("python3", ["python3", *sys.argv[1:]])' "$@"; }
f="$1"; h="$f/harness"; k="$h/first-grade"
[ -d "$k" ] && { echo "$(basename $f): already done"; exit 0; }
mkdir -p "$k" && cp "$h/grade.json" "$h/grade.diff" "$h/verdict.json" "$k/" 2>/dev/null
PY -m grader.grade "$f" > "$h/grade.log" 2>&1 || echo "$(basename $f): grade exit $?"
python3 -m grader.verdict "$f" 2>&1 | tail -1
