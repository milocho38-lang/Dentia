#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

# The deploy runner owns these verified paths and passes them to every
# production helper it launches. Other scripts sourcing dentia_common do not
# leak their resolved defaults into unrelated child processes.
export DENTIA_PROJECT_DIR DENTIA_PRODUCTION_DIR DENTIA_ENV_FILE

usage() {
  cat <<'EOF'
Usage: deploy_dentia.sh --maintenance --target-sha <40-character-sha>

Runs the production deploy workflow with an explicit maintenance window. It
does not repair storage during deploy; run
prepare_dentia_persistent_storage.sh first if needed.

Safe order:
  preflight -> git pull -> build -> stop application writers
  -> backup + verify + temporary restore -> one-off Alembic
  -> validate invariants -> start backend/frontend/website -> healthchecks.

Before migrations start, a failure attempts to restart the unchanged old
containers. After migrations start, every failure keeps maintenance active and
never starts old application containers automatically.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi
[ "${1:-}" = "--maintenance" ] && [ "${2:-}" = "--target-sha" ] && [ "$#" -eq 3 ] || \
  dentia_fail "Explicit --maintenance and --target-sha are required."
TARGET_SHA="$3"
[[ "$TARGET_SHA" =~ ^[0-9a-f]{40}$ ]] || dentia_fail "A full 40-character target SHA is required."
[ -z "${DENTIA_DEPLOY_TARGET_SHA:-}" ] || [ "$DENTIA_DEPLOY_TARGET_SHA" = "$TARGET_SHA" ] || \
  dentia_fail "Launcher SHA and runner SHA do not match."

deploy_db_scalar() {
  local sql="$1"
  docker exec "$DENTIA_DB_CONTAINER" psql -v ON_ERROR_STOP=1 -U "$DENTIA_DB_USER" \
    -d "$DENTIA_DB_NAME" -tAc "$sql" | tr -d '[:space:]'
}

deploy_current_revision() {
  deploy_db_scalar 'SELECT version_num FROM alembic_version LIMIT 1;'
}

deploy_assert_no_unknown_writers() {
  local unknown
  unknown="$(deploy_db_scalar "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid() AND backend_type = 'client backend' AND coalesce(application_name, '') NOT IN ('dentia-maintenance');")"
  if [ "$unknown" != "0" ]; then
    docker exec "$DENTIA_DB_CONTAINER" psql -v ON_ERROR_STOP=1 -U "$DENTIA_DB_USER" \
      -d "$DENTIA_DB_NAME" -At -F '|' -c \
      "SELECT pid, usename, coalesce(application_name, ''), coalesce(client_addr::text, 'local'), state FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid() AND backend_type = 'client backend' AND coalesce(application_name, '') NOT IN ('dentia-maintenance') ORDER BY pid;" >&2
    dentia_fail "Unknown database client sessions remain. No sessions were terminated."
  fi
}

deploy_enable_write_barrier() {
  printf 'target_sha=%s\nstarted_at=%s\n' "$TARGET_SHA" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >"$WRITE_BARRIER_FILE"
  chmod 600 "$WRITE_BARRIER_FILE" 2>/dev/null || true
  [ -f "$WRITE_BARRIER_FILE" ] || dentia_fail "Maintenance write barrier was not created."
}

deploy_disable_write_barrier() {
  [ -f "$WRITE_BARRIER_FILE" ] || dentia_fail "Maintenance write barrier disappeared before final release."
  rm -f "$WRITE_BARRIER_FILE"
  [ ! -e "$WRITE_BARRIER_FILE" ] || dentia_fail "Maintenance write barrier could not be removed."
}

deploy_resolve_target_image() {
  local service="$1" image_ref image_id revision
  image_ref="$(dentia_compose images -q "$service")"
  [ -n "$image_ref" ] || dentia_fail "Built image is missing for service: $service"
  image_id="$(docker image inspect -f '{{.Id}}' "$image_ref")"
  revision="$(docker image inspect -f '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$image_ref")"
  [[ "$image_id" =~ ^sha256:[0-9a-f]{64}$ ]] || dentia_fail "Built image identity is not a full sha256 digest: $service"
  [ "$revision" = "$TARGET_SHA" ] || dentia_fail "Built image revision label does not match target SHA: $service"
  printf '%s\n' "$image_id"
}

