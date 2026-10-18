#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

usage() {
  cat <<'EOF'
Usage: rollback_dentia.sh --maintenance --target-sha <40-character-sha>

Performs a code-only rollback to three prebuilt immutable images. It never
downgrades or restores the database. The target commit and each image's OCI
revision label must exactly match the requested full SHA. On any failure after
maintenance begins, application containers remain stopped and both maintenance
markers remain active for manual recovery.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then usage; exit 0; fi
[ "${1:-}" = "--maintenance" ] && [ "${2:-}" = "--target-sha" ] && [ "$#" -eq 3 ] || \
  dentia_fail "Explicit --maintenance and --target-sha are required."
TARGET_SHA="$3"
[[ "$TARGET_SHA" =~ ^[0-9a-f]{40}$ ]] || dentia_fail "A full 40-character target SHA is required."
export DENTIA_IMAGE_TAG="$TARGET_SHA"

ROOT="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"
STATE_DIR="$ROOT/.run"
LOCK_DIR="$STATE_DIR/deploy.lock"
MAINTENANCE_MARKER="$STATE_DIR/maintenance_active"
WRITE_BARRIER_FILE="$(dentia_storage_host_root "$ROOT")/.dentia-maintenance"
MAINTENANCE_ACTIVE=false

rollback_stop_apps() {
  docker stop "$DENTIA_WEBSITE_CONTAINER" "$DENTIA_FRONTEND_CONTAINER" "$DENTIA_BACKEND_CONTAINER" >/dev/null 2>&1 || true
}

rollback_exit_handler() {
  local status="$1"
  trap - EXIT INT TERM
  if [ "$status" -ne 0 ] && [ "$MAINTENANCE_ACTIVE" = true ]; then
    rollback_stop_apps
    dentia_warn "Rollback failed closed: application containers are stopped and maintenance remains active."
  fi
  if [ "${LOCK_ACQUIRED:-false}" = true ]; then rm -rf "$LOCK_DIR"; fi
  exit "$status"
}

rollback_image_identity() {
  local service="$1" image_ref image_id revision
  image_ref="$(dentia_compose config --format json | python3 -c 'import json,sys; print(json.load(sys.stdin)["services"][sys.argv[1]]["image"])' "$service")"
  [ -n "$image_ref" ] || dentia_fail "Target image reference is missing: $service"
  image_id="$(docker image inspect -f '{{.Id}}' "$image_ref" 2>/dev/null || true)"
  revision="$(docker image inspect -f '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$image_ref" 2>/dev/null || true)"
  [[ "$image_id" =~ ^sha256:[0-9a-f]{64}$ ]] || dentia_fail "Target image has no immutable full ID: $service"
  [ "$revision" = "$TARGET_SHA" ] || dentia_fail "Target image OCI revision does not match target SHA: $service"
  printf '%s\n' "$image_id"
}

rollback_verify_runtime() {
  local service="$1" container="$2" expected_id="$3" runtime_id revision
  runtime_id="$(docker inspect -f '{{.Image}}' "$container")"
  revision="$(docker inspect -f '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$container")"
  [ "$runtime_id" = "$expected_id" ] || dentia_fail "Runtime image ID mismatch: $service"
  [ "$revision" = "$TARGET_SHA" ] || dentia_fail "Runtime OCI revision mismatch: $service"
  [ "$(docker inspect -f '{{.State.Running}}' "$container")" = true ] || dentia_fail "Runtime container is not running: $service"
}

mkdir -p "$STATE_DIR"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  dentia_fail "Deploy lock exists: $LOCK_DIR. Inspect it manually; stale locks are never removed automatically."
fi
LOCK_ACQUIRED=true
chmod 700 "$LOCK_DIR" 2>/dev/null || true
printf '%s\n' "$$" >"$LOCK_DIR/pid"
trap 'rollback_exit_handler $?' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

