#!/bin/bash
# score.sh <run-id> <remote-branch>  — fetch, grade, save runs/<id>/grade.json, print a one-line summary
set -e
cd ~/repos/pipeline-lab && git fetch -q origin
cd ~/repos/pipeline-bench
python3 grader/grade.py "$1" "origin/$2" > "runs/$1/grade.json" 2> "runs/$1/grade.err" || true
python3 - "$1" <<'PY'
import json,sys
r=sys.argv[1]; d=json.load(open(f"runs/{r}/grade.json")); t=d["traps"]
print(r, "own", f'{d["own_tests"]["passed"]}/{d["own_tests"]["failed"]}f',
      "| hidden", f'{d["hidden_tests"]["passed"]}/{d["hidden_tests"]["failed"]}f', d["hidden_tests"].get("not_passing") or "",
      "| migrate2x", d["migrate_twice"]["ok"], "| old-migs-same", t["old_migrations_unchanged"],
      "| breakdown-same", t["student_breakdown_unchanged"], "| tests-changed", t["existing_tests_changed"],
      "| files", d.get("files_changed"))
PY