deploy_snapshot_stable_data() {
  local output="$1"
  docker exec "$DENTIA_DB_CONTAINER" psql -v ON_ERROR_STOP=1 -U "$DENTIA_DB_USER" \
    -d "$DENTIA_DB_NAME" -At -F '|' <<'SQL' >"$output"
SELECT 'usuarios', count(*), md5(coalesce(string_agg(id::text || ':' || password_hash, ',' ORDER BY id), '')) FROM usuarios
UNION ALL
SELECT 'usuario_roles', count(*), md5(coalesce(string_agg(id::text || ':' || usuario_id::text || ':' || rol_id::text, ',' ORDER BY id), '')) FROM usuario_roles
UNION ALL
SELECT 'roles', count(*), md5(coalesce(string_agg(id::text || ':' || code, ',' ORDER BY id), '')) FROM roles
UNION ALL
SELECT 'auth_sessions', count(*), md5(coalesce(string_agg(id::text || ':' || usuario_id::text, ',' ORDER BY id), '')) FROM auth_sessions
UNION ALL
SELECT 'auditoria_eventos', count(*), md5(coalesce(string_agg(id::text, ',' ORDER BY id), '')) FROM auditoria_eventos
UNION ALL
SELECT 'pacientes', count(*), md5(coalesce(string_agg(id::text || ':' || empresa_id::text, ',' ORDER BY id), '')) FROM pacientes
ORDER BY 1;
SQL
  [ -s "$output" ] || dentia_fail "Stable data snapshot is empty."
}

deploy_assert_pre_migration_invariants() {
  local expected="${DENTIA_EXPECTED_PRE_DEPLOY_REVISION:-20260926_0045}"
  local revision duplicate_emails
  revision="$(deploy_current_revision)"
  [ "$revision" = "$expected" ] || dentia_fail "Unexpected pre-deploy Alembic revision: $revision (expected $expected)."
  duplicate_emails="$(deploy_db_scalar "SELECT count(*) FROM (SELECT correo_normalizado FROM usuarios GROUP BY correo_normalizado HAVING count(*) > 1) duplicates;")"
  [ "$duplicate_emails" = "0" ] || dentia_fail "Existing normalized email duplicates block migration 0046."
}

deploy_assert_post_migration_invariants() {
  local expected="${DENTIA_EXPECTED_POST_DEPLOY_REVISION:-20261006_0047}"
  local revision
  revision="$(deploy_current_revision)"
  [ "$revision" = "$expected" ] || dentia_fail "Unexpected post-deploy Alembic revision: $revision (expected $expected)."
  [ "$(deploy_db_scalar "SELECT count(*) FROM usuarios WHERE username IS DISTINCT FROM correo_normalizado OR username_normalizado IS DISTINCT FROM correo_normalizado;")" = "0" ] || dentia_fail "Legacy login backfill invariant failed."
  [ "$(deploy_db_scalar "SELECT count(*) FROM (SELECT username_normalizado FROM usuarios GROUP BY username_normalizado HAVING count(*) > 1) duplicates;")" = "0" ] || dentia_fail "Username uniqueness invariant failed."
  [ "$(deploy_db_scalar "SELECT count(*) FROM patient_import_sources;")" = "0" ] || dentia_fail "Patient import sources must be empty immediately after rollout."
  [ "$(deploy_db_scalar "SELECT count(*) FROM patient_external_references;")" = "0" ] || dentia_fail "Patient external references must be empty immediately after rollout."
  [ "$(deploy_db_scalar "SELECT count(*) FROM permisos WHERE code = 'patients.import' AND is_active;")" = "1" ] || dentia_fail "Active patients.import permission was not created exactly once."
  [ "$(deploy_db_scalar "SELECT count(*) FROM rol_permisos rp JOIN permisos p ON p.id = rp.permiso_id JOIN roles r ON r.id = rp.rol_id WHERE p.code = 'patients.import' AND rp.is_active AND r.code NOT IN ('ADMINISTRATOR', 'DENTIST_ADMIN');")" = "0" ] || dentia_fail "patients.import was actively assigned to an unauthorized role."
  [ "$(deploy_db_scalar "SELECT count(*) FROM roles r WHERE r.code IN ('ADMINISTRATOR', 'DENTIST_ADMIN') AND r.is_active AND NOT EXISTS (SELECT 1 FROM rol_permisos rp JOIN permisos p ON p.id = rp.permiso_id WHERE rp.rol_id = r.id AND p.code = 'patients.import' AND p.is_active AND rp.is_active);")" = "0" ] || dentia_fail "Active patients.import is missing from an active authorized role."
}

