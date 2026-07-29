#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

BACKUP_PATH="${1:-}"
[ -n "$BACKUP_PATH" ] || dentia_fail "Usage: $0 /path/to/dentia_YYYYMMDD_HHMMSS"
[ -d "$BACKUP_PATH" ] || dentia_fail "Backup directory not found: $BACKUP_PATH"

cd "$BACKUP_PATH"

for required in database.dump storage.tar.gz manifest.json checksums.sha256 metadata.txt; do
  [ -f "$required" ] || dentia_fail "Backup verification failed: missing $required"
done

[ -s database.dump ] || dentia_fail "Backup verification failed: database.dump is empty"
[ -s storage.tar.gz ] || dentia_fail "Backup verification failed: storage.tar.gz is empty"
[ -s manifest.json ] || dentia_fail "Backup verification failed: manifest.json is empty"
[ -s checksums.sha256 ] || dentia_fail "Backup verification failed: checksums.sha256 is empty"

dentia_info "Verifying checksums..."
if command -v sha256sum >/dev/null 2>&1; then
  sha256sum -c checksums.sha256 >/dev/null
else
  shasum -a 256 -c checksums.sha256 >/dev/null
fi

dentia_info "Validating manifest JSON..."
python3 - "$BACKUP_PATH/manifest.json" <<'PY'
import json
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
data = json.loads(manifest.read_text(encoding="utf-8"))
required = ["format", "created_at_utc", "commit", "alembic_revision", "database", "storage", "verification"]
missing = [key for key in required if key not in data]
if missing:
    raise SystemExit(f"missing manifest keys: {', '.join(missing)}")
if data["format"] != "dentia_complete_backup_v1":
    raise SystemExit(f"unexpected backup format: {data['format']}")
if data["database"].get("file") != "database.dump":
    raise SystemExit("database.file must be database.dump")
if data["storage"].get("file") != "storage.tar.gz":
    raise SystemExit("storage.file must be storage.tar.gz")
PY

dentia_info "Validating PostgreSQL dump catalogue..."
if command -v pg_restore >/dev/null 2>&1; then
  pg_restore -l database.dump >/dev/null
elif command -v docker >/dev/null 2>&1 && docker inspect "$DENTIA_DB_CONTAINER" >/dev/null 2>&1; then
  docker exec -i "$DENTIA_DB_CONTAINER" pg_restore -l <database.dump >/dev/null
else
  dentia_fail "Backup verification failed: pg_restore unavailable and DB container is not available."
fi

dentia_info "Validating storage archive..."
tar -tzf storage.tar.gz >/dev/null

DATABASE_SHA="$(dentia_sha256 database.dump | awk '{print $1}')"
STORAGE_SHA="$(dentia_sha256 storage.tar.gz | awk '{print $1}')"

python3 - "$BACKUP_PATH/manifest.json" "$DATABASE_SHA" "$STORAGE_SHA" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
database_sha = sys.argv[2]
storage_sha = sys.argv[3]
if data["database"].get("sha256") != database_sha:
    raise SystemExit("database sha256 does not match manifest")
if data["storage"].get("sha256") != storage_sha:
    raise SystemExit("storage sha256 does not match manifest")
if not data.get("alembic_revision") or data["alembic_revision"] == "unknown":
    raise SystemExit("alembic revision is missing or unknown")
if not data.get("commit") or data["commit"] == "unknown":
    raise SystemExit("commit is missing or unknown")
PY

printf 'BACKUP_VALID\n'
