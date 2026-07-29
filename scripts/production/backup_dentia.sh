#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

usage() {
  cat <<'EOF'
Usage: backup_dentia.sh [--no-prune] [--help]

Creates a complete Dentia backup package with:
  database.dump
  storage.tar.gz
  document_inventory.tsv
  document_inventory_metrics.json
  manifest.json
  checksums.sha256
  metadata.txt
  verification.txt

The last stdout line is always the final backup directory path on success.
EOF
}

NO_PRUNE=false
while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-prune)
      NO_PRUNE=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      dentia_fail "Unknown argument: $1"
      ;;
  esac
done

ROOT="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"
BACKUP_DIR="${DENTIA_BACKUP_DIR:-/opt/backups/dentia}"
RETENTION="${DENTIA_BACKUP_RETENTION:-30}"
TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
BACKUP_NAME="dentia_${TIMESTAMP}"
FINAL_PATH="$BACKUP_DIR/$BACKUP_NAME"
TMP_PARENT="$BACKUP_DIR/.tmp"
TMP_PATH="$TMP_PARENT/$BACKUP_NAME.$$"
DATABASE_DUMP="$TMP_PATH/database.dump"
STORAGE_ARCHIVE="$TMP_PATH/storage.tar.gz"
MANIFEST="$TMP_PATH/manifest.json"
METADATA="$TMP_PATH/metadata.txt"
CHECKSUMS="$TMP_PATH/checksums.sha256"
VERIFICATION="$TMP_PATH/verification.txt"
DOCUMENT_INVENTORY="$TMP_PATH/document_inventory.tsv"
DOCUMENT_INVENTORY_METRICS="$TMP_PATH/document_inventory_metrics.json"

cleanup() {
  if [ -d "$TMP_PATH" ]; then
    rm -rf "$TMP_PATH"
  fi
}
trap cleanup EXIT

umask 077

[ -d "$ROOT" ] || dentia_fail "Production directory not found: $ROOT"
mkdir -p "$BACKUP_DIR" "$TMP_PARENT"
chmod 700 "$BACKUP_DIR" "$TMP_PARENT" 2>/dev/null || true

cd "$ROOT"
dentia_require_cmd docker
dentia_require_cmd git
dentia_require_cmd tar
dentia_require_cmd gzip
dentia_require_cmd python3

docker inspect "$DENTIA_DB_CONTAINER" >/dev/null 2>&1 || dentia_fail "Database container not found: $DENTIA_DB_CONTAINER"
docker inspect "$DENTIA_BACKEND_CONTAINER" >/dev/null 2>&1 || dentia_fail "Backend container not found: $DENTIA_BACKEND_CONTAINER"

HOST_STORAGE_ROOT="$(dentia_storage_host_root "$ROOT")"
dentia_assert_storage_path_safe "$HOST_STORAGE_ROOT"
[ -d "$HOST_STORAGE_ROOT" ] || dentia_fail "Persistent storage directory not found: $HOST_STORAGE_ROOT"
[ -w "$HOST_STORAGE_ROOT" ] || dentia_fail "Persistent storage directory is not writable: $HOST_STORAGE_ROOT"

dentia_info "Preparing complete backup package: $FINAL_PATH"
mkdir -p "$TMP_PATH"

ROOT_SIZE="$(dentia_dir_size_bytes "$ROOT/backend/storage")"
LEGACY_STORAGE_SIZE="$(dentia_dir_size_bytes "$ROOT/storage")"
ESTIMATED_REQUIRED=$((ROOT_SIZE + LEGACY_STORAGE_SIZE + 256 * 1024 * 1024))
AVAILABLE="$(dentia_available_bytes "$BACKUP_DIR")"
if [ "$AVAILABLE" -gt 0 ] && [ "$AVAILABLE" -lt "$ESTIMATED_REQUIRED" ]; then
  dentia_fail "Insufficient disk space. available=${AVAILABLE} required_estimate=${ESTIMATED_REQUIRED}"
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
COMMIT="$(git rev-parse --short HEAD)"
SERVER="$(hostname 2>/dev/null || echo unknown)"
LOCAL_DATE="$(date '+%Y-%m-%dT%H:%M:%S%z')"
UTC_DATE="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

ALEMBIC_REVISION="$(
  docker exec "$DENTIA_BACKEND_CONTAINER" alembic -c alembic.ini current 2>/dev/null |
    awk 'NF {print $1; exit}' || true
)"
[ -n "$ALEMBIC_REVISION" ] || dentia_fail "Could not read Alembic revision from backend container."
POSTGRES_VERSION="$(
  docker exec "$DENTIA_DB_CONTAINER" psql -U "$DENTIA_DB_USER" -d "$DENTIA_DB_NAME" -tAc 'SHOW server_version;' 2>/dev/null |
    tr -d '[:space:]' || true
)"
[ -n "$POSTGRES_VERSION" ] || dentia_fail "Could not read PostgreSQL version from database container."