deploy_stop_application_writers() {
  docker stop "$DENTIA_WEBSITE_CONTAINER" "$DENTIA_FRONTEND_CONTAINER" "$DENTIA_BACKEND_CONTAINER" >/dev/null
  local container running
  for container in "$DENTIA_BACKEND_CONTAINER" "$DENTIA_FRONTEND_CONTAINER" "$DENTIA_WEBSITE_CONTAINER"; do
    running="$(docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null || true)"
    [ "$running" = "false" ] || dentia_fail "Application container is still running: $container"
  done
}

deploy_cleanup_temporary_restore() {
  if [ -n "${RESTORE_DB:-}" ]; then
    docker exec "$DENTIA_DB_CONTAINER" dropdb -U "$DENTIA_DB_USER" --if-exists "$RESTORE_DB" >/dev/null 2>&1 || true
  fi
  if [ -n "${RESTORE_STORAGE:-}" ] && [[ "$RESTORE_STORAGE" == /tmp/dentia_restore_deploy_* ]]; then
    rm -rf "$RESTORE_STORAGE"
  fi
}

deploy_restart_old_containers() {
  dentia_warn "Failure occurred before migrations. Attempting safe restart of unchanged old containers."
  docker start "$DENTIA_BACKEND_CONTAINER" >/dev/null
  dentia_wait_http "$DENTIA_PRODUCTION_BACKEND_HEALTH_URL" 30 2 || return 1
  docker start "$DENTIA_FRONTEND_CONTAINER" "$DENTIA_WEBSITE_CONTAINER" >/dev/null
  dentia_wait_http "$DENTIA_PRODUCTION_FRONTEND_URL" 30 2 || return 1
  dentia_wait_http "$DENTIA_PRODUCTION_WEBSITE_URL" 30 2 || return 1
}

deploy_exit_handler() {
  local status="$1"
  trap - EXIT INT TERM
  deploy_cleanup_temporary_restore
  if [ "$status" -ne 0 ] && [ "${MAINTENANCE_ACTIVE:-false}" = "true" ]; then
    if [ "${MIGRATION_STARTED:-false}" = "false" ]; then
      if deploy_restart_old_containers; then
        rm -f "$WRITE_BARRIER_FILE"
        rm -f "$MAINTENANCE_MARKER"
        dentia_warn "Old application containers recovered; maintenance cleared."
      else
        dentia_warn "Old application recovery failed; maintenance marker retained."
      fi
    else
      docker stop "$DENTIA_WEBSITE_CONTAINER" "$DENTIA_FRONTEND_CONTAINER" "$DENTIA_BACKEND_CONTAINER" >/dev/null 2>&1 || true
      if [ ! -f "$MAINTENANCE_MARKER" ]; then
        if printf 'target_sha=%s\nfailed_at=%s\n' "$TARGET_SHA" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >"$MAINTENANCE_MARKER"; then
          chmod 600 "$MAINTENANCE_MARKER" 2>/dev/null || true
        else
          dentia_warn "Could not re-arm the state marker; all application containers remain stopped."
        fi
      fi
      if [ ! -f "$WRITE_BARRIER_FILE" ]; then
        if printf 'target_sha=%s\nrearmed_at=%s\n' "$TARGET_SHA" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >"$WRITE_BARRIER_FILE"; then
          chmod 600 "$WRITE_BARRIER_FILE" 2>/dev/null || true
        else
          dentia_warn "Could not re-arm the file barrier; all application containers remain stopped."
        fi
      fi
      dentia_warn "Maintenance remains active because migrations started. Do not start old application containers."
    fi
  fi
  if [ -n "${DEPLOY_LOCK_DIR:-}" ] && [ "${DEPLOY_LOCK_DIR:-}" = "${STATE_DIR:-}/deploy.lock" ]; then
    rm -rf "$DEPLOY_LOCK_DIR"
  fi
  exit "$status"
}

