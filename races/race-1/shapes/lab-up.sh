#!/usr/bin/env bash
# lab-up <run-id> <branch-slug>
# Make an isolated sandbox for one benchmark run: its own git worktree on a new branch from
# origin/main, its own SQLite database inside the sandbox, its own .env. Never edits the owner's
# checkout (~/repos/pipeline-lab) beyond fetch and the worktree bookkeeping git keeps there.
set -euo pipefail

RUN="${1:?usage: lab-up <run-id> <branch-slug>}"
SLUG="${2:?usage: lab-up <run-id> <branch-slug>}"
[[ "$RUN" =~ ^[A-Za-z0-9-]+$ ]] || { echo "bad run id: $RUN"; exit 1; }
[[ "$SLUG" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "bad slug (use lowercase, digits, dashes): $SLUG"; exit 1; }
REPO="${LAB_REPO:-$HOME/repos/pipeline-lab}"
ROOT="${LAB_WORKTREES:-$HOME/repos/lab-worktrees}"
RUNS="${LAB_RUNS:-$HOME/repos/pipeline-bench/runs}"
WT="$ROOT/$RUN"
BRANCH="$(printf '%s' "$RUN" | tr '[:upper:]' '[:lower:]')/$SLUG"
DB="$WT/lab.db"

[ -e "$WT" ] && { echo "sandbox already exists: $WT"; exit 1; }
mkdir -p "$ROOT" "$RUNS/$RUN"
git -C "$REPO" fetch --quiet origin
git -C "$REPO" worktree add --quiet -b "$BRANCH" "$WT" origin/main

echo "LAB_DB=$DB" > "$WT/.env"

# Keep the sandbox's own files out of commits even if the repo's .gitignore misses them.
EXCLUDE="$(git -C "$WT" rev-parse --path-format=absolute --git-common-dir)/info/exclude"
for p in .env lab.db 'lab_*.db' .venv/; do
  git -C "$WT" check-ignore -q "${p%/}" 2>/dev/null && continue
  mkdir -p "$(dirname "$EXCLUDE")"
  grep -qxF "$p" "$EXCLUDE" 2>/dev/null || echo "$p" >> "$EXCLUDE"
done

(
  cd "$WT"
  uv sync --quiet --extra dev
  # Same as CI: migrate twice, so a migration that cannot re-run fails here, not in CI.
  LAB_DB="$DB" uv run --quiet python scripts/migrate.py >/dev/null
  LAB_DB="$DB" uv run --quiet python scripts/migrate.py >/dev/null
)

BASE="$(git -C "$WT" rev-parse --short HEAD)"
cat > "$RUNS/$RUN/state.json" <<JSON
{"run": "$RUN", "branch": "$BRANCH", "worktree": "$WT", "database": "$DB",
 "created": "$(date -u +%Y-%m-%dT%H:%M:%SZ)", "base": "$BASE"}
JSON

echo "sandbox ready (baseline not yet run)"
echo "  folder:   $WT"
echo "  branch:   $BRANCH (from origin/main $BASE)"
echo "  database: $DB (migrated twice)"
echo "  pages:    $RUNS/$RUN/"
echo "  baseline: cd $WT && uv run pytest -q"
