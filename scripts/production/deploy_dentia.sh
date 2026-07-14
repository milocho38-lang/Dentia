#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

STARTED_AT="$(date +%s)"
ROOT="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"
STATE_DIR="$ROOT/.run"
mkdir -p "$STATE_DIR"

[ -d "$ROOT/.git" ] || dentia_fail "Git repository not found at $ROOT"
cd "$ROOT"
dentia_require_cmd git
dentia_require_cmd docker

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
OLD_COMMIT="$(git rev-parse --short HEAD)"
dentia_info "Branch: $CURRENT_BRANCH"
dentia_info "Current commit: $OLD_COMMIT"

if [ -n "$(git status --porcelain)" ]; then
  git status --short
  dentia_fail "VPS repository has local changes. Aborting deploy."
fi

dentia_info "Creating mandatory backup..."
BACKUP_PATH="$("$SCRIPT_DIR/backup_dentia.sh" | tail -n 1)"
[ -s "$BACKUP_PATH" ] || dentia_fail "Backup failed or empty: $BACKUP_PATH"

dentia_info "Fetching and fast-forwarding master..."
git fetch origin
git pull --ff-only origin master
NEW_COMMIT="$(git rev-parse --short HEAD)"
printf '%s\n' "$OLD_COMMIT" >"$STATE_DIR/last_deploy_previous_commit"
printf '%s\n' "$NEW_COMMIT" >"$STATE_DIR/last_deploy_commit"
printf '%s\n' "$BACKUP_PATH" >"$STATE_DIR/last_deploy_backup"

dentia_info "Building images without stopping current containers..."
dentia_compose build

dentia_info "Starting updated containers..."
dentia_compose up -d

dentia_info "Applying migrations inside backend container..."
docker exec "$DENTIA_BACKEND_CONTAINER" alembic -c alembic.ini upgrade head

dentia_info "Validating containers..."
dentia_compose ps

if ! dentia_wait_http "$DENTIA_PRODUCTION_BACKEND_HEALTH_URL" 30 2; then
  dentia_warn "Backend healthcheck failed. Recent backend logs:"
  docker logs --tail 120 "$DENTIA_BACKEND_CONTAINER" || true
  dentia_fail "Deploy failed after containers started."
fi

if ! dentia_wait_http "$DENTIA_PRODUCTION_FRONTEND_URL" 30 2; then
  dentia_warn "Frontend check failed. Recent frontend logs:"
  docker logs --tail 120 "$DENTIA_FRONTEND_CONTAINER" || true
  dentia_fail "Deploy failed after containers started."
fi

if [ -n "${DENTIA_DOMAIN_URL:-}" ]; then
  curl -fsS --max-time 10 "$DENTIA_DOMAIN_URL" >/dev/null 2>&1 || dentia_warn "Domain check failed: $DENTIA_DOMAIN_URL"
fi

FINISHED_AT="$(date +%s)"
dentia_info "Deploy OK"
dentia_info "Previous commit: $OLD_COMMIT"
dentia_info "New commit: $NEW_COMMIT"
dentia_info "Backup: $BACKUP_PATH"
dentia_info "Duration: $((FINISHED_AT - STARTED_AT)) seconds"
