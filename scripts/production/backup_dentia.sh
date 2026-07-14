#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

ROOT="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"
BACKUP_DIR="${DENTIA_BACKUP_DIR:-/opt/backups/dentia}"
RETENTION="${DENTIA_BACKUP_RETENTION:-30}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_PATH="$BACKUP_DIR/dentia_${TIMESTAMP}.sql.gz"

[ -d "$ROOT" ] || dentia_fail "Production directory not found: $ROOT"
mkdir -p "$BACKUP_DIR"

cd "$ROOT"
dentia_require_cmd docker
dentia_info "Creating PostgreSQL backup: $BACKUP_PATH"

if ! docker exec "$DENTIA_DB_CONTAINER" pg_dump -U "$DENTIA_DB_USER" "$DENTIA_DB_NAME" | gzip -c >"$BACKUP_PATH"; then
  rm -f "$BACKUP_PATH"
  dentia_fail "Backup failed. No old backups were deleted."
fi

if [ ! -s "$BACKUP_PATH" ]; then
  rm -f "$BACKUP_PATH"
  dentia_fail "Backup file is empty. No old backups were deleted."
fi

find "$BACKUP_DIR" -maxdepth 1 -type f -name 'dentia_*.sql.gz' -print |
  sort -r |
  awk "NR>$RETENTION" |
  while IFS= read -r old_backup; do
    [ -n "$old_backup" ] && rm -f "$old_backup"
  done

dentia_info "Backup OK: $BACKUP_PATH"
printf '%s\n' "$BACKUP_PATH"
