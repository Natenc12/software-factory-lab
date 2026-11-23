#!/bin/bash
# grade_confirm.sh: grade finished confirm-round runs, two at a time, until the stage log shows its final line.
# Ends on the stage log's last line, not on process names.
R=~/factory-runs/stage-2; G="$(dirname "$0")/grade_run.sh"
while :; do
  pending=()
  for d in "$R"/*/; do
    h="$d/harness"; [ -f "$h/run.json" ] || continue; [ -f "$h/verdict.json" ] && continue
    st=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('status'))" "$h/run.json" 2>/dev/null)
    [ "$st" = "running" ] && continue
    n=$(cat "$h/.grade-tries" 2>/dev/null || echo 0); [ "$n" -ge 3 ] && continue
    echo $((n+1)) > "$h/.grade-tries"; pending+=("${d%/}")
  done
  if [ ${#pending[@]} -gt 0 ]; then printf '%s\n' "${pending[@]}" | head -4 | xargs -P 2 -n 1 "$G"; continue; fi
  grep -q "^stage stage-2: .* counted tokens used" "$R/.logs/stage.log" 2>/dev/null && break
  sleep 30
done
echo "stage 2 grading done"
