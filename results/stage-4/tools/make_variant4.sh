#!/bin/bash
# make_variant4.sh <name>: copy every stage 4 run's records (not its repo clone) to ~/factory-runs-variants/<name>/<stage>/
set -e
for st in stage-4-hono stage-4-sqlglot; do
  dst=~/factory-runs-variants/$1/$st; mkdir -p "$dst"
  for d in ~/factory-runs/$st/*/; do
    r=$(basename "$d"); [ -f "$d/harness/run.json" ] || continue
    mkdir -p "$dst/$r"
    rsync -a --no-specials --no-devices --delete --exclude repo --exclude scratch --exclude arm "$d" "$dst/$r/"
    [ -e "${d%/}/repo" ] && ln -sfn "${d%/}/repo" "$dst/$r/repo"
  done
  echo "$st: $(ls "$dst" | wc -l | tr -d ' ') run folders"
done