STARTED_AT="$(date +%s)"
ROOT="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"
STATE_DIR="$ROOT/.run"
mkdir -p "$STATE_DIR"
MAINTENANCE_MARKER="$STATE_DIR/maintenance_active"
DEPLOY_LOCK_DIR="$STATE_DIR/deploy.lock"
MAINTENANCE_ACTIVE=false
MIGRATION_STARTED=false
RESTORE_DB=""
RESTORE_STORAGE=""

if ! mkdir "$DEPLOY_LOCK_DIR" 2>/dev/null; then
  dentia_fail "Deploy lock exists: $DEPLOY_LOCK_DIR. Inspect its pid and maintenance state manually; stale locks are never removed automatically."
fi
chmod 700 "$DEPLOY_LOCK_DIR" 2>/dev/null || true
printf '%s\n' "$$" >"$DEPLOY_LOCK_DIR/pid"
trap 'deploy_exit_handler $?' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

[ -d "$ROOT/.git" ] || dentia_fail "Git repository not found at $ROOT"
cd "$ROOT"
dentia_require_cmd git
dentia_require_cmd docker
dentia_require_cmd python3

dentia_info "Validating production configuration..."
"$SCRIPT_DIR/validate_dentia_production_config.sh"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
DEPLOYED_COMMIT_FILE="$STATE_DIR/last_deploy_commit"
[ -s "$DEPLOYED_COMMIT_FILE" ] || dentia_fail "Verified deployed commit record is missing: $DEPLOYED_COMMIT_FILE"
DEPLOYED_COMMIT_REF="$(tr -d '[:space:]' <"$DEPLOYED_COMMIT_FILE")"
OLD_COMMIT="$(git rev-parse "$DEPLOYED_COMMIT_REF^{commit}" 2>/dev/null || true)"
[ -n "$OLD_COMMIT" ] || dentia_fail "Deployed commit record does not resolve to a local commit."
CHECKOUT_COMMIT="$(git rev-parse HEAD)"
if [ "$CHECKOUT_COMMIT" != "$OLD_COMMIT" ] && [ "$CHECKOUT_COMMIT" != "$TARGET_SHA" ]; then
  dentia_fail "Clean checkout matches neither the verified deployed commit nor the approved retry target."
fi
OLD_BACKEND_IMAGE_ID="$(docker inspect -f '{{.Image}}' "$DENTIA_BACKEND_CONTAINER")"
OLD_FRONTEND_IMAGE_ID="$(docker inspect -f '{{.Image}}' "$DENTIA_FRONTEND_CONTAINER")"
OLD_WEBSITE_IMAGE_ID="$(docker inspect -f '{{.Image}}' "$DENTIA_WEBSITE_CONTAINER")"
for image_id in "$OLD_BACKEND_IMAGE_ID" "$OLD_FRONTEND_IMAGE_ID" "$OLD_WEBSITE_IMAGE_ID"; do
  [[ "$image_id" =~ ^sha256:[0-9a-f]{64}$ ]] || dentia_fail "Runtime container image identity is not a full sha256 digest."
done
dentia_info "Branch: $CURRENT_BRANCH"
dentia_info "Verified deployed commit: $OLD_COMMIT"
[ "$CURRENT_BRANCH" = "master" ] || dentia_fail "Production repository must be on master."
docker inspect "$DENTIA_DB_CONTAINER" >/dev/null 2>&1 || dentia_fail "Database container not found."
[ "$(docker inspect -f '{{.State.Running}}' "$DENTIA_DB_CONTAINER")" = "true" ] || dentia_fail "Database container is not running."

HOST_STORAGE_ROOT="$(dentia_storage_host_root "$ROOT")"
WRITE_BARRIER_FILE="$HOST_STORAGE_ROOT/.dentia-maintenance"
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
    dentia_fail "Backend persistent storage mount is missing."
  fi
fi

if [ -n "$(git status --porcelain)" ]; then
  git status --short
  dentia_fail "VPS repository has local changes. Aborting deploy."
fi

deploy_assert_pre_migration_invariants