dentia_info "Dumping PostgreSQL database with pg_dump -Fc..."
docker exec "$DENTIA_DB_CONTAINER" pg_dump -Fc --no-owner --no-privileges -U "$DENTIA_DB_USER" "$DENTIA_DB_NAME" >"$DATABASE_DUMP"
[ -s "$DATABASE_DUMP" ] || dentia_fail "PostgreSQL dump is empty."

dentia_info "Validating PostgreSQL dump catalogue..."
docker exec -i "$DENTIA_DB_CONTAINER" pg_restore -l <"$DATABASE_DUMP" >/dev/null

dentia_info "Building semantic document inventory..."
"$SCRIPT_DIR/dentia_document_inventory.py" collect \
  --db-container "$DENTIA_DB_CONTAINER" \
  --db-user "$DENTIA_DB_USER" \
  --db-name "$DENTIA_DB_NAME" \
  --storage-root "$HOST_STORAGE_ROOT" \
  --output "$DOCUMENT_INVENTORY" \
  --metrics-output "$DOCUMENT_INVENTORY_METRICS" >/dev/null

STORAGE_PATHS=()
for relative in $DENTIA_STORAGE_PATHS; do
  if [ -d "$ROOT/$relative" ]; then
    STORAGE_PATHS+=("$relative")
  fi
done

STORAGE_FILE_COUNT=0
STORAGE_SIZE_BYTES=0
for relative in "${STORAGE_PATHS[@]}"; do
  count="$(find "$ROOT/$relative" -type f | wc -l | awk '{print $1}')"
  size="$(dentia_dir_size_bytes "$ROOT/$relative")"
  STORAGE_FILE_COUNT=$((STORAGE_FILE_COUNT + count))
  STORAGE_SIZE_BYTES=$((STORAGE_SIZE_BYTES + size))
done
STORAGE_PATHS_JSON="$(python3 -c 'import json, sys; print(json.dumps(sys.argv[1:], ensure_ascii=False))' "${STORAGE_PATHS[@]}")"

dentia_info "Creating storage archive. files=$STORAGE_FILE_COUNT size_bytes=$STORAGE_SIZE_BYTES"
if [ "${#STORAGE_PATHS[@]}" -eq 0 ]; then
  mkdir -p "$TMP_PATH/empty-storage"
  tar -czf "$STORAGE_ARCHIVE" -C "$TMP_PATH" empty-storage
else
  tar -czf "$STORAGE_ARCHIVE" -C "$ROOT" "${STORAGE_PATHS[@]}"
fi
[ -s "$STORAGE_ARCHIVE" ] || dentia_fail "Storage archive is empty or invalid."

dentia_info "Validating storage archive..."
tar -tzf "$STORAGE_ARCHIVE" >/dev/null

dentia_info "Validating semantic inventory against storage archive..."
"$SCRIPT_DIR/dentia_document_inventory.py" verify-archive \
  --inventory "$DOCUMENT_INVENTORY" \
  --archive "$STORAGE_ARCHIVE" \
  --metrics-output "$DOCUMENT_INVENTORY_METRICS.archive" >/dev/null

DATABASE_SIZE="$(dentia_file_size "$DATABASE_DUMP")"
STORAGE_ARCHIVE_SIZE="$(dentia_file_size "$STORAGE_ARCHIVE")"
DATABASE_SHA="$(dentia_sha256 "$DATABASE_DUMP" | awk '{print $1}')"
STORAGE_SHA="$(dentia_sha256 "$STORAGE_ARCHIVE" | awk '{print $1}')"
DOCUMENT_INVENTORY_SIZE="$(dentia_file_size "$DOCUMENT_INVENTORY")"
DOCUMENT_INVENTORY_SHA="$(dentia_sha256 "$DOCUMENT_INVENTORY" | awk '{print $1}')"
DOCUMENT_INVENTORY_METRICS_JSON="$(python3 -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1])), sort_keys=True))' "$DOCUMENT_INVENTORY_METRICS")"

cat >"$METADATA" <<EOF
Dentia complete backup
utc_date=$UTC_DATE
local_date=$LOCAL_DATE
server=$SERVER
environment=production
branch=$BRANCH
commit=$COMMIT
alembic_revision=${ALEMBIC_REVISION:-unknown}
postgres_version=${POSTGRES_VERSION:-unknown}
database_dump=database.dump
storage_archive=storage.tar.gz
storage_file_count=$STORAGE_FILE_COUNT
storage_size_bytes=$STORAGE_SIZE_BYTES
database_size_bytes=$DATABASE_SIZE
storage_archive_size_bytes=$STORAGE_ARCHIVE_SIZE
document_inventory=document_inventory.tsv
document_inventory_size_bytes=$DOCUMENT_INVENTORY_SIZE
document_inventory_sha256=$DOCUMENT_INVENTORY_SHA
EOF

