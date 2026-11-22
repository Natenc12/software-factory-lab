#!/bin/bash
# grade_corrected.sh <variant run folder>: script grade with the corrected answers; re-run the honesty judge
# only if the hidden-test result changed; then verdict. The frozen records stay in ~/factory-runs/stage-1.
cd ~/repos/software-factory-lab || exit 1
A=~/repos/software-factory-lab/.claude/worktrees/corrected/answers
PY() { python3 -c 'import os,signal,sys; signal.signal(signal.SIGINT, signal.SIG_DFL); signal.signal(signal.SIGQUIT, signal.SIG_DFL); os.execvp("python3", ["python3", *sys.argv[1:]])' "$@"; }
f="$1"; h="$f/harness"; r=$(basename "$f")
before=$(python3 -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))['hidden_tests'], sort_keys=True))" "$h/grade.json")
PY -m grader.grade "$f" --answers-root "$A" > "$h/grade.log" 2>&1 || echo "$r: grade exit $?"
after=$(python3 -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))['hidden_tests'], sort_keys=True))" "$h/grade.json")
if [ "$before" != "$after" ]; then
  python3 -m grader.judge "$f" --kind honesty --answers-root "$A" > "$h/judge-honesty.log" 2>&1
  echo "$r: hidden result changed, honesty judge re-run"
else
  echo "$r: hidden result unchanged"
fi
python3 -m grader.verdict "$f" --answers-root "$A" 2>&1 | tail -1
