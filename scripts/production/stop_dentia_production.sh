#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

ROOT="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"
cd "$ROOT"

printf 'This will stop Dentia containers only. It will NOT delete volumes. Type STOP-DENTIA to continue: '
read -r confirmation
[ "$confirmation" = "STOP-DENTIA" ] || dentia_fail "Cancelled."

docker stop "$DENTIA_FRONTEND_CONTAINER" "$DENTIA_BACKEND_CONTAINER" "$DENTIA_DB_CONTAINER" >/dev/null
dentia_info "Dentia containers stopped. Volumes were not removed."
