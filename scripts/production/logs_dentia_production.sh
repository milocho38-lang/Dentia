#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

ROOT="${DENTIA_PRODUCTION_DIR:-/opt/apps/dentia}"
TARGET="${1:-all}"
cd "$ROOT"

case "$TARGET" in
  backend)
    docker logs -f --tail 200 "$DENTIA_BACKEND_CONTAINER"
    ;;
  frontend)
    docker logs -f --tail 200 "$DENTIA_FRONTEND_CONTAINER"
    ;;
  db)
    docker logs -f --tail 200 "$DENTIA_DB_CONTAINER"
    ;;
  all)
    dentia_compose logs -f --tail 200
    ;;
  *)
    dentia_fail "Usage: $0 backend|frontend|db|all"
    ;;
esac
