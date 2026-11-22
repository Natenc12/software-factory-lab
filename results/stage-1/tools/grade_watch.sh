#!/bin/bash
# grade_watch.sh <stage> <plan basename>: grade finished runs two at a time while the stage runs, then finish the rest.
S="$(cd "$(dirname "$0")" && pwd)"; R=~/factory-runs/$1
pending() {
  for f in "$R"/*/; do
    f=${f%/}; h="$f/harness"; [ -f "$h/run.json" ] || continue
    st=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('status'))" "$h/run.json" 2>/dev/null)
    case "$st" in finished|ceiling_hit) ;; *) continue;; esac
    out=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('outcome'))" "$h/verdict.json" 2>/dev/null)
    [ -n "$out" ] && [ "$out" != "incomplete" ] && continue
    n=$(cat "$h/.grade-tries" 2>/dev/null || echo 0); [ "$n" -ge 3 ] && continue
    echo "$f"
  done
}
while :; do
  list=$(pending | head -2)
  if [ -z "$list" ]; then
    pgrep -f "harness.stage results/$1/$2" >/dev/null || break
    sleep 30; continue
  fi
  for f in $list; do n=$(cat "$f/harness/.grade-tries" 2>/dev/null || echo 0); echo $((n+1)) > "$f/harness/.grade-tries"; done
  echo "$list" | xargs -P 2 -n 1 "$S/grade_run.sh"
done
echo "grading done for $1"
