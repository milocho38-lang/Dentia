#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

ROOT="$DENTIA_PROJECT_DIR"
RESTART=false
[[ "${1:-}" == "--restart" ]] && RESTART=true

cd "$ROOT"
if [ -n "$(git status --porcelain)" ]; then
  git status --short
  dentia_fail "Working tree has local changes. Commit/stash/review them before update."
fi

dentia_info "Pulling latest master..."
git pull --ff-only origin master

dentia_info "Updating backend dependencies..."
(cd "$ROOT/backend" && .venv/bin/pip install -r requirements.txt && .venv/bin/alembic -c alembic.ini upgrade head)

dentia_info "Updating frontend dependencies and build..."
if [ -f "$ROOT/frontend/package-lock.json" ]; then
  (cd "$ROOT/frontend" && npm ci && rm -rf .next && npm run build)
else
  (cd "$ROOT/frontend" && npm install && rm -rf .next && npm run build)
fi

dentia_info "Update complete."
if $RESTART; then
  "$SCRIPT_DIR/stop_dentia.sh" || true
  "$SCRIPT_DIR/start_dentia.sh"
fi