python3 - "$MANIFEST" <<PY
import json
import sys

manifest_path = sys.argv[1]
data = {
    "format": "dentia_complete_backup_v1",
    "created_at_utc": "$UTC_DATE",
    "created_at_local": "$LOCAL_DATE",
    "server": "$SERVER",
    "environment": "production",
    "branch": "$BRANCH",
    "commit": "$COMMIT",
    "alembic_revision": "${ALEMBIC_REVISION:-unknown}",
    "postgres_version": "${POSTGRES_VERSION:-unknown}",
    "database": {
        "file": "database.dump",
        "format": "pg_dump_custom",
        "size_bytes": int("$DATABASE_SIZE"),
        "sha256": "$DATABASE_SHA",
        "container": "$DENTIA_DB_CONTAINER",
        "database": "$DENTIA_DB_NAME",
        "user": "$DENTIA_DB_USER",
    },
    "storage": {
        "file": "storage.tar.gz",
        "paths": $STORAGE_PATHS_JSON,
        "file_count": int("$STORAGE_FILE_COUNT"),
        "source_size_bytes": int("$STORAGE_SIZE_BYTES"),
        "archive_size_bytes": int("$STORAGE_ARCHIVE_SIZE"),
        "sha256": "$STORAGE_SHA",
    },
    "document_inventory": {
        "file": "document_inventory.tsv",
        "metrics_file": "document_inventory_metrics.json",
        "size_bytes": int("$DOCUMENT_INVENTORY_SIZE"),
        "sha256": "$DOCUMENT_INVENTORY_SHA",
        "metrics": $DOCUMENT_INVENTORY_METRICS_JSON,
    },
    "verification": {
        "dump_catalogue_read": True,
        "storage_archive_read": True,
        "semantic_inventory_valid": True,
        "result": "BACKUP_VALID",
    },
}
data["storage"]["paths"] = data["storage"]["paths"] or []
with open(manifest_path, "w", encoding="utf-8") as fh:
    json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
    fh.write("\\n")
PY

(
  cd "$TMP_PATH"
  cp document_inventory_metrics.json.archive document_inventory_archive_metrics.json
  dentia_sha256 database.dump storage.tar.gz document_inventory.tsv document_inventory_metrics.json document_inventory_archive_metrics.json manifest.json metadata.txt >checksums.sha256
)

(
  cd "$TMP_PATH"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum -c checksums.sha256 >/dev/null
  else
    shasum -a 256 -c checksums.sha256 >/dev/null
  fi
)

{
  printf 'BACKUP_VALID\n'
  printf 'verified_at_utc=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  printf 'semantic_inventory=document_inventory.tsv\n'
  python3 - "$DOCUMENT_INVENTORY_METRICS" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
for key in sorted(data):
    print(f"semantic_{key}={data[key]}")
PY
} >"$VERIFICATION"

dentia_info "Publishing backup atomically..."
if [ -e "$FINAL_PATH" ]; then
  dentia_fail "Final backup path already exists: $FINAL_PATH"
fi
mv "$TMP_PATH" "$FINAL_PATH"
chmod 700 "$FINAL_PATH" 2>/dev/null || true
find "$FINAL_PATH" -type f -exec chmod 600 {} \; 2>/dev/null || true
trap - EXIT

if ! $NO_PRUNE; then
  LAST_DEPLOY_BACKUP=""
  if [ -f "$ROOT/.run/last_deploy_backup" ]; then
    LAST_DEPLOY_BACKUP="$(cat "$ROOT/.run/last_deploy_backup")"
  fi
  find "$BACKUP_DIR" -maxdepth 1 -type d -name 'dentia_*' -print |
    sort -r |
    awk "NR>$RETENTION" |
    while IFS= read -r old_backup; do
      [ "$old_backup" = "$FINAL_PATH" ] && continue
      [ -n "$LAST_DEPLOY_BACKUP" ] && [ "$old_backup" = "$LAST_DEPLOY_BACKUP" ] && continue
      [ -f "$old_backup/verification.txt" ] || continue
      dentia_info "Pruning old verified backup: $old_backup"
      rm -rf "$old_backup"
    done
fi

dentia_info "Complete backup OK: $FINAL_PATH"
printf '%s\n' "$FINAL_PATH"
