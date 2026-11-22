#!/bin/bash
# make_variant.sh <name>: copy every stage-1 run's records (not its repo clone) to ~/factory-runs-variants/<name>/stage-1/
set -e
dst=~/factory-runs-variants/$1/stage-1; mkdir -p "$dst"
for d in ~/factory-runs/stage-1/*/; do
  r=$(basename "$d"); [ -f "$d/harness/run.json" ] || continue
  mkdir -p "$dst/$r"
  rsync -a --no-specials --no-devices --delete --exclude repo "$d" "$dst/$r/"
  ln -sfn "${d%/}/repo" "$dst/$r/repo"
done
ls "$dst" | wc -l
