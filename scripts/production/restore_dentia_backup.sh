#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

usage() {
  cat <<'EOF'
Usage: restore_dentia_backup.sh --backup /path/to/backup [--temporary|--production] [--database-name name] [--storage-dir dir] [--yes-i-understand]

Default mode is --temporary. It restores the dump into a temporary database,
extracts storage into a temporary directory and validates DB document rows
against restored files and SHA-256 hashes.
EOF
}

BACKUP_PATH=""
MODE="temporary"
DATABASE_NAME=""
STORAGE_DIR=""
YES=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --backup)
      BACKUP_PATH="${2:-}"
      shift 2
      ;;
    --temporary)
      MODE="temporary"
      shift
      ;;
    --production)
      MODE="production"
      shift
      ;;
    --database-name)
      DATABASE_NAME="${2:-}"
      shift 2
      ;;
    --storage-dir)
      STORAGE_DIR="${2:-}"
      shift 2
      ;;
    --yes-i-understand)
      YES=true
      shift
      ;;
    *)
      if [ -z "$BACKUP_PATH" ]; then
        BACKUP_PATH="$1"
        shift
      else
        dentia_fail "Unknown argument: $1"
      fi
      ;;
  esac
done

[ -n "$BACKUP_PATH" ] || dentia_fail "Usage: $0 --backup /path/to/backup [--temporary|--production] [--database-name name] [--storage-dir dir]"
[ -d "$BACKUP_PATH" ] || dentia_fail "Backup directory not found: $BACKUP_PATH"

dentia_require_cmd docker
dentia_require_cmd tar
dentia_require_cmd python3
dentia_require_cmd mktemp

"$SCRIPT_DIR/verify_dentia_backup.sh" "$BACKUP_PATH" >/dev/null

ROOT="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"
TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"

if [ "$MODE" = "temporary" ]; then
  DATABASE_NAME="${DATABASE_NAME:-dentia_restore_${TIMESTAMP}}"
  STORAGE_DIR="${STORAGE_DIR:-/tmp/dentia_restore_${TIMESTAMP}/storage}"
else
  [ "$YES" = true ] || dentia_fail "Production restore requires --yes-i-understand."
  DATABASE_NAME="${DATABASE_NAME:-$DENTIA_DB_NAME}"
  STORAGE_DIR="${STORAGE_DIR:-$ROOT/backend/storage}"
  cat <<EOF
PRODUCTION DATA RESTORE REQUESTED

Database: $DATABASE_NAME
Storage:  $STORAGE_DIR

This may overwrite production data. Type RESTORE-DENTIA-DATA to continue:
EOF
  read -r confirmation
  [ "$confirmation" = "RESTORE-DENTIA-DATA" ] || dentia_fail "Cancelled."
fi

dentia_assert_safe_restore_path "$STORAGE_DIR"

docker inspect "$DENTIA_DB_CONTAINER" >/dev/null 2>&1 || dentia_fail "Database container not found: $DENTIA_DB_CONTAINER"

dentia_info "Restoring database into: $DATABASE_NAME"
if [ "$MODE" = "temporary" ]; then
  docker exec "$DENTIA_DB_CONTAINER" dropdb -U "$DENTIA_DB_USER" --if-exists "$DATABASE_NAME"
  docker exec "$DENTIA_DB_CONTAINER" createdb -U "$DENTIA_DB_USER" "$DATABASE_NAME"
else
  docker exec "$DENTIA_DB_CONTAINER" dropdb -U "$DENTIA_DB_USER" --if-exists "$DATABASE_NAME"
  docker exec "$DENTIA_DB_CONTAINER" createdb -U "$DENTIA_DB_USER" "$DATABASE_NAME"
fi
docker exec -i "$DENTIA_DB_CONTAINER" pg_restore --no-owner --no-privileges -U "$DENTIA_DB_USER" -d "$DATABASE_NAME" <"$BACKUP_PATH/database.dump"

dentia_info "Restoring storage into: $STORAGE_DIR"
mkdir -p "$STORAGE_DIR"
EXTRACT_DIR="$(mktemp -d "/tmp/dentia_restore_extract_${TIMESTAMP}.XXXXXX")"
cleanup_extract() {
  rm -rf "$EXTRACT_DIR"
}
trap cleanup_extract EXIT
python3 - "$BACKUP_PATH/storage.tar.gz" "$EXTRACT_DIR" <<'PY'
import sys
from pathlib import Path, PurePosixPath
import tarfile

archive = Path(sys.argv[1])
destination = Path(sys.argv[2]).resolve()
with tarfile.open(archive, "r:gz") as tar:
    members = tar.getmembers()
    names = set()
    for member in members:
        name = member.name
        if name in names:
            raise SystemExit(f"duplicate path in storage archive: {name}")
        names.add(name)
        path = PurePosixPath(name)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise SystemExit(f"unsafe path in storage archive: {name}")
        target = (destination / Path(*path.parts)).resolve()
        try:
            target.relative_to(destination)
        except ValueError:
            raise SystemExit(f"archive member escapes destination: {name}")
        if member.issym() or member.islnk():
            raise SystemExit(f"links are not allowed in storage archive: {name}")
    tar.extractall(destination, members=members)
PY

if [ -d "$EXTRACT_DIR/backend/storage" ]; then
  if [ "$MODE" = "production" ] && [ -n "$(find "$STORAGE_DIR" -mindepth 1 -type f -print -quit 2>/dev/null)" ]; then
    dentia_warn "Production storage is not empty; files will be merged without overwrites."
  fi
  cp -Rn "$EXTRACT_DIR/backend/storage/." "$STORAGE_DIR/"
fi
if [ -d "$EXTRACT_DIR/storage" ]; then
  mkdir -p "$STORAGE_DIR/legacy-storage"
  cp -Rn "$EXTRACT_DIR/storage/." "$STORAGE_DIR/legacy-storage/"
fi

RESTORED_FILE_COUNT="$(find "$STORAGE_DIR" -type f 2>/dev/null | wc -l | awk '{print $1}')"

dentia_info "Validating restored database has Alembic version table..."
docker exec "$DENTIA_DB_CONTAINER" psql -U "$DENTIA_DB_USER" -d "$DATABASE_NAME" -tAc "SELECT version_num FROM alembic_version LIMIT 1;" >/dev/null

dentia_info "Validating restored semantic DB -> file -> SHA-256 integrity..."
RESTORE_INVENTORY="$EXTRACT_DIR/restored_document_inventory.tsv"
RESTORE_METRICS="$EXTRACT_DIR/restored_document_inventory_metrics.json"
"$SCRIPT_DIR/dentia_document_inventory.py" collect \
  --db-container "$DENTIA_DB_CONTAINER" \
  --db-user "$DENTIA_DB_USER" \
  --db-name "$DATABASE_NAME" \
  --storage-root "$STORAGE_DIR" \
  --output "$RESTORE_INVENTORY" \
  --metrics-output "$RESTORE_METRICS" >/dev/null

dentia_info "Restore completed."
printf 'RESTORE_VALID\n'
printf 'database=%s\n' "$DATABASE_NAME"
printf 'storage_dir=%s\n' "$STORAGE_DIR"
printf 'restored_file_count=%s\n' "$RESTORED_FILE_COUNT"

if [ "$MODE" = "temporary" ]; then
  dentia_warn "Temporary database was left in place for inspection: $DATABASE_NAME"
  dentia_warn "Temporary storage was left in place for inspection: $STORAGE_DIR"
fi