dentia_info "Fetching the exact approved target SHA..."
git fetch origin
FETCHED_MASTER="$(git rev-parse refs/remotes/origin/master)"
[ "$FETCHED_MASTER" = "$TARGET_SHA" ] || dentia_fail "origin/master moved or does not match the approved target SHA."
git merge-base --is-ancestor "$OLD_COMMIT" "$TARGET_SHA" || dentia_fail "Target SHA is not a fast-forward of the deployed commit."
git merge --ff-only "$TARGET_SHA"
NEW_COMMIT="$(git rev-parse HEAD)"
[ "$NEW_COMMIT" = "$TARGET_SHA" ] || dentia_fail "Checkout does not match the approved target SHA after fast-forward."
[ -z "$(git status --porcelain)" ] || dentia_fail "Repository became dirty after fast-forward."

dentia_info "Building images without stopping current containers..."
DENTIA_BUILD_REVISION="$TARGET_SHA" dentia_compose build
TARGET_BACKEND_IMAGE_ID="$(deploy_resolve_target_image "$DENTIA_BACKEND_SERVICE")"
TARGET_FRONTEND_IMAGE_ID="$(deploy_resolve_target_image "$DENTIA_FRONTEND_SERVICE")"
TARGET_WEBSITE_IMAGE_ID="$(deploy_resolve_target_image "$DENTIA_WEBSITE_SERVICE")"

dentia_info "Entering maintenance and stopping all application writers..."
deploy_enable_write_barrier
printf 'started_at=%s\nold_commit=%s\nnew_commit=%s\n' \
  "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$OLD_COMMIT" "$NEW_COMMIT" >"$MAINTENANCE_MARKER"
chmod 600 "$MAINTENANCE_MARKER" 2>/dev/null || true
MAINTENANCE_ACTIVE=true
deploy_stop_application_writers
deploy_assert_pre_migration_invariants
deploy_assert_no_unknown_writers

BEFORE_SNAPSHOT="$STATE_DIR/deploy_before_stable.tsv"
AFTER_SNAPSHOT="$STATE_DIR/deploy_after_stable.tsv"
umask 077
deploy_snapshot_stable_data "$BEFORE_SNAPSHOT"

dentia_info "Creating and verifying a consistent backup with writers stopped..."
BACKUP_PATH="$(
  DENTIA_BACKUP_DEPLOYED_COMMIT="$OLD_COMMIT" \
  DENTIA_BACKUP_TARGET_COMMIT="$TARGET_SHA" \
  DENTIA_BACKUP_BACKEND_IMAGE_ID="$OLD_BACKEND_IMAGE_ID" \
  DENTIA_BACKUP_FRONTEND_IMAGE_ID="$OLD_FRONTEND_IMAGE_ID" \
  DENTIA_BACKUP_WEBSITE_IMAGE_ID="$OLD_WEBSITE_IMAGE_ID" \
  DENTIA_BACKUP_TARGET_BACKEND_IMAGE_ID="$TARGET_BACKEND_IMAGE_ID" \
  DENTIA_BACKUP_TARGET_FRONTEND_IMAGE_ID="$TARGET_FRONTEND_IMAGE_ID" \
  DENTIA_BACKUP_TARGET_WEBSITE_IMAGE_ID="$TARGET_WEBSITE_IMAGE_ID" \
    "$SCRIPT_DIR/backup_dentia.sh" --no-prune | tail -n 1
)"
[ -d "$BACKUP_PATH" ] || dentia_fail "Backup failed or package directory is missing: $BACKUP_PATH"
"$SCRIPT_DIR/verify_dentia_backup.sh" "$BACKUP_PATH" >/dev/null

RESTORE_SUFFIX="$(date -u +%Y%m%d_%H%M%S)_$$"
RESTORE_DB="dentia_restore_deploy_$RESTORE_SUFFIX"
RESTORE_STORAGE="/tmp/dentia_restore_deploy_$RESTORE_SUFFIX/storage"
dentia_info "Testing backup restoration in an isolated database and storage path..."
RESTORE_OUTPUT="$("$SCRIPT_DIR/restore_dentia_backup.sh" --backup "$BACKUP_PATH" --temporary \
  --database-name "$RESTORE_DB" --storage-dir "$RESTORE_STORAGE")"
