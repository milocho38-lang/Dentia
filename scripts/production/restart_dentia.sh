#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

ROOT="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"
cd "$ROOT"

dentia_info "Restarting Dentia containers only..."
docker restart "$DENTIA_DB_CONTAINER" "$DENTIA_BACKEND_CONTAINER" "$DENTIA_FRONTEND_CONTAINER" >/dev/null
sleep 5
dentia_compose ps

if ! dentia_wait_http "$DENTIA_PRODUCTION_BACKEND_HEALTH_URL" 20 2; then
  docker logs --tail 120 "$DENTIA_BACKEND_CONTAINER" || true
  dentia_fail "Backend did not become healthy after restart."
fi
if ! dentia_wait_http "$DENTIA_PRODUCTION_FRONTEND_URL" 20 2; then
  docker logs --tail 120 "$DENTIA_FRONTEND_CONTAINER" || true
  dentia_fail "Frontend did not become reachable after restart."
fi
dentia_info "Restart OK."
