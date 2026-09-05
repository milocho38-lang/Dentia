#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

usage() {
  cat <<'EOF'
Usage: deploy_dentia.sh [--help]

Runs the production deploy workflow. It creates and semantically verifies a
mandatory backup before git pull/build/recreate. It does not repair storage
during deploy; run prepare_dentia_persistent_storage.sh first if needed.

Safe order:
  preflight -> backup + verify -> git pull -> build -> one-off Alembic
  -> recreate backend/frontend/website -> healthchecks.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi
[ "$#" -eq 0 ] || dentia_fail "Unknown argument: $1"

STARTED_AT="$(date +%s)"
ROOT="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"
STATE_DIR="$ROOT/.run"
mkdir -p "$STATE_DIR"

[ -d "$ROOT/.git" ] || dentia_fail "Git repository not found at $ROOT"
cd "$ROOT"
dentia_require_cmd git
dentia_require_cmd docker

dentia_info "Validating production configuration..."
"$SCRIPT_DIR/validate_dentia_production_config.sh"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
OLD_COMMIT="$(git rev-parse --short HEAD)"
dentia_info "Branch: $CURRENT_BRANCH"
dentia_info "Current commit: $OLD_COMMIT"

HOST_STORAGE_ROOT="$(dentia_storage_host_root "$ROOT")"
dentia_assert_storage_path_safe "$HOST_STORAGE_ROOT"
[ -d "$HOST_STORAGE_ROOT" ] || dentia_fail "Persistent storage directory is missing: $HOST_STORAGE_ROOT. Run prepare_dentia_persistent_storage.sh before deploy."
[ -w "$HOST_STORAGE_ROOT" ] || dentia_fail "Persistent storage directory is not writable: $HOST_STORAGE_ROOT"

if docker inspect "$DENTIA_BACKEND_CONTAINER" >/dev/null 2>&1; then
  MOUNTS_JSON="$(docker inspect "$DENTIA_BACKEND_CONTAINER" --format '{{json .Mounts}}')"
  MOUNTED="$(
    python3 - "$DENTIA_BACKEND_STORAGE_CONTAINER_PATH" "$MOUNTS_JSON" <<'PY'
import json, sys
target = sys.argv[1]
mounts = json.loads(sys.argv[2])
print("yes" if any(m.get("Destination") == target for m in mounts) else "no")
PY
  )"
  if [ "$MOUNTED" != "yes" ]; then
    dentia_warn "Backend storage is not mounted yet. Deploy will require compose mount to protect /app/storage."
    dentia_warn "If files still live only inside the container, run prepare_dentia_persistent_storage.sh --apply before deploy."
  fi
fi

if [ -n "$(git status --porcelain)" ]; then
  git status --short
  dentia_fail "VPS repository has local changes. Aborting deploy."
fi

dentia_info "Creating mandatory backup..."
BACKUP_PATH="$("$SCRIPT_DIR/backup_dentia.sh" | tail -n 1)"
[ -d "$BACKUP_PATH" ] || dentia_fail "Backup failed or missing package directory: $BACKUP_PATH"

dentia_info "Verifying mandatory backup..."
"$SCRIPT_DIR/verify_dentia_backup.sh" "$BACKUP_PATH" >/dev/null || dentia_fail "Backup verification failed. Deploy aborted before git pull."

dentia_info "Fetching and fast-forwarding master..."
git fetch origin
git pull --ff-only origin master
NEW_COMMIT="$(git rev-parse --short HEAD)"
printf '%s\n' "$OLD_COMMIT" >"$STATE_DIR/last_deploy_previous_commit"
printf '%s\n' "$NEW_COMMIT" >"$STATE_DIR/last_deploy_commit"
printf '%s\n' "$BACKUP_PATH" >"$STATE_DIR/last_deploy_backup"

dentia_info "Building images without stopping current containers..."
dentia_compose build

dentia_info "Applying migrations with the newly built backend image before recreating application containers..."
dentia_compose run --rm --no-deps "$DENTIA_BACKEND_SERVICE" alembic -c alembic.ini upgrade head

dentia_info "Verifying Alembic head with the newly built backend image..."
dentia_compose run --rm --no-deps "$DENTIA_BACKEND_SERVICE" alembic -c alembic.ini current

dentia_info "Recreating backend, frontend and public website..."
dentia_compose up -d --no-deps "$DENTIA_BACKEND_SERVICE"
if ! dentia_wait_http "$DENTIA_PRODUCTION_BACKEND_HEALTH_URL" 30 2; then
  dentia_warn "Backend healthcheck failed after backend recreate. Recent backend logs:"
  docker logs --tail 120 "$DENTIA_BACKEND_CONTAINER" || true
  dentia_fail "Deploy failed after backend recreate."
fi
dentia_compose up -d --no-deps "$DENTIA_FRONTEND_SERVICE"
dentia_compose up -d --no-deps "$DENTIA_WEBSITE_SERVICE"

dentia_info "Validating containers..."
dentia_compose ps

if ! dentia_wait_http "$DENTIA_PRODUCTION_FRONTEND_URL" 30 2; then
  dentia_warn "Frontend check failed. Recent frontend logs:"
  docker logs --tail 120 "$DENTIA_FRONTEND_CONTAINER" || true
  dentia_fail "Deploy failed after containers started."
fi

if ! dentia_wait_http "$DENTIA_PRODUCTION_WEBSITE_URL" 30 2; then
  dentia_warn "Website check failed. Recent website logs:"
  docker logs --tail 120 "$DENTIA_WEBSITE_CONTAINER" || true
  dentia_fail "Deploy failed after website recreate."
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
