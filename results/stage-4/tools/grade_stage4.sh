#!/bin/bash
# grade_stage4.sh <stage> [<stage> ...]: grade finished runs of the named stages, four at a time,
# with the second reading straight after each run's first grade. Ends when every stage log shows
# its final line and nothing is left to grade. Ends on the logs, not on process names.
# A run gets three tries; a try is counted only for a run that is actually picked up.
S="$(cd "$(dirname "$0")" && pwd)"
OLD="$S"
ROOT=~/factory-runs
# Grade from a temp folder a sealed run cannot read (the grader's checkouts hold the hidden tests).
export TMPDIR=~/factory-runs/.grading-tmp; mkdir -p "$TMPDIR"
one() {
  f="$1"; h="$f/harness"
  n=$(cat "$h/.grade-tries" 2>/dev/null || echo 0); echo $((n+1)) > "$h/.grade-tries"
  "$OLD/grade_run.sh" "$f"
  [ -f "$h/verdict.json" ] || return
  "$OLD/second_reading.sh" "$f"
  # Other-model check (stage 4 freeze): honesty and quality judged again by Opus, reported only.
  ( cd ~/repos/software-factory-lab || exit 1
    ok() { python3 -c "import json,sys; sys.exit(0 if json.load(open(sys.argv[1])).get('valid') else 1)" "$1" 2>/dev/null; }
    kinds="honesty quality"; grep -q '"deliverable": "review_report"' "$h/grade.json" 2>/dev/null && kinds="honesty"
    for k in $kinds; do ok "$h/judge-$k-check.json" || python3 -m grader.judge "$f" --kind $k --check > "$h/judge-$k-check.log" 2>&1; done
    python3 -m grader.verdict "$f" --check-only 2>&1 | tail -1 | sed 's/; wrote.*//' )
}
if [ "$1" = "--one" ]; then one "$2"; exit 0; fi
while :; do
  pending=()
  for st in "$@"; do
    for d in "$ROOT/$st"/*/; do
      h="$d/harness"; [ -f "$h/run.json" ] || continue
      [ -f "$h/verdict.json" ] && [ -f "$h/second-picks.json" ] && [ -f "$h/judge-honesty-check.json" ] && continue
      s=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('status'))" "$h/run.json" 2>/dev/null)
      case "$s" in finished|ceiling_hit) ;; *) continue ;; esac
      n=$(cat "$h/.grade-tries" 2>/dev/null || echo 0); [ "$n" -ge 3 ] && continue
      pending+=("${d%/}")
    done
  done
  if [ ${#pending[@]} -gt 0 ]; then
    printf '%s\n' "${pending[@]}" | head -4 | xargs -P 4 -n 1 "$S/grade_stage4.sh" --one
    continue
  fi
  done_all=1
  for st in "$@"; do
    grep -q "^stage $st: .* counted tokens used" "$ROOT/$st/.logs/stage.log" 2>/dev/null || done_all=0
  done
  [ "$done_all" = 1 ] && break
  sleep 30
done
echo "grading done: $*"