printf '%s\n' "$RESTORE_OUTPUT" | grep -qx 'RESTORE_VALID' || dentia_fail "Temporary restore did not report RESTORE_VALID."
deploy_cleanup_temporary_restore
RESTORE_DB=""
RESTORE_STORAGE=""

deploy_assert_no_unknown_writers
MIGRATION_STARTED=true
dentia_info "Applying migrations with the newly built backend image while maintenance is active..."
dentia_compose run --rm --no-deps "$DENTIA_BACKEND_SERVICE" alembic -c alembic.ini upgrade head

dentia_info "Verifying Alembic head and rollout invariants..."
deploy_assert_post_migration_invariants
deploy_snapshot_stable_data "$AFTER_SNAPSHOT"
cmp -s "$BEFORE_SNAPSHOT" "$AFTER_SNAPSHOT" || \
  dentia_fail "Stable IDs, password hashes, roles, sessions, audit history or patients changed during migration."

dentia_info "Starting the new backend..."
dentia_compose up -d --no-deps "$DENTIA_BACKEND_SERVICE"
if ! dentia_wait_http "$DENTIA_PRODUCTION_BACKEND_HEALTH_URL" 30 2; then
  dentia_warn "Backend healthcheck failed after backend recreate. Recent backend logs:"
  docker logs --tail 120 "$DENTIA_BACKEND_CONTAINER" || true
  dentia_fail "Deploy failed after backend recreate."
fi
dentia_info "Starting the frontend and public website..."
dentia_compose up -d --no-deps "$DENTIA_FRONTEND_SERVICE"
dentia_compose up -d --no-deps "$DENTIA_WEBSITE_SERVICE"
[ "$(docker inspect -f '{{.Image}}' "$DENTIA_BACKEND_CONTAINER")" = "$TARGET_BACKEND_IMAGE_ID" ] || dentia_fail "Backend container is not running the approved target image."
[ "$(docker inspect -f '{{.Image}}' "$DENTIA_FRONTEND_CONTAINER")" = "$TARGET_FRONTEND_IMAGE_ID" ] || dentia_fail "Frontend container is not running the approved target image."
[ "$(docker inspect -f '{{.Image}}' "$DENTIA_WEBSITE_CONTAINER")" = "$TARGET_WEBSITE_IMAGE_ID" ] || dentia_fail "Website container is not running the approved target image."

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

dentia_info "Running an internal read-only route/dependency smoke while the public write barrier remains active..."
dentia_compose run --rm --no-deps "$DENTIA_BACKEND_SERVICE" python - <<'PY'
from app.main import create_app

expected = {
    ("GET", "/api/patient-imports/dentalink/sources"),
    ("POST", "/api/patient-imports/dentalink/sources"),
    ("POST", "/api/patient-imports/dentalink/preview"),
    ("POST", "/api/patient-imports/dentalink/confirm"),
}
found = set()
for route in create_app().routes:
    key_candidates = {(method, route.path) for method in (getattr(route, "methods", set()) or set())}
    matching = expected & key_candidates
    if not matching:
        continue
    dependency_names = {
        getattr(dependency.call, "__name__", repr(dependency.call))
        for dependency in route.dependant.dependencies
    }
    if "permission_dependency" not in dependency_names:
        raise SystemExit(f"missing permission dependency: {sorted(matching)}")
    found.update(matching)
if found != expected:
    raise SystemExit(f"missing importer routes: {sorted(expected - found)}")
print("INTERNAL_IMPORTER_ROUTE_SMOKE_OK")
PY

printf '%s\n' "$OLD_COMMIT" >"$STATE_DIR/last_deploy_previous_commit"
printf '%s\n' "$NEW_COMMIT" >"$STATE_DIR/last_deploy_commit"
printf '%s\n' "$BACKUP_PATH" >"$STATE_DIR/last_deploy_backup"
FINISHED_AT="$(date +%s)"
dentia_info "All gates passed. Removing the public write barrier as the final availability transition."
rm -f "$MAINTENANCE_MARKER"
deploy_disable_write_barrier
MAINTENANCE_ACTIVE=false
dentia_info "Deploy OK"
dentia_info "Previous commit: $OLD_COMMIT"
dentia_info "New commit: $NEW_COMMIT"
dentia_info "Backup: $BACKUP_PATH"
dentia_info "Duration: $((FINISHED_AT - STARTED_AT)) seconds"