dentia_require_cmd git
dentia_require_cmd docker
dentia_require_cmd python3
[ -d "$ROOT/.git" ] || dentia_fail "Git repository not found at $ROOT"
cd "$ROOT"
[ -z "$(git status --porcelain)" ] || dentia_fail "Repository has local changes. Aborting rollback."
[ "$(git rev-parse --abbrev-ref HEAD)" = master ] || dentia_fail "Production repository must be on master."
git cat-file -e "$TARGET_SHA^{commit}" 2>/dev/null || dentia_fail "Target SHA is not a local commit."
[ "$(git rev-parse "$TARGET_SHA^{commit}")" = "$TARGET_SHA" ] || dentia_fail "Target did not resolve exactly."
[ -s "$STATE_DIR/last_deploy_commit" ] || dentia_fail "Verified deployed commit record is missing."
CURRENT_SHA="$(tr -d '[:space:]' <"$STATE_DIR/last_deploy_commit")"
[[ "$CURRENT_SHA" =~ ^[0-9a-f]{40}$ ]] || dentia_fail "Verified deployed commit record is not a full SHA."
git merge-base --is-ancestor "$TARGET_SHA" "$CURRENT_SHA" || dentia_fail "Rollback target is not an ancestor of the verified deployed commit."

"$SCRIPT_DIR/validate_dentia_production_config.sh"
docker inspect "$DENTIA_DB_CONTAINER" >/dev/null 2>&1 || dentia_fail "Database container not found."
[ "$(docker inspect -f '{{.State.Running}}' "$DENTIA_DB_CONTAINER")" = true ] || dentia_fail "Database container is not running."

BACKEND_IMAGE_ID="$(rollback_image_identity "$DENTIA_BACKEND_SERVICE")"
FRONTEND_IMAGE_ID="$(rollback_image_identity "$DENTIA_FRONTEND_SERVICE")"
WEBSITE_IMAGE_ID="$(rollback_image_identity "$DENTIA_WEBSITE_SERVICE")"

printf 'target_sha=%s\nstarted_at=%s\n' "$TARGET_SHA" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >"$MAINTENANCE_MARKER"
printf 'target_sha=%s\nstarted_at=%s\n' "$TARGET_SHA" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >"$WRITE_BARRIER_FILE"
chmod 600 "$MAINTENANCE_MARKER" "$WRITE_BARRIER_FILE" 2>/dev/null || true
[ -f "$MAINTENANCE_MARKER" ] && [ -f "$WRITE_BARRIER_FILE" ] || dentia_fail "Maintenance barriers were not created."
MAINTENANCE_ACTIVE=true

rollback_stop_apps
for container in "$DENTIA_BACKEND_CONTAINER" "$DENTIA_FRONTEND_CONTAINER" "$DENTIA_WEBSITE_CONTAINER"; do
  [ "$(docker inspect -f '{{.State.Running}}' "$container")" = false ] || dentia_fail "Application container is still running: $container"
done

dentia_compose up -d --no-deps "$DENTIA_BACKEND_SERVICE" "$DENTIA_FRONTEND_SERVICE" "$DENTIA_WEBSITE_SERVICE"
rollback_verify_runtime "$DENTIA_BACKEND_SERVICE" "$DENTIA_BACKEND_CONTAINER" "$BACKEND_IMAGE_ID"
rollback_verify_runtime "$DENTIA_FRONTEND_SERVICE" "$DENTIA_FRONTEND_CONTAINER" "$FRONTEND_IMAGE_ID"
rollback_verify_runtime "$DENTIA_WEBSITE_SERVICE" "$DENTIA_WEBSITE_CONTAINER" "$WEBSITE_IMAGE_ID"
dentia_wait_http "$DENTIA_PRODUCTION_BACKEND_HEALTH_URL" 60 2 || dentia_fail "Backend health check failed."
dentia_wait_http "$DENTIA_PRODUCTION_FRONTEND_URL" 60 2 || dentia_fail "Frontend health check failed."
dentia_wait_http "$DENTIA_PRODUCTION_WEBSITE_URL" 60 2 || dentia_fail "Website health check failed."

printf '%s\n' "$CURRENT_SHA" >"$STATE_DIR/last_deploy_previous_commit"
printf '%s\n' "$TARGET_SHA" >"$STATE_DIR/last_deploy_commit"
rm -f "$WRITE_BARRIER_FILE" "$MAINTENANCE_MARKER"
[ ! -e "$WRITE_BARRIER_FILE" ] && [ ! -e "$MAINTENANCE_MARKER" ] || dentia_fail "Maintenance barriers could not be cleared."
MAINTENANCE_ACTIVE=false

dentia_info "Rollback complete: $CURRENT_SHA -> $TARGET_SHA"
dentia_info "Database schema and clinical storage were not downgraded or restored."
