#!/usr/bin/env bash
set -Eeuo pipefail

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." >/dev/null 2>&1 && pwd)"
HARNESS="$(mktemp -d "${TMPDIR:-/tmp}/dentia-verify-pg-restore.XXXXXX")"
trap 'rm -rf "$HARNESS"' EXIT INT TERM

mkdir -p "$HARNESS/scripts/production" "$HARNESS/scripts/lib" "$HARNESS/bin" "$HARNESS/backup/storage"
cp "$SOURCE_ROOT/scripts/production/verify_dentia_backup.sh" "$HARNESS/scripts/production/verify_dentia_backup.sh"

cat >"$HARNESS/scripts/lib/dentia_common.sh" <<'EOF'
dentia_info() { :; }
dentia_fail() { printf '%s\n' "$*" >&2; exit 1; }
dentia_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1"
  else
    shasum -a 256 "$1"
  fi
}
EOF

cat >"$HARNESS/scripts/production/dentia_document_inventory.py" <<'EOF'
#!/usr/bin/env sh
exit 0
EOF
chmod +x "$HARNESS/scripts/production/dentia_document_inventory.py"

cat >"$HARNESS/bin/docker" <<'EOF'
#!/usr/bin/env bash
printf 'docker %s\n' "$*" >>"$MOCK_LOG"
if [ "${1:-}" = inspect ]; then
  exit "${MOCK_DOCKER_INSPECT_STATUS:-0}"
fi
if [ "${1:-}" = exec ]; then
  exit "${MOCK_DOCKER_EXEC_STATUS:-0}"
fi
exit 2
EOF

cat >"$HARNESS/bin/pg_restore" <<'EOF'
#!/usr/bin/env bash
printf 'host pg_restore %s\n' "$*" >>"$MOCK_LOG"
exit "${MOCK_HOST_STATUS:-0}"
EOF
chmod +x "$HARNESS/bin/docker" "$HARNESS/bin/pg_restore"

printf 'synthetic dump\n' >"$HARNESS/backup/database.dump"
printf 'kind\tid\tpath\tsha256\n' >"$HARNESS/backup/document_inventory.tsv"
printf '{}\n' >"$HARNESS/backup/document_inventory_metrics.json"
printf 'synthetic metadata\n' >"$HARNESS/backup/metadata.txt"
printf 'synthetic storage\n' >"$HARNESS/backup/storage/file.txt"
tar -czf "$HARNESS/backup/storage.tar.gz" -C "$HARNESS/backup/storage" .

sha() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

cat >"$HARNESS/backup/manifest.json" <<EOF
{
  "format": "dentia_complete_backup_v1",
  "created_at_utc": "2026-10-18T00:00:00Z",
  "commit": "synthetic-commit",
  "alembic_revision": "synthetic-revision",
  "database": {"file": "database.dump", "sha256": "$(sha "$HARNESS/backup/database.dump")"},
  "storage": {"file": "storage.tar.gz", "sha256": "$(sha "$HARNESS/backup/storage.tar.gz")"},
  "document_inventory": {"file": "document_inventory.tsv", "sha256": "$(sha "$HARNESS/backup/document_inventory.tsv")"},
  "verification": {}
}
EOF

(
  cd "$HARNESS/backup"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum database.dump storage.tar.gz document_inventory.tsv document_inventory_metrics.json manifest.json metadata.txt >checksums.sha256
  else
    shasum -a 256 database.dump storage.tar.gz document_inventory.tsv document_inventory_metrics.json manifest.json metadata.txt >checksums.sha256
  fi
)

run_verify() {
  MOCK_LOG="$1" MOCK_DOCKER_INSPECT_STATUS="$2" MOCK_DOCKER_EXEC_STATUS="$3" MOCK_HOST_STATUS="$4" \
    DENTIA_DB_CONTAINER=dentia-test-db PATH="$HARNESS/bin:$PATH" \
    "$HARNESS/scripts/production/verify_dentia_backup.sh" "$HARNESS/backup"
}

: >"$HARNESS/both.log"
run_verify "$HARNESS/both.log" 0 0 0 | grep -qx BACKUP_VALID
grep -q '^docker inspect dentia-test-db$' "$HARNESS/both.log"
grep -q '^docker exec -i dentia-test-db pg_restore -l$' "$HARNESS/both.log"
! grep -q '^host pg_restore ' "$HARNESS/both.log"
printf 'container_preferred OK\n'

: >"$HARNESS/host.log"
run_verify "$HARNESS/host.log" 1 0 0 | grep -qx BACKUP_VALID
grep -q '^docker inspect dentia-test-db$' "$HARNESS/host.log"
grep -q '^host pg_restore -l database.dump$' "$HARNESS/host.log"
printf 'host_fallback OK\n'

: >"$HARNESS/container-failure.log"
if run_verify "$HARNESS/container-failure.log" 0 17 0 >/dev/null 2>&1; then
  printf 'container pg_restore failure was incorrectly accepted\n' >&2
  exit 1
fi
grep -q '^docker exec -i dentia-test-db pg_restore -l$' "$HARNESS/container-failure.log"
! grep -q '^host pg_restore ' "$HARNESS/container-failure.log"
printf 'container_failure_is_fatal OK\n'
