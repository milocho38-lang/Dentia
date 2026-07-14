#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

ROOT="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"
cd "$ROOT"

dentia_info "Starting existing Dentia services..."
dentia_compose up -d
sleep 5
dentia_compose ps

docker exec "$DENTIA_DB_CONTAINER" pg_isready -U "$DENTIA_DB_USER" >/dev/null || dentia_fail "Database is not ready."
dentia_wait_http "$DENTIA_PRODUCTION_BACKEND_HEALTH_URL" 20 2 || dentia_fail "Backend healthcheck failed."
dentia_wait_http "$DENTIA_PRODUCTION_FRONTEND_URL" 20 2 || dentia_fail "Frontend check failed."
dentia_info "Production start OK."
