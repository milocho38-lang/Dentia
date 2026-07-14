#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

TARGET="${1:-all}"
LOG_DIR="$DENTIA_PROJECT_DIR/.run/logs"

case "$TARGET" in
  backend)
    tail -f "$LOG_DIR/backend.log"
    ;;
  frontend)
    tail -f "$LOG_DIR/frontend.log"
    ;;
  all)
    tail -f "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log"
    ;;
  *)
    dentia_fail "Usage: $0 backend|frontend|all"
    ;;
esac
