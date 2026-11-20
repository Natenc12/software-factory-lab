#!/usr/bin/env bash
# lab-down <run-id> [--keep-branch]
# Remove a run's sandbox worktree (its SQLite database lives inside it and goes with it).
# Refuses if the worktree has uncommitted changes or the branch has unpushed commits.
# Never touches the remote branch or the PR.
set -euo pipefail

RUN="${1:?usage: lab-down <run-id> [--keep-branch]}"
[[ "$RUN" =~ ^[A-Za-z0-9-]+$ ]] || { echo "bad run id: $RUN"; exit 1; }
REPO="${LAB_REPO:-$HOME/repos/pipeline-lab}"
ROOT="${LAB_WORKTREES:-$HOME/repos/lab-worktrees}"
WT="$ROOT/$RUN"

if [ -d "$WT" ]; then
  if [ -n "$(git -C "$WT" status --porcelain)" ]; then
    echo "refusing: $WT has uncommitted changes"; git -C "$WT" status --short | head; exit 1
  fi
  BRANCH=$(git -C "$WT" rev-parse --abbrev-ref HEAD)
  git -C "$WT" fetch --quiet origin || true
  if git -C "$WT" rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1; then
    ahead=$(git -C "$WT" rev-list --count '@{u}..HEAD')
  else
    ahead=$(git -C "$WT" rev-list --count origin/main..HEAD)
  fi
  if [ "$ahead" != "0" ]; then
    echo "refusing: branch $BRANCH has $ahead commit(s) not on GitHub. Push first."; exit 1
  fi
  # Ignored files (.env, lab.db, .venv) do not block removal; tracked or untracked changes would.
  git -C "$REPO" worktree remove "$WT"
  [ "${2:-}" = "--keep-branch" ] || git -C "$REPO" branch -D "$BRANCH" >/dev/null 2>&1 || true
fi
git -C "$REPO" worktree prune
echo "sandbox $RUN removed (remote branch and PR left as they are)"
