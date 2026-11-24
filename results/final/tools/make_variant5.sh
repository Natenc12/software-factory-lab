#!/bin/bash
# make_variant5.sh: copy the corrected records of stages 1 to 2b (~/factory-runs-variants/combined2) to
# ~/factory-runs-variants/corrected5/<stage>/. Repo clones are linked, not copied; combined2 is not touched.
set -e
src=~/factory-runs-variants/combined2; dst=~/factory-runs-variants/corrected5
for st in stage-1 stage-1-confirm stage-2 stage-2b; do
  mkdir -p "$dst/$st"
  for d in "$src/$st"/*/; do
    r=$(basename "$d"); [ -f "$d/harness/run.json" ] || continue
    mkdir -p "$dst/$st/$r"
    rsync -a --no-specials --no-devices --delete --exclude repo "$d" "$dst/$st/$r/"
    [ -e "${d%/}/repo" ] && ln -sfn "$(cd "${d%/}/repo" && pwd -P)" "$dst/$st/$r/repo"
  done
  echo "$st: $(ls "$dst/$st" | wc -l | tr -d ' ') run folders"
done
