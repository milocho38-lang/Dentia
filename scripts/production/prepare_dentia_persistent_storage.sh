#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

usage() {
  cat <<'EOF'
Usage: prepare_dentia_persistent_storage.sh [--dry-run|--apply] [--help]

Safely prepares host-backed persistent storage before the first backend
container recreate.

Default: --dry-run

It:
  - detects dentia-backend;
  - checks whether /app/storage is already mounted;
  - copies container /app/storage into a temporary staging directory;
  - compares host and container files by path, size and SHA-256;
  - with --apply, copies only missing files to backend/storage;
  - aborts on same-path hash conflicts;
  - never deletes files and never restarts containers.
EOF
}

MODE="dry-run"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run)
      MODE="dry-run"
      shift
      ;;
    --apply)
      MODE="apply"
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
HOST_STORAGE_ROOT="$(dentia_storage_host_root "$ROOT")"
CONTAINER_STORAGE_ROOT="${DENTIA_BACKEND_STORAGE_CONTAINER_PATH:-/app/storage}"
TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
STAGING_PARENT="${TMPDIR:-/tmp}/dentia_storage_prepare_${TIMESTAMP}.$$"
CONTAINER_COPY="$STAGING_PARENT/container-storage"
HOST_INVENTORY="$STAGING_PARENT/host_inventory.tsv"
CONTAINER_INVENTORY="$STAGING_PARENT/container_inventory.tsv"
PLAN_JSON="$STAGING_PARENT/plan.json"
AUDIT_DIR="$ROOT/.run/storage_prepare_${TIMESTAMP}"

cleanup() {
  if [ -d "$STAGING_PARENT" ]; then
    rm -rf "$STAGING_PARENT"
  fi
}
trap cleanup EXIT

dentia_require_cmd docker
dentia_require_cmd python3
dentia_require_cmd find

docker inspect "$DENTIA_BACKEND_CONTAINER" >/dev/null 2>&1 || dentia_fail "Backend container not found: $DENTIA_BACKEND_CONTAINER"

dentia_info "Backend container: $DENTIA_BACKEND_CONTAINER"
dentia_info "Container storage: $CONTAINER_STORAGE_ROOT"
dentia_info "Host storage: $HOST_STORAGE_ROOT"
dentia_info "Mode: $MODE"

mkdir -p "$STAGING_PARENT"
mkdir -p "$AUDIT_DIR"
chmod 700 "$AUDIT_DIR" 2>/dev/null || true
mkdir -p "$HOST_STORAGE_ROOT"
dentia_assert_storage_path_safe "$HOST_STORAGE_ROOT"
[ -d "$HOST_STORAGE_ROOT" ] || dentia_fail "Host storage directory not found: $HOST_STORAGE_ROOT"
[ -w "$HOST_STORAGE_ROOT" ] || dentia_fail "Host storage directory is not writable: $HOST_STORAGE_ROOT"
chmod 750 "$HOST_STORAGE_ROOT" 2>/dev/null || true

MOUNTS_JSON="$(docker inspect "$DENTIA_BACKEND_CONTAINER" --format '{{json .Mounts}}')"
python3 - "$CONTAINER_STORAGE_ROOT" "$MOUNTS_JSON" <<'PY'
import json, sys
target = sys.argv[1]
mounts = json.loads(sys.argv[2])
matches = [m for m in mounts if m.get("Destination") == target]
if matches:
    print(f"storage_mount_detected=true source={matches[0].get('Source', '')}")
else:
    print("storage_mount_detected=false")
PY

if ! docker exec "$DENTIA_BACKEND_CONTAINER" test -d "$CONTAINER_STORAGE_ROOT"; then
  dentia_fail "Container storage directory does not exist: $CONTAINER_STORAGE_ROOT"
fi

dentia_info "Copying container storage into staging for comparison..."
docker cp "$DENTIA_BACKEND_CONTAINER:$CONTAINER_STORAGE_ROOT" "$CONTAINER_COPY"

python3 - "$HOST_STORAGE_ROOT" "$CONTAINER_COPY" "$HOST_INVENTORY" "$CONTAINER_INVENTORY" "$PLAN_JSON" <<'PY'
import csv
import hashlib
import json
import sys
from pathlib import Path

host_root = Path(sys.argv[1]).resolve()
container_root = Path(sys.argv[2]).resolve()
host_inventory = Path(sys.argv[3])
container_inventory = Path(sys.argv[4])
plan_path = Path(sys.argv[5])

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def inventory(root: Path):
    rows = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        rows[relative] = {"path": relative, "size": path.stat().st_size, "sha256": digest(path)}
    return rows

def write(path: Path, rows: dict):
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["path", "size", "sha256"], delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows.values():
            writer.writerow(row)

host = inventory(host_root)
container = inventory(container_root)
write(host_inventory, host)
write(container_inventory, container)

missing = []
matching = []
conflicts = []
for relative, row in container.items():
    current = host.get(relative)
    if current is None:
        missing.append(relative)
    elif current["sha256"] == row["sha256"] and current["size"] == row["size"]:
        matching.append(relative)
    else:
        conflicts.append({
            "path": relative,
            "host_size": current["size"],
            "container_size": row["size"],
            "host_sha256": current["sha256"],
            "container_sha256": row["sha256"],
        })

plan = {
    "host_file_count": len(host),
    "container_file_count": len(container),
    "matching_count": len(matching),
    "missing_count": len(missing),
    "conflict_count": len(conflicts),
    "missing": missing,
    "conflicts": conflicts,
}
plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({k: plan[k] for k in ["host_file_count", "container_file_count", "matching_count", "missing_count", "conflict_count"]}, sort_keys=True))
if conflicts:
    raise SystemExit(2)
PY

dentia_info "Inventories:"
cp "$HOST_INVENTORY" "$AUDIT_DIR/host_inventory_before.tsv"
cp "$CONTAINER_INVENTORY" "$AUDIT_DIR/container_inventory.tsv"
cp "$PLAN_JSON" "$AUDIT_DIR/plan.json"
dentia_info "  audit_dir=$AUDIT_DIR"
dentia_info "  host=$AUDIT_DIR/host_inventory_before.tsv"
dentia_info "  container=$AUDIT_DIR/container_inventory.tsv"
dentia_info "  plan=$AUDIT_DIR/plan.json"

if [ "$MODE" = "apply" ]; then
  dentia_info "Applying copy plan: missing files only."
  python3 - "$CONTAINER_COPY" "$HOST_STORAGE_ROOT" "$PLAN_JSON" <<'PY'
import json
import shutil
import sys
from pathlib import Path

container_root = Path(sys.argv[1]).resolve()
host_root = Path(sys.argv[2]).resolve()
plan = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
if plan["conflict_count"]:
    raise SystemExit("Refusing to apply with hash conflicts.")
for relative in plan["missing"]:
    source = (container_root / relative).resolve()
    target = (host_root / relative).resolve()
    source.relative_to(container_root)
    target.relative_to(host_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise SystemExit(f"Target appeared during copy; refusing overwrite: {target}")
    shutil.copy2(source, target)
print(f"copied_missing_files={len(plan['missing'])}")
PY
  find "$HOST_STORAGE_ROOT" -type f -print | sort >"$AUDIT_DIR/host_inventory_after_paths.txt"
else
  dentia_warn "Dry-run only. Re-run with --apply to copy missing files."
fi

dentia_info "Persistent storage preparation completed."
