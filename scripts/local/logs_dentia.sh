#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# shellcheck source=../lib/dentia_common.sh
source "$SCRIPT_DIR/../lib/dentia_common.sh"

usage() {
  cat <<'EOF'
Usage: logs_dentia.sh [backend|frontend|all] [--help]

Follows local Dentia logs under .run/logs/.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

TARGET="${1:-all}"
LOG_DIR="$DENTIA_PROJECT_DIR/.run/logs"

case "$TARGET" in
  backend)
    [ -f "$LOG_DIR/backend.log" ] || dentia_fail "Backend log not found. Start Dentia first: $LOG_DIR/backend.log"
    tail -f "$LOG_DIR/backend.log"
    ;;
  frontend)
    [ -f "$LOG_DIR/frontend.log" ] || dentia_fail "Frontend log not found. Start Dentia first: $LOG_DIR/frontend.log"
    tail -f "$LOG_DIR/frontend.log"
    ;;
  all)
    [ -f "$LOG_DIR/backend.log" ] || dentia_fail "Backend log not found. Start Dentia first: $LOG_DIR/backend.log"
    [ -f "$LOG_DIR/frontend.log" ] || dentia_fail "Frontend log not found. Start Dentia first: $LOG_DIR/frontend.log"
    tail -f "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log"
    ;;
  *)
    usage
    dentia_fail "Unknown target: $TARGET"
    ;;
esac
